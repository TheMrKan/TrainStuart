from robot.core.navigation.passenger_zone import PassengerZoneController
from robot.core.navigation.chart import Vector2
from robot.core.navigation import chart
from robot.hardware import robot_interface as irobot


class VendingZoneController(PassengerZoneController):

    MOVING_HEAD_Y = 7
    vending_pos: Vector2

    def __init__(self):
        super().__init__()
        self.vending_pos = chart.get_point_position("vending")