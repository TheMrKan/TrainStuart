import logging
import time
from utils.collections import first

from robot.behaviour.base import BaseBehaviour
from robot.core.navigation import general, passenger_zone, chart
from robot.hardware import robot_interface
from robot.hardware.audio import AudioOutput
from robot.hardware.robot_interface import RobotContainer, Side
from robot.gui.interaction import InteractionApp
from robot.gui.idle import IdleApp
from robot.core import calls


class CarriageMovingBehaviour(BaseBehaviour):
    RESTART_ON_EXCEPTION = False

    def __init__(self):
        super().__init__()

    def initialize(self):
        pass

    def behave(self):
        app = IdleApp()
        app.run()

        general.locate()

        while True:
            general.go_home()

            general.go_to_point((350, 30))
            time.sleep(3)

        exit()

    def __wait_for_call(self) -> int:
        while not any(calls.active_calls):
            time.sleep(2)

        return first(calls.active_calls)

    def on_touch_received(self, state: int, *args):
        if state:
            AudioOutput.play_async("blocked.wav")


