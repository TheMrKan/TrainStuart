from threading import Thread
import time
from typing import Optional
import logging

from .base_zone_controller import BaseZoneController, Movement
from robot.core.navigation import chart, visual_positioning
from robot.core.navigation.chart import Vector2, Point, Zone
from robot.hardware import robot_interface as irobot
from utils.misc import are_nearly_equal, sqr_distance
from robot.hardware.cameras import CameraAccessor


logger: logging.Logger = logging.getLogger(__name__)


class PassengerZoneController(BaseZoneController):

    MOVING_HEAD_Y = 25

    passage: Zone
    prev_marker_name: Optional[str] = None
    prev_marker_ts: float = 0

    @classmethod
    def class_init(cls):
        cls.passage = chart.zones["passage"]

    def __init__(self):
        super().__init__()

    def go_to_seat(self, seat: int):
        seat_pos = chart.get_position_for_seat(seat)
        logger.info(f"Going to seat {seat} {seat_pos}")
        self.go_to_point(seat_pos)

    def _process_movement(self, *args):
        try:
            CameraAccessor.main_camera.attach("passenger_zone")
            super()._process_movement(*args)
        finally:
            CameraAccessor.main_camera.detach("passenger_zone")

    def _move(self, point: Vector2):
        if sqr_distance(point, (irobot.current_x, irobot.current_y)) < 16:
            logger.debug(f"Points are too close: {point} {(irobot.current_x, irobot.current_y)}")
            return

        is_y = abs(irobot.current_x - point[0]) < abs(irobot.current_y - point[1])
        line = self.__select_line(point)
        logger.debug(f"Line select #1: {line}")

        target_pos = point
        if line is not None:
            direction = 1 if irobot.current_y < line else -1
            target_pos = point[0], point[1] - (min(10, abs(irobot.current_y - line))) * direction
            logger.debug(f"Corrected target point: {target_pos}")

        thread = Thread(target=irobot.move_to, args=target_pos)
        thread.start()
        time.sleep(0.2)

        while thread.is_alive():
            self.__update_position(is_y)

        line = self.__select_line((irobot.current_x, irobot.current_y))
        logger.debug(f"Line select #1: {line}")
        if line is not None:
            self.__try_align_to_line(line)

    def __select_line(self, point: Vector2) -> Optional[int]:
        line = None
        if abs(point[1] - chart.LINE_Y) < 15:
            line = chart.LINE_Y
        elif abs(point[1] - chart.VENDING_LINE_Y) < 15:
            line = chart.VENDING_LINE_Y

        return line

    def __try_align_to_line(self, line):
        irobot.move_to_line(irobot.Side.LEFT if irobot.current_y < line else irobot.Side.RIGHT)
        irobot.set_actual_pos(irobot.current_x, line)

    def __update_position(self, is_y: bool):
        head_distance = irobot.get_camera_distance()
        if head_distance == 0:
            time.sleep(0.05)
            return
        self.distance_to_wall = visual_positioning.head_distance_to_wall_distance(head_distance,
                                                                                  irobot.head_vertical)
        marker_name, marker_pos = visual_positioning.try_get_position(
            irobot.head_horizontal,
            head_distance,
            self.distance_to_wall
        )
        
        if marker_pos and not is_y:
            marker_pos = (marker_pos[0], irobot.current_y)

        irobot.get_current_position()

        if self.__is_marker_valid(marker_name, marker_pos):
            irobot.set_actual_pos(*marker_pos)

        # self.__calculate_rot()

        time.sleep(0.2)

    def __is_marker_valid(self, name: Optional[str], pos: Vector2) -> bool:
        if not name or not pos:
            return False

        valid = name == self.prev_marker_name and time.time() - self.prev_marker_ts > 0.3
        valid = valid and sqr_distance((irobot.current_x, irobot.current_y), pos) < 40 ** 2

        if name != self.prev_marker_name:
            self.prev_marker_name = name
            self.prev_marker_ts = time.time()

        return valid

