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
        m = passenger_zone.prepare_movement((140, 20))
        self.logger.info(f"Moving to point 0")
        passenger_zone.process_movement(m)
        self.logger.info(f"Arrived to point 0")

        time.sleep(3)

        m = passenger_zone.prepare_movement((0, 20))
        self.logger.info(f"Moving to point 1")
        passenger_zone.process_movement(m)
        self.logger.info(f"Arrived to point 1")

        time.sleep(5)


