import logging
import time

from robot.behaviour.base import BaseBehaviour
from robot.core.navigation import passenger_zone, chart
from robot.hardware import robot_interface
from robot.hardware.audio import AudioOutput
from robot.hardware.robot_interface import RobotContainer, Side
from robot.gui.interaction import InteractionApp
from robot.gui.idle import IdleApp


class CarriageMovingBehaviour(BaseBehaviour):

    def __init__(self):
        super().__init__()

    def initialize(self):
        pass

    def behave(self):
        app = IdleApp()
        app.run()

        passenger_zone.start()
        while True:
            input("Press enter to go to base...")

            passenger_zone.go_to_base()

            input("Press enter to go to seat 4...")

            passenger_zone.go_to_seat(4)

        while True:
            time.sleep(1)

    def on_touch_received(self, state: int, *args):
        if state:
            AudioOutput.play_async("blocked.wav")


