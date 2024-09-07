import time
from dataclasses import dataclass
from typing import Optional
from threading import Thread, Event

from robot.core.navigation import chart, visual_positioning
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
    head_rotation: int


current_x = current_y = 0
current_movement: Optional[Movement]
passage: Zone


def start():
    global current_x, current_y, passage
    current_x, current_y = chart.get_point_position("start")
    passage = chart.zones["passage"]
    robot_interface.set_actual_pos(current_x, current_y)


def go_to_seat(seat: int):
    print(f"Going to seat {seat}")
    seat_pos = chart.get_position_for_seat(seat)
    print(f"Seat position: {seat_pos}")
    movement = prepare_movement(seat_pos)
    process_movement(movement)


def go_to_base():
    movement = prepare_movement((0, 0))
    process_movement(movement)


def prepare_movement(destination: Vector2) -> Movement:
    movement = Movement()
    movement.start = (current_x, current_y)
    movement.destination = destination

    if destination[1] > 0:
        movement.movement_line_y = MOVEMENT_LINE_LEFT
        movement.head_rotation = -90
    else:
        movement.movement_line_y = MOVEMENT_LINE_RIGHT
        movement.head_rotation = 90

    return movement


def process_movement(movement: Movement):
    global current_x, current_y, current_movement

    current_movement = movement

    robot_interface.set_head_rotation(movement.head_rotation, 0)
    time.sleep(0.5)

    thread = Thread(target=robot_interface.move_to, args=(movement.destination[0], 0))
    thread.start()

    for pos in visual_positioning.watcher():
        if not thread.is_alive():
            break

        if not pos:
            continue

        print(pos)

    time.sleep(0.5)
    current_x, current_y = movement.destination
    current_movement = None
    time.sleep(1)


