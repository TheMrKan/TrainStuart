import logging
import time

from robot.behaviour.base import BaseBehaviour
from robot.core.navigation import passenger_zone


class CarriageMovingBehaviour(BaseBehaviour):

    def __init__(self):
        super().__init__()

    def initialize(self):
        passenger_zone.start()

    def behave(self):
        passenger_zone.go_to_seat(1)
        time.sleep(3)
        passenger_zone.go_to_seat(5)
        time.sleep(3)
        passenger_zone.go_to_seat(9)
        time.sleep(3)
        passenger_zone.go_to_base()
        time.sleep(3)


