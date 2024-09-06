import logging

from robot.behaviour.base import BaseBehaviour
from robot.core.navigation import passenger_zone


class CarriageMovingBehaviour(BaseBehaviour):

    def __init__(self):
        super().__init__()

    def initialize(self):
        passenger_zone.start()

    def behave(self):
        passenger_zone.go_to_seat(1)


