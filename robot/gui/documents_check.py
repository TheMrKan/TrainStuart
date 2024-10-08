import threading
import numpy as np
import time
import base64
import cv2
import random
from typing import Callable, Optional, Dict, Any
from datetime import datetime

from robot.hardware.cameras import CameraAccessor
import robot.config as config
from robot.gui.base.app import BaseApp
from robot.gui.base import gui_server, navigation as gui_navigation
import utils.faces as face_util
from robot.core.async_processor import AsyncProcessor
from robot.core.tickets import TicketsRepository, TicketInfo
from utils.docs_reader import PassportData
import robot.core.route as route
from robot.gui import external


class PassportNotFoundError(Exception):
    pass


class TicketNotFoundError(Exception):
    pass


class DocumentsCheckApp(BaseApp):

    NAME = "DocumentsCheck"
    INITIAL_PAGE = "passport"

    success: bool

    def __init__(self):
        super().__init__()
        self.success = False

    def run(self):
        super().run()
        self.logger.debug("Running DocumentsCheck app")

        self.wait_message("read_passport")

        passport_data = self.read_passport()

        self.logger.debug(f"Passport found: {passport_data}. Looking for a ticket...")

        ticket = self.check_ticket(passport_data)

        self.logger.debug(f"Ticket found: {ticket}. Going to step 2...")
        self.send_page("face")

        face = self.read_face()

        self.send_page("done")

        similarity = face_util.compare_faces(passport_data.face_descriptor, face)
        self.logger.debug(f"Similarity: {similarity}")

        time.sleep(2)

        self.show_preferences()

        self.success = True
        self.logger.debug("DocumentsCheckApp run finished")

    def read_passport(self) -> PassportData:
        self.logger.debug("Reading passport...")
        passport_image = CameraAccessor.documents_camera.image_bgr.copy()
        passport_read_event = threading.Event()
        passport_data: Optional[PassportData] = None
        error: Optional[Exception] = None

        def callback_success(data: PassportData):
            nonlocal passport_data
            passport_data = data
            passport_read_event.set()

        def callback_error(exception: Exception):
            nonlocal error
            error = exception
            passport_read_event.set()

        AsyncProcessor.read_passport_async(passport_image, callback_success, callback_error)
        passport_read_event.wait()

        if error:
            raise error

        passport_found = passport_data is not None

        if not passport_found:
            self.logger.debug("Passport not found.")
            self.send("passport_not_found")
            time.sleep(5)
            raise PassportNotFoundError()
        
        return passport_data

    def check_ticket(self, passport_data: PassportData) -> TicketInfo:
        ticket = TicketsRepository.get_by_passport(passport_data.passport_number)
        if not ticket:
            self.logger.debug("Ticket not found.")
            self.send("ticket_not_found")
            time.sleep(5)
            raise TicketNotFoundError()
        return ticket

    def read_face(self) -> face_util.FaceDescriptor:
        is_rect_displayed = False
        face_center_history_x = []
        face_center_history_y = []
        face_not_found_confirmations = 25   # кол-во кадров, на которых лицо не найдено, после которого квадрат пропадет. Чтобы квадрат не моргал

        face_processing_result: Optional[face_util.FaceDescriptor] = None
        face_processing_error: Optional[Exception] = None
        face_processing_started = False
        time_start = time.time()
        time_start_tracking = 0

        def reset():
            nonlocal is_rect_displayed
            nonlocal time_start_tracking
            nonlocal face_processing_started
            nonlocal face_processing_result
            nonlocal face_processing_error
            nonlocal face_not_found_confirmations
            nonlocal time_start
            self.send("hide_face_rect")
            is_rect_displayed = False
            time_start_tracking = 0
            face_center_history_x.clear()
            face_center_history_y.clear()
            face_not_found_confirmations = 25
            face_processing_started = False
            face_processing_result = None
            face_processing_error = None
            time_start = time.time()

        while True:
            current_time = time.time()

            image = self.crop_image(CameraAccessor.main_camera.image_bgr.copy())

            face_location = face_util.find_face(image)
            if face_location is None:
                if face_not_found_confirmations > 0:
                    face_not_found_confirmations -= 1
                elif is_rect_displayed:
                    reset()
            else:
                if current_time - time_start >= 2:    # задержка после включения камеры, чтобы лицо не находило мгновенно
                    face_not_found_confirmations = 25    # сброс кол-ва кадров для скрытия квадрата

                    if time_start_tracking == 0:
                        time_start_tracking = current_time
                    elif current_time - time_start_tracking > 0.5:
                        if not face_processing_started:

                            def callback_success(descriptor: face_util.FaceDescriptor):
                                nonlocal face_processing_result
                                face_processing_result = descriptor

                            def callback_error(exception: Exception):
                                nonlocal face_processing_error
                                face_processing_error = exception

                            self.logger.debug("Face decriptor processing started")
                            AsyncProcessor.get_face_descriptor_async(image, callback_success, callback_error, face_location=face_location)
                            face_processing_started = True

                        elif face_processing_error:
                            self.logger.exception("Failed to get face descriptor from camera image", exc_info=face_processing_error)
                            reset()

                        elif face_processing_result is not None and current_time - time_start_tracking > 1.5:
                            self.logger.debug(f"Recognition completed")
                            self.send("hide_face_rect")
                            return face_processing_result

                    center = int(face_location[0] + (face_location[2] / 2)), int(face_location[1] + (face_location[3] / 2))
                    if not is_rect_displayed:
                        self.send("show_face_rect")
                        is_rect_displayed = True

                    # фильтр, чтобы квадрат не дергался
                    face_center_history_x.append(center[0])
                    face_center_history_y.append(center[1])

                    if len(face_center_history_x) > 10:
                        del face_center_history_x[0]
                        del face_center_history_y[0]

                    average_center_x = sum(face_center_history_x) / len(face_center_history_x)
                    average_center_y = sum(face_center_history_y) / len(face_center_history_y)

                    x_rel, y_rel = average_center_x / image.shape[1], average_center_y / image.shape[0]
                    self.send("face_rect_position", x=x_rel, y=y_rel)

            gui_server.send_image("/app/image", image)

    @staticmethod
    def crop_image(image: cv2.UMat) -> cv2.UMat:
        # временные преобразования для корректного отображения на мониторе ПК
        # позже будут перенесены в другое место
        # обрезает входное изображение под 9:16 и отражает его по горизонатали (чтобы выглядело как зеркало)
        # TODO: вынести преобразование изображения с камеры в другое место и привязать к конфигу
        h, w, _ = image.shape
        target_ratio = 0.5625  # 9:16
        target_width = h * target_ratio
        image = image[:, int(w / 2 - target_width / 2):int(w / 2 + target_width / 2)]
        image = cv2.flip(image, 1)
        return image

    def show_preferences(self):
        self.send_page("preferences")

        self.wait_connection()
        time.sleep(1)
        self.logger.debug("Connected")
        self.send("preferences", preferences=[
            {
                "callback_data": {"type": "product", "product_id": "water_still_05"},
                "name": "Минеральная вода",
                "image_url": gui_server.get_absolute_http_static_url("images/shop/water.png"),
            },
            {
                "callback_data": {"type": "product", "product_id": "cola"},
                "name": "Добрый Cola 0,33л",
                "image_url": gui_server.get_absolute_http_static_url("images/shop/cola.jpg"),
            },
        ])
        self.logger.debug("Sent preferences")
        message = self.wait_message()
        if message["code"] == "preference_callback":
            self.logger.debug("Selected preference type: %s", message["type"])
            self.process_preference(message)
        else:
            self.logger.debug("No preference selected")

    def process_preference(self, callback_data: Dict[str, Any]):
        if callback_data["type"] == "product":
            url = external.get_product_url(callback_data["product_id"])
            self.logger.debug("Redirecting to external URL: %s", url)
            gui_navigation.set_current_url(url, self.server_path)
            time.sleep(0.5)
            self.send_page("complete")
            self.logger.debug("Waiting...")
            self.wait_connection()
            time.sleep(3)
            self.logger.debug("Returned")