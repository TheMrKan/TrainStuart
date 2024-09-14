import time
from dataclasses import dataclass
from typing import Optional, List
from threading import Thread, Event
import logging

from robot.core.navigation import chart, visual_positioning
from robot.core.navigation.chart import Vector2, Zone
from robot.hardware import robot_interface
from robot.dev import control_panel


ROBOT_DIMENSIONS = (13, 44, 13, 44)
"""
Габаритные размеры робота в сантиметрах в 4 стороны относительно точки, которая считается позицией робота. Порядок: Y+, X+, Y-, X-
"""

GAP = 10
"""
Минимальный зазор в сантиметрах между корпусом робота и препятствием при построении маршрута
"""



logger = logging.getLogger(__name__)


class Movement:
    start: Vector2
    destination: Vector2
    intermediate_points: List[Vector2]
    head_rotation: int


current_x = current_y = 0
current_movement: Optional[Movement]
passage: Zone


def start():
    global current_x, current_y, passage
    pos = find_start_position()
    if pos is None:
        logger.warning("Failed to calculate start position via visual positioning")
        current_x, current_y = chart.get_point_position("start")
    else:
        current_x, current_y = pos
        logger.info(f"Start position: {current_x} {current_y}")

    robot_interface.set_actual_pos(current_x, current_y)
    control_panel.update_robot_pos(current_x, current_y)

    passage = chart.zones["passage"]


def find_start_position() -> Optional[chart.Vector2]:
    robot_interface.set_head_rotation(-90, 0)
    pos = visual_positioning.try_get_position(robot_interface.head_horizontal)
    if pos is not None:
        return pos

    robot_interface.set_head_rotation(90, 0)
    pos = visual_positioning.try_get_position(robot_interface.head_horizontal)
    return pos


def go_to_seat(seat: int):
    logger.debug(f"Going to seat {seat}")
    seat_pos = chart.get_position_for_seat(seat)
    logger.debug(f"Seat position: {seat_pos}")
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
        #movement.head_rotation = -90
        line_y = passage.p0[1] - ROBOT_DIMENSIONS[0] - GAP
    else:
        #movement.head_rotation = 90
        line_y = passage.p1[1] + ROBOT_DIMENSIONS[2] + GAP
    movement.head_rotation = 90

    movement.intermediate_points = [(current_x, line_y), (destination[0], line_y)]

    return movement


def process_movement(movement: Movement):
    global current_x, current_y, current_movement

    control_panel.send_robot_path([movement.start, *movement.intermediate_points, movement.destination])

    current_movement = movement
    control_panel.update_robot_pos(*movement.start)

    robot_interface.set_head_rotation(movement.head_rotation, 0)
    time.sleep(0.5)

    thread = Thread(target=robot_interface.move_to, args=(movement.destination[0], 0))
    thread.start()
    time.sleep(0.5)

    start_time = time.time()
    last_send_pos: Optional[chart.Vector2] = None
    last_send_time: float = 0
    while thread.is_alive():
        pos = visual_positioning.try_get_position(movement.head_rotation)

        _path = (time.time() - start_time) * robot_interface.WHEELS_SPEED_X
        if movement.start[0] > movement.destination[0]:
            _path = -_path
        _x = int(round(movement.start[0] + _path))
        control_panel.update_robot_pos(_x, 0)

        if not pos:
            continue

        if last_send_pos is None or abs(last_send_pos[0] - pos[0]) > 5:
            if last_send_pos is None or abs(last_send_pos[0] - pos[0]) < (time.time() - last_send_time) * robot_interface.WHEELS_SPEED_X * 2:
                logger.debug(pos)
                robot_interface.set_actual_pos(pos[0], 0)
                last_send_pos = pos
                last_send_time = time.time()
            else:
                logger.debug(f"Delta is too big ({abs(last_send_pos[0] - pos[0]):.1f} / {(time.time() - last_send_time) * robot_interface.WHEELS_SPEED_X * 2:.1f})")
        else:
            #logger.debug(f"Delta is too low ({abs(last_send_pos[0] - pos[0]):.1f})")
            pass


    logger.debug("Loop completed")

    time.sleep(0.5)
    current_x, current_y = movement.destination
    control_panel.update_robot_pos(current_x, current_y)
    control_panel.send_robot_path([])
    current_movement = None
    time.sleep(1)


