from threading import Thread
import time
from typing import Optional

from .base_zone_controller import BaseZoneController, Movement
from robot.core.navigation import chart, visual_positioning
from robot.core.navigation.chart import Vector2, Point, Zone
from robot.hardware import robot_interface as irobot
from utils.misc import are_nearly_equal, sqr_distance


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

    def _move(self, point: Vector2):
        self.last_correction = 0

        thread = Thread(target=irobot.move_to, args=(point[0], point[1]))
        thread.start()
        time.sleep(0.2)

        while thread.is_alive():
            self.__update_position()

    def __update_position(self):
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

        irobot.get_current_position()

        if self.__is_marker_valid(marker_name, marker_pos):
            irobot.set_actual_pos(*marker_pos)
        else:
            actual_y = visual_positioning.distance_to_wall_to_y(self.distance_to_wall)    # TODO: убрать хардкод позиции стены в методе
            irobot.set_actual_pos(irobot.current_x, actual_y)

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

    last_correction: int = 0

    def __calculate_rot(self):
        movement_dir = self.target_point[0] - self.start_point[0] < 0

        target_distance_to_wall = visual_positioning.y_to_distance_to_wall(self.target_point[1])

        delta = target_distance_to_wall - self.distance_to_wall

        if abs(delta) > 4:
            correction = 100
        elif abs(delta) > 3:
            correction = 75
        elif abs(delta) > 2:
            correction = 75
        else:
            correction = 0

        if delta < 0:
            correction = -correction

        print(delta, correction)
        if correction == self.last_correction:
            return

        irobot.set_speed_correction(correction)
        self.last_correction = correction

