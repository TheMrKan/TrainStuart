import threading
import numpy as np
import webview
import time
import base64
import cv2
import random
from typing import Callable, Optional
from datetime import datetime

from robot.hardware.cameras import CameraAccessor
import robot.config as config
from robot.gui.apps import BasePipelineApp, PipelineLogicError
import utils.faces as face_util
from robot.core.async_processor import AsyncProcessor
from robot.core.tickets import TicketsRepository, TicketInfo
from utils.cancelations import sleep, await_event, CancellationToken
from utils.scanner import PassportData
import robot.core.route as route


class PassportNotFoundError(PipelineLogicError):
    pass


class TicketNotFoundError(PipelineLogicError):
    pass


class DocumentsCheckApp(BasePipelineApp):

    NAME = "DocumentsCheck"
    ASSETS_PATH = "./gui/assets/"

    PAGES = {
        "default": "loading.html",
        "put_passport": "passport.html",
        "face": "face.html",
        "done": "done.html"
    }

    is_serving: bool

    def __init__(self):
        super().__init__()

        self.is_serving = False

    def check_is_running(self) -> bool:
        return super().check_is_running() and (not route.is_boarding_finished() or self.is_serving)

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
        await_event(passport_read_event, None, self.cancellation)

        if error:
            raise error

        passport_found = passport_data is not None

        if not passport_found:
            self.logger.debug("Passport not found.")
            self.show_passport_not_found()
            self.api.await_continue(5)
            raise PassportNotFoundError()
        
        return passport_data

    def check_ticket(self, passport_data: PassportData) -> TicketInfo:
        ticket = TicketsRepository.get_by_passport(passport_data.passport_number)
        if not ticket:
            self.logger.debug("Ticket not found.")
            self.show_ticket_not_found()
            self.api.await_continue(5)
            raise TicketNotFoundError()
        return ticket

    def read_face(self) -> face_util.FaceDescriptor:
        is_rect_displayed = False
        face_center_history_x = []
        face_center_history_y = []
        face_not_found_confirmations = 25   # кол-во кадров, на которых лицо не найдено, после которого квадрат пропадет. Чтобы квадрат не моргал

        face_processing_result: face_util.FaceDescriptor | None  = None
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
            self.hide_face_rect()
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
            if not self.check_is_running():
                return
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
                            self.hide_face_rect()
                            return face_processing_result

                    center = int(face_location[0] + (face_location[2] / 2)), int(face_location[1] + (face_location[3] / 2))
                    if not is_rect_displayed:
                        self.show_face_rect()
                        is_rect_displayed = True

                    # фильтр, чтобы квадрат не дергался
                    face_center_history_x.append(center[0])
                    face_center_history_y.append(center[1])

                    if len(face_center_history_x) > 10:
                        del face_center_history_x[0]
                        del face_center_history_y[0]

                    average_center_x = sum(face_center_history_x) / len(face_center_history_x)
                    average_center_y = sum(face_center_history_y) / len(face_center_history_y)

                    # вычитаем из 1, т. к. изображение выводится зеркально
                    self.set_face_rect_pos(1 - average_center_x / image.shape[1], average_center_y / image.shape[0])

            self.send_camera_image(image)

    def pipeline(self):
        self.is_serving = False
        self.send_page("put_passport")

        # если ожидание завершено из-за таймаута, значит настало время отправления. Приложение должно закрыться
        # после завершения пайплайна check_is_running вернет False и выполнение завершится
        if not self.api.await_continue((route.departure_time - datetime.now()).total_seconds()):
            return
        
        self.is_serving = True

        passport_data = self.read_passport()

        self.logger.debug(f"Passport found: {passport_data}. Looking for a ticket...")

        ticket = self.check_ticket(passport_data)

        self.logger.debug(f"Ticket found: {ticket}. Going to step 2...")
        self.send_page("face")

        face = self.read_face()

        self.send_page("done")

        similarity = face_util.compare_faces(passport_data.face_descriptor, face)
        self.logger.debug(f"Similarity: {similarity}")

        sleep(5, self.cancellation)

    def show_passport_not_found(self):
        self.window.evaluate_js("""
            $("#process").toggle();
            $("#no_passport").toggle();
            """)
        
    def show_ticket_not_found(self):
        self.window.evaluate_js("""
            $("#process").toggle();
            $("#no_ticket").toggle();
            """)

    def hide_face_rect(self):
        self.window.evaluate_js("disableRect();")

    def show_face_rect(self):
        self.window.evaluate_js("enableRect();")

    def set_face_rect_pos(self, x_rel: float, y_rel: float):
        '''
        x и y задаются в процентах от 0 до 1.
        '''
        self.window.evaluate_js(f"setRectPos({x_rel}, {y_rel});")

    def send_camera_image(self, image: cv2.Mat):
        cv2.flip(image, 1, image)
        _, png = cv2.imencode(".png", image)
        image_b64 = base64.b64encode(png).decode("utf-8")
        self.window.evaluate_js(f"setCameraImage('data:image/png;base64, {image_b64}');")

    @staticmethod
    def crop_image(image: cv2.UMat) -> cv2.UMat:
        # временные преобразования для корректного отображения на мониторе ПК
        # позже будут перенесены в другое место
        # обрезает входное изображение под 9:16 и отражает его по горизонатали (чтобы выглядело как зеркало)
        # TODO: вынести преобразование изображения с камеры в другое место и привязать к конфигу
        h, w, _ = image.shape
        target_ratio = 0.5625  # 9:16
        target_width = h * target_ratio
        return image[:, int(w / 2 - target_width / 2):int(w / 2 + target_width / 2)]

    @staticmethod
    def get_window_params() -> dict:
        # для отладки на ПК. Позже будет переделано. На устройстве должно стоять
        # {"fullscreen": True}
        # TODO: привязать эти параметры к конфигу
        return {"width": 600, "height": 1024}

    @staticmethod
    def get_webview_start_params() -> dict:
        return {"debug": config.instance.passport_check.show_dev_tools}

