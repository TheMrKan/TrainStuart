import os.path
import threading
import numpy as np
import time
import base64
import cv2
import random
from typing import Callable, Optional, Dict, Any
from datetime import datetime

from robot.hardware.cameras import CameraAccessor
from robot.hardware.audio import AudioOutput
import robot.config as config
from robot.gui.base.app import BaseApp
from robot.gui.base import gui_server, navigation as gui_navigation
import utils.faces as face_util
from robot.core.async_processor import AsyncProcessor
from utils.docs_reader import PassportData
import robot.core.route as route
from robot.gui import external
from utils.cancelations import CancellationToken
from robot.core import server, passengers
from utils.cv import Image
from robot.dev import control_panel


class PassportNotFoundError(Exception):
    pass


class TicketNotFoundError(Exception):
    pass


class DocumentsCheckApp(BaseApp):

    NAME = "DocumentsCheck"
    INITIAL_PAGE = "passport"

    success: bool
    __face_detector: face_util.ContinuousFaceDetector

    def __init__(self):
        super().__init__()
        self.success = False
        self.__face_detector = face_util.ContinuousFaceDetector(lambda: CameraAccessor.main_camera.image_bgr, 500)

    def run(self):
        super().run()
        self.logger.debug("Running DocumentsCheck app")

        cancellation = CancellationToken(self.wait_message_no_block("passport_step2"))
        self.play_audio_for_faces(cancellation)

        passenger = self.read_passport()

        self.logger.debug(f"Passenger found: {passenger}. Going to step 2...")
        self.send_page("face")

        AudioOutput.play_async("face_check.wav")
        face = self.read_face()

        self.send_page("done")

        if passenger.face_descriptor is not None:
            similarity = face_util.compare_faces(passenger.face_descriptor, face)
            self.logger.debug(f"Similarity: {similarity}")
        else:
            passengers.update_face_descriptor(passenger.id, face)
            self.logger.debug("Failed to check faces similarity: passenger doesn't have a saved face")

        time.sleep(2)

        AudioOutput.play_async("preferences.wav")
        self.show_preferences()
        AudioOutput.play_async("goodbye.wav")

        self.success = True
        self.logger.debug("DocumentsCheckApp run finished")

    def play_audio_for_faces(self, cancellation: CancellationToken):
        self.__face_detector.reset()
        try:
            CameraAccessor.main_camera.attach("documents_check")
            while not cancellation:
                state = self.__face_detector.tick()
                if state == self.__face_detector.State.FOUND:
                    AudioOutput.play_async("document.wav")
                elif state == self.__face_detector.State.WAITING:
                    time.sleep(0.25)
                else:
                    time.sleep(0.1)
        finally:
            CameraAccessor.main_camera.detach("documents_check")

    def read_passport(self) -> passengers.Person:
        self.logger.debug("Reading passport...")
        while not CameraAccessor.documents_camera.grab_image():
            time.sleep(0.01)

        passport_image = CameraAccessor.documents_camera.image_bgr.copy()
        passport_read_event = threading.Event()
        passenger_id: Optional[str] = None
        passenger = None
        error: Optional[Exception] = None

        def send_request():
            nonlocal passenger_id
            nonlocal error
            try:
                passenger_id = server.process_document(passport_image)
            except Exception as e:
                error = e
            finally:
                passport_read_event.set()

        threading.Thread(target=send_request, daemon=True).start()
        passport_read_event.wait()

        if error:
            if isinstance(error, server.DocumentProcessingError):
                self.logger.debug("Document processing error: %s", error)
                self.send("passport_not_found")

                try:
                    self.wait_message("", timeout=20)
                    if self.last_message["code"] == "send_to_operator":
                        passport_number = control_panel.request_read_passport()
                        if not passport_number:
                            self.send("invalid_passport")
                            time.sleep(5)
                            raise PassportNotFoundError()

                        passenger = passengers.get_by_passport(passport_number)
                        if not passenger:
                            self.send("ticket_not_found")
                            time.sleep(5)
                            raise TicketNotFoundError()
                    else:
                        raise error
                except TimeoutError:
                    raise error
            else:
                raise error

        if not passenger and not passenger_id:
            self.logger.debug("Passport not found.")
            self.send("passport_not_found")
            time.sleep(5)
            raise TicketNotFoundError()

        if not passenger:
            passenger = passengers.get_by_id(passenger_id)
        if not passenger:
            raise TicketNotFoundError(f"Got remote passenger id {passenger_id} but unable to find it localy")
        
        return passenger

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

        try:
            CameraAccessor.main_camera.attach("documents_check")
            while True:
                current_time = time.time()

                image = self.crop_image(CameraAccessor.main_camera.image_bgr.copy())
                image_ext = self.crop_image(CameraAccessor.main_camera.image_bgr.copy(), 1.2)

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
        finally:
            CameraAccessor.main_camera.detach("documents_check")

    @staticmethod
    def crop_image(image: cv2.UMat, multiplier: float = 1) -> cv2.UMat:
        # временные преобразования для корректного отображения на мониторе ПК
        # позже будут перенесены в другое место
        # обрезает входное изображение под 9:16 и отражает его по горизонатали (чтобы выглядело как зеркало)
        # TODO: вынести преобразование изображения с камеры в другое место и привязать к конфигу
        h, w, _ = image.shape
        target_ratio = 0.5625 * multiplier  # 9:16
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