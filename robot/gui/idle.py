from typing import Optional
import time

from robot.gui.base.app import BaseLoopApp
from robot.config import instance as config
import robot.core.route as route


class IdleApp(BaseLoopApp):

    NAME = "Idle"

    INITIAL_PAGE = "rest"

    next: Optional[str]

    def __init__(self):
        super().__init__()

        self.next = None

    @BaseLoopApp.is_running.getter
    def is_running(self) -> bool:
        return super().is_running and not route.is_service_finished()

    def loop(self):
        time.sleep(10)

