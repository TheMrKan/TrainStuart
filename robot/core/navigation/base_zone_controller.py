from typing import List, Optional
from abc import abstractmethod

from robot.core.navigation.chart import Vector2, Point
from robot.hardware import robot_interface as irobot
from utils.misc import are_nearly_equal
from robot.dev import control_panel


class Movement:
    start: Vector2
    destination: Vector2
    intermediate_points: List[Vector2]
    head_rotation_x: int
    head_rotation_y: int


class BaseZoneController:

    MOVING_HEAD_Y = 25
    current_movement: Optional[Movement] = None
    target_point: Optional[Vector2] = None
    start_point: Optional[Vector2] = None

    @classmethod
    def class_init(cls):
        pass

    def go_to_point(self, point: Vector2):
        movement = self._prepare_movement(point)
        self._process_movement(movement)

    def _prepare_movement(self, destination: Vector2) -> Movement:
        irobot.get_current_position()

        movement = Movement()
        movement.start = (irobot.current_x, irobot.current_y)
        movement.destination = destination
        movement.head_rotation_y = self.MOVING_HEAD_Y

        if destination[1] >= 0:
            movement.head_rotation_x = -90
            line_y = 0
        else:
            movement.head_rotation_x = 90
            line_y = 0

        movement.intermediate_points = []
        if not are_nearly_equal(irobot.current_y, line_y):
            movement.intermediate_points.append((irobot.current_x, line_y))
        if not are_nearly_equal(line_y, destination[1]):
            movement.intermediate_points.append((destination[0], line_y))

        return movement

    def _process_movement(self, movement: Movement):
        self.current_movement = movement
        self._send_movement(movement)

        irobot.set_head_rotation(-90, self.MOVING_HEAD_Y)

        self.start_point = movement.start
        for point in (*movement.intermediate_points, movement.destination):
            self.target_point = point
            self._move(point)
            self.start_point = point

        self.target_point = None
        self.current_movement = None
        self._send_movement(None)

    @staticmethod
    def _send_movement(movement: Optional[Movement]):
        if movement:
            move_points = [movement.start, *movement.intermediate_points, movement.destination]
        else:
            move_points = []
        control_panel.send_robot_path(move_points)

    def _move(self, point: Vector2):
        pass

    def dispose(self):
        pass
