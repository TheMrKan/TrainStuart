import webview
from webview.dom.dom import Element
import time
import base64
import cv2
import random

from robot.hardware.cameras import CameraAccessor
import robot.config as config
from robot.gui.apps import BasePipelineApp, PipelineLogicError


class PassportNotFoundError(PipelineLogicError):
    pass


class DocumentsCheckApp(BasePipelineApp):

    NAME = "DocumentsCheck"
    ASSETS_PATH = "./gui/assets/"

    PAGES = {
        "default": "loading.html",
        "put_passport": "passport.html",
        "face": "face.html",
    }

    def pipeline(self):
        self.send_page("put_passport")

        self.api.await_continue()

        self.logger.debug("Reading passport...")
        # проверка паспорта
        time.sleep(random.randint(2, 5))
        passport_found = int(random.randint(0, 1))

        if not passport_found:
            self.logger.debug("Passport not found.")
            self.show_step1_error()
            self.api.await_continue()
            raise PassportNotFoundError()

        self.logger.debug("Passport found. Going to step 2...")
        self.send_page("face")

        image_element = self.window.dom.get_element("#cameraImage")

        with CameraAccessor.main_camera:
            while True:
                if not self.check_is_running():
                    return

                self.send_camera_image(image_element, CameraAccessor.main_camera.image_bgr.copy())

    def show_step1_error(self):
        self.window.evaluate_js("""
            $("#process").toggle();
            $("#wrong").toggle();
            """)

    @staticmethod
    def send_camera_image(element: Element, image: cv2.Mat):
        # временные преобразования для корректного отображения на мониторе ПК
        # позже будут перенесены в другое место
        # обрезает входное изображение под 9:16 и отражает его по горизонатали (чтобы выглядело как зеркало)
        # TODO: вынести преобразование изображения с камеры в другое место и привязать к конфигу
        h, w, _ = image.shape
        target_ratio = 0.5625    # 9:16
        target_width = h * target_ratio
        image = image[:, int(w / 2 - target_width / 2):int(w / 2 + target_width / 2)]
        cv2.flip(image, 1, image)

        _, png = cv2.imencode(".png", image)
        image_b64 = base64.b64encode(png).decode("utf-8")
        element.attributes["src"] = f"data:image/png;base64, {image_b64}"

    @staticmethod
    def get_window_params() -> dict:
        # для отладки на ПК. Позже будет переделано. На устройстве должно стоять
        # {"fullscreen": True}
        # TODO: привязать эти параметры к конфигу
        return {"width": 600, "height": 1024}

    @staticmethod
    def get_webview_start_params() -> dict:
        return {"debug": config.instance.passport_check.show_dev_tools}

