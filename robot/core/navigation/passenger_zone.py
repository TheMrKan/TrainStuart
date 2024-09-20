import math
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

MOVING_HEAD_Y = 20


logger = logging.getLogger(__name__)


class Movement:
    start: Vector2
    destination: Vector2
    intermediate_points: List[Vector2]
    head_rotation_x: int
    head_rotation_y: int


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
    robot_interface.set_head_rotation(-90, MOVING_HEAD_Y)
    head_distance = int(86 / math.cos(math.radians(robot_interface.head_vertical)))
    marker_name, pos = visual_positioning.try_get_position(robot_interface.head_horizontal,
                                              robot_interface.head_vertical,
                                              head_distance)
    if pos is not None:
        return pos

    robot_interface.set_head_rotation(90, MOVING_HEAD_Y)
    marker_name, pos = visual_positioning.try_get_position(robot_interface.head_horizontal,
                                              robot_interface.head_vertical,
                                              head_distance)
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


def __are_nearly_equal(a: float, b: float, limit: float = 3):
    return abs(a - b) <= limit


def prepare_movement(destination: Vector2, head_y_override: Optional[int] = None) -> Movement:
    movement = Movement()
    movement.start = (current_x, current_y)
    movement.destination = destination
    movement.head_rotation_y = head_y_override or MOVING_HEAD_Y

    if destination[1] >= 0:
        movement.head_rotation_x = -90
        line_y = 0
    else:
        movement.head_rotation_x = 90
        line_y = 0

    movement.intermediate_points = []
    '''if not __are_nearly_equal(current_y, line_y):
        movement.intermediate_points.append((current_x, line_y))
    if not __are_nearly_equal(line_y, destination[1]):
        movement.intermediate_points.append((destination[0], line_y))'''

    return movement


def process_movement(movement: Movement):
    global current_x, current_y, current_movement

    control_panel.send_robot_path([movement.start, *movement.intermediate_points, movement.destination])

    current_movement = movement
    control_panel.update_robot_pos(*movement.start)

    robot_interface.set_head_rotation(movement.head_rotation_x, movement.head_rotation_y)
    time.sleep(0.5)

    for point in (*movement.intermediate_points, movement.destination):

        thread = Thread(target=robot_interface.move_to, args=(point[0], point[1]))
        thread.start()

        if abs(current_x - point[0]) > abs(current_y - point[1]):
            time.sleep(0.5)

            last_send_pos: Optional[chart.Vector2] = None
            last_send_time: float = 0
            marker_name = None
            marker_counter = 0
            while thread.is_alive():
                # head_distance = robot_interface.get_camera_distance()
                time.sleep(0.01)
                head_distance = int(86 / math.cos(math.radians(robot_interface.head_vertical)))
                #print(head_distance, current_y, 86, robot_interface.head_vertical)
                _marker_name, pos = visual_positioning.try_get_position(
                    robot_interface.head_horizontal,
                    robot_interface.head_vertical,
                    head_distance
                )

                if not _marker_name:
                    marker_name = None
                    marker_counter = 0

                    _path = (time.time() - last_send_time) * robot_interface.WHEELS_SPEED_X
                    if current_x > point[0]:
                        _path = -_path
                    _last_x = last_send_pos[0] if last_send_pos is not None else current_x
                    _x = int(round(_last_x + _path))
                    control_panel.update_robot_pos(_x, current_y)
                    continue
                else:
                    if _marker_name != marker_name:
                        marker_counter = 0
                        marker_name = _marker_name

                    marker_counter += 1
                    if marker_counter < 30:
                        continue

                if last_send_pos is None or abs(last_send_pos[0] - pos[0]) > 1:
                    if last_send_pos is None or abs(last_send_pos[0] - pos[0]) < (time.time() - last_send_time) * robot_interface.WHEELS_SPEED_X * 2.5:
                        logger.debug(pos)
                        robot_interface.set_actual_pos(pos[0], 0)
                        control_panel.update_robot_pos(pos[0], current_y)
                        last_send_pos = pos
                        last_send_time = time.time()
                    else:
                        logger.debug(f"Delta is too big ({abs(last_send_pos[0] - pos[0]):.1f} / {(time.time() - last_send_time) * robot_interface.WHEELS_SPEED_X * 2.5:.1f})")
                else:
                    #logger.debug(f"Delta is too low ({abs(last_send_pos[0] - pos[0]):.1f})")
                    pass

            logger.debug("Loop completed")

        else:
            last_send_time = time.time()
            while thread.is_alive():
                speed = robot_interface.WHEELS_SPEED_Y_RIGHT \
                        if current_y > point[1] \
                        else robot_interface.WHEELS_SPEED_Y_LEFT
                _path = (time.time() - last_send_time) * speed
                if current_y > point[1]:
                    _path = -_path
                _y = int(round(current_y + _path))
                control_panel.update_robot_pos(current_x, _y)

                time.sleep(0.05)

        time.sleep(2)

        current_x, current_y = point
        control_panel.update_robot_pos(current_x, current_y)
    control_panel.send_robot_path([])
    current_movement = None
    time.sleep(1)


