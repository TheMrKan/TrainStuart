from robot.gui.apps import BaseLoopApp
from typing import Optional
import time

from robot.config import instance as config
import robot.core.route as route


class IdleApp(BaseLoopApp):

    NAME = "Idle"
    ASSETS_PATH = "./gui/assets/"

    PAGES = {
        "default": "loading.html",
        "idle": "rest.html",
    }

    next: Optional[str]

    def __init__(self):
        super().__init__()

        self.next = None


    def check_is_running(self) -> bool:
        return super().check_is_running() and not route.is_service_finished()


    def loop_start(self):
        self.send_page("idle")


    def loop(self):
        time.sleep(10)
        

    @staticmethod
    def get_window_params() -> dict:
        # для отладки на ПК. Позже будет переделано. На устройстве должно стоять
        # {"fullscreen": True}
        # TODO: привязать эти параметры к конфигу
        return {"width": 600, "height": 1024}


    @staticmethod
    def get_webview_start_params() -> dict:
        return {"debug": config.idle.show_dev_tools}
