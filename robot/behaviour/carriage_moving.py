import logging
import time

from robot.behaviour.base import BaseBehaviour
from robot.core.navigation import passenger_zone, chart
from robot.hardware import robot_interface
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

        vending = chart.get_point_position("vending")
        self.logger.debug("Going to vending")
        time.sleep(1)
        robot_interface.set_head_rotation(-90, 0)

        robot_interface.move_to(vending[0], 0)

        robot_interface.move_to(vending[0], 60)

        robot_interface.open_container(RobotContainer.SMALL_FRONT, Side.LEFT)

        robot_interface.open_container(RobotContainer.BIG, Side.LEFT)

        time.sleep(3)

        robot_interface.close_container(RobotContainer.SMALL_FRONT)

        robot_interface.close_container(RobotContainer.BIG)

        robot_interface.move_to(vending[0], 0)

        robot_interface.move_to(0, 0)

        passenger_zone.start()
        passenger_zone.go_to_seat(2)

        robot_interface.open_container(RobotContainer.BIG, Side.LEFT)

        time.sleep(3)

        robot_interface.close_container(RobotContainer.BIG)

        passenger_zone.go_to_seat(4)

        robot_interface.open_container(RobotContainer.SMALL_FRONT, Side.LEFT)

        robot_interface.set_head_rotation(-90, -10)

        app.shutdown()
        app = InteractionApp()
        app.run()
        while app.is_running:
            time.sleep(1)

        app = IdleApp()
        app.run()

        time.sleep(1)

        robot_interface.close_container(RobotContainer.SMALL_FRONT)
        time.sleep(2)
        passenger_zone.go_to_base()

        while True:
            time.sleep(1)


