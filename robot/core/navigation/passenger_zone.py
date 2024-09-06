from dataclasses import dataclass
from typing import Optional

from robot.core.navigation import chart
from robot.core.navigation.chart import Vector2, Zone
from robot.hardware import robot_interface


ROBOT_DIMENSIONS = (13, 44, 13, 44)
"""
Габаритные размеры робота в сантиметрах в 4 стороны относительно точки, которая считается позицией робота. Порядок: Y+, X+, Y-, X-
"""

GAP = 5
"""
Минимальный зазор в сантиметрах между корпусом робота и препятствием при построении маршрута
"""

MOVEMENT_LINE_LEFT = -30
"""
Координата Y линии, по которой передвигается робот, прижавшись к левому краю
"""

MOVEMENT_LINE_RIGHT = 30
"""
Координата Y линии, по которой передвигается робот, прижавшись к правому краю
"""


class Movement:
    start: Vector2
    destination: Vector2
    movement_line_y: int


current_x = current_y = 0
current_movement: Optional[Movement]
passage: Zone


def start():
    global current_x, current_y, passage
    current_x, current_y = chart.get_point_position("start")
    passage = chart.zones["passage"]


def go_to_seat(seat: int):
    seat_pos = chart.get_position_for_seat(seat)
    movement = prepare_movement(seat_pos)
    process_movement(movement)


def prepare_movement(destination: Vector2) -> Movement:
    movement = Movement()
    movement.start = (current_x, current_y)
    movement.destination = destination

    if destination[1] > 0:
        movement.movement_line_y = MOVEMENT_LINE_LEFT
    else:
        movement.movement_line_y = MOVEMENT_LINE_RIGHT

    return movement


def process_movement(movement: Movement):
    global current_x, current_y, current_movement

    current_movement = movement

    robot_interface.move_to(current_x, movement.movement_line_y)
    current_y = movement.movement_line_y

    robot_interface.move_to(movement.destination[0], movement.movement_line_y)
    current_x = movement.destination[0]

    robot_interface.move_to(movement.destination[0], movement.destination[1])
    current_y = movement.destination[1]


