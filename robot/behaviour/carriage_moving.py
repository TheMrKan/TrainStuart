import logging
import time
from utils.collections import first

from robot.behaviour.base import BaseBehaviour
from robot.core.navigation import general, passenger_zone, chart
from robot.hardware import robot_interface
from robot.hardware.audio import AudioOutput
from robot.hardware.robot_interface import RobotContainer, Side
from robot.gui.interaction import InteractionApp
from robot.gui.base.app import BaseApp
from robot.gui.idle import IdleApp
from robot.core import calls


class CarriageMovingBehaviour(BaseBehaviour):
    RESTART_ON_EXCEPTION = False
    app: BaseApp = None

    def __init__(self):
        super().__init__()

    def initialize(self):
        pass

    def behave(self):
        self.app = IdleApp()
        self.app.run()

        robot_interface.on_command.on("Tch", self.on_touch_received)

        general.locate()
        if not any(calls.active_calls):
            general.go_home()

        while True:
            seat = self.__wait_for_call()
            general.go_to_seat(seat)

            self.__interact()
            calls.active_calls.remove(seat)

            if not any(calls.active_calls):
                general.go_home()

        exit()

    def __wait_for_call(self) -> int:
        while not any(calls.active_calls):
            time.sleep(0.5)

        return first(calls.active_calls)

    def __interact(self):
        self.app.shutdown()
        self.app = InteractionApp()

        self.app.run()
        while self.app.is_running:
            time.sleep(1)
        self.app = IdleApp()
        self.app.run()

    def on_touch_received(self, state: int, *args):
        if isinstance(self.app, InteractionApp):
            return

        if state:
            AudioOutput.play_async("blocked.wav")


