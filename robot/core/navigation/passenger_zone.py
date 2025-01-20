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

GAP = 5
"""
Минимальный зазор в сантиметрах между корпусом робота и препятствием при построении маршрута
"""

MOVING_HEAD_Y = 25


logger = logging.getLogger(__name__)


class Movement:
    start: Vector2
    destination: Vector2
    intermediate_points: List[Vector2]
    head_rotation_x: int
    head_rotation_y: int


current_movement: Optional[Movement]
passage: Zone
zone: Zone


def start():
    global passage, zone

    zone = chart.zones["passenger_zone"]
    pos = find_start_position()
    if pos is None:
        logger.warning("Failed to calculate start position via visual positioning")
        robot_interface.set_actual_pos(*chart.get_point_position("start"))
    else:
        robot_interface.set_actual_pos(*pos)
        logger.info(f"Start position: {robot_interface.current_x} {robot_interface.current_y}")

    passage = chart.zones["passage"]


def find_start_position() -> Optional[chart.Vector2]:
    robot_interface.set_head_rotation(-90, MOVING_HEAD_Y)

    while True:
        head_distance = robot_interface.get_camera_distance()
        if head_distance == 0:
            time.sleep(0.05)
            continue

        wall_distance = visual_positioning.head_distance_to_wall_distance(head_distance, robot_interface.head_vertical)

        y = zone.p0[1] - wall_distance

        robot_interface.set_actual_pos(robot_interface.current_x, y)

        logger.debug(f"Distance to wall: {wall_distance}; "
                     f"Current position: {robot_interface.current_x, robot_interface.current_y}")

        if wall_distance < visual_positioning.MIN_WALL_DISTANCE:
            logger.debug("Distance is too small")
            # -5 см для запаса
            robot_interface.move_to(robot_interface.current_x, zone.p0[1] - visual_positioning.MIN_WALL_DISTANCE - 5)
        elif wall_distance > visual_positioning.MAX_WALL_DISTANCE:
            logger.debug("Distance is too big")
            # +5 см для запаса
            robot_interface.move_to(robot_interface.current_x, zone.p0[1] - visual_positioning.MAX_WALL_DISTANCE + 5)
        else:
            break
    logger.debug("Wall distance calibration completed")

    time.sleep(0.5)
    marker_name, pos = visual_positioning.try_get_position(robot_interface.head_horizontal,
                                              robot_interface.head_vertical,
                                              head_distance)

    if pos is not None:
        logger.debug(f"Got pos {pos} from marker {marker_name}")
        return pos

    logger.info("Failed to find a marker in front of the camera. Going right...")
    pos = try_find_marker(True)
    if pos:
        return pos

    time.sleep(0.5)
    robot_interface.set_head_rotation(-90, MOVING_HEAD_Y)   # возвращаем голову прямо после поворота направо
    logger.info("Failed to find a marker on the right. Going left...")
    return try_find_marker(False)


def try_find_marker(direction: bool) -> Optional[Vector2]:
    if visual_find_marker_horiz(direction):
        time.sleep(0.5)
        robot_interface.set_head_rotation(-90, MOVING_HEAD_Y)

        logger.info(f"Found marker {'right' if direction else 'left'}")
        if not go_until_marker(direction):
            logger.error(f"Failed to go until marker on the {'right' if direction else 'left'}")
            return None

        while True:
            head_distance = robot_interface.get_camera_distance()
            if head_distance:
                break
            time.sleep(0.05)

        marker_name, pos = visual_positioning.try_get_position(robot_interface.head_horizontal,
                                                               robot_interface.head_vertical,
                                                               head_distance)
        if pos is None:
            logger.error(f"Failed to get visual position ({'right' if direction else 'left'})")
            return None

        logger.debug(f"Got pos {pos} from marker {marker_name} ({'right' if direction else 'left'} side)")
        return pos


def go_until_marker(direction: bool, timeout: float = 20, delay: float = 0.5) -> bool:
    t = time.time()
    delta = 20 * (1 if direction else -1)

    while time.time() - t < timeout:
        robot_interface.move_to(robot_interface.current_x + delta, robot_interface.current_y)
        time.sleep(1.5)
        # current_x не обновляется в move_to. !!! Убрать после добавления передачи координат с робота !!!
        robot_interface.current_x += delta

        is_visible = visual_positioning.is_marker_visible()
        if is_visible:
            return True
        time.sleep(0.5)

    return False


def visual_find_marker_horiz(direction: bool, timeout: float = 3, delay: float = 0.2) -> bool:
    logger.debug(f"Rotating {'right' if direction else 'left'}...")
    t = time.time()
    robot_interface.head_horizontal_run(
        robot_interface.RotationDirection.RIGHT if direction else robot_interface.RotationDirection.LEFT)

    found = False
    try:
        visible_since = 0

        while time.time() - t < timeout:
            is_visible = visual_positioning.is_marker_visible()
            if not is_visible:
                visible_since = 0
            else:
                if visible_since == 0:
                    visible_since = time.time()
                else:
                    if time.time() - visible_since > delay:
                        found = True
                        break
    finally:
        robot_interface.head_horizontal_run(robot_interface.RotationDirection.STOP)

    return found



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


def __sqr_distance(a: Vector2, b: Vector2):
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2


def __is_inside(point: Vector2, area: chart.Zone, gap: int = 0):
    return (area.p1[1] + gap <= point[1] <= area.p0[1] - gap) #(area.p0[0] + gap <= point[0] <= area.p1[0] - gap) and \




def prepare_movement(destination: Vector2, head_y_override: Optional[int] = None) -> Movement:
    movement = Movement()
    movement.start = (robot_interface.current_x, robot_interface.current_y)
    movement.destination = destination
    movement.head_rotation_y = head_y_override or MOVING_HEAD_Y

    if destination[1] >= 0:
        movement.head_rotation_x = -90
        line_y = 0
    else:
        movement.head_rotation_x = 90
        line_y = 0

    movement.intermediate_points = []
    if not __are_nearly_equal(robot_interface.current_y, line_y):
        movement.intermediate_points.append((robot_interface.current_x, line_y))
    if not __are_nearly_equal(line_y, destination[1]):
        movement.intermediate_points.append((destination[0], line_y))

    return movement


def process_movement(movement: Movement):
    global current_movement

    move_points = [movement.start, *movement.intermediate_points, movement.destination]
    control_panel.send_robot_path(move_points)

    current_movement = movement
    control_panel.update_robot_pos(*robot_interface.get_current_position())

    robot_interface.set_head_rotation(movement.head_rotation_x, movement.head_rotation_y)
    time.sleep(0.5)

    marker_name = None
    marker_ts = 0
    point_index = 1
    correction_point_idx = []
    while point_index < len(move_points):
        point = move_points[point_index]
        should_check_passage = point_index not in correction_point_idx
        should_check_passage = should_check_passage and not (robot_interface.current_y + ROBOT_DIMENSIONS[0] + GAP >= passage.p0[1] \
                        or robot_interface.current_y - ROBOT_DIMENSIONS[2] - GAP <= passage.p1[1])
        should_check_passage = should_check_passage and not (point[1] + ROBOT_DIMENSIONS[0] + GAP >= passage.p0[1] \
                        or point[1] - ROBOT_DIMENSIONS[2] - GAP <= passage.p1[1])

        logger.debug(f"Target point index: {point_index}; point: {point}; passage: {should_check_passage}")

        thread = Thread(target=robot_interface.move_to, args=(point[0], point[1]))
        thread.start()
        time.sleep(0.5)

        while thread.is_alive():
            head_distance = robot_interface.get_camera_distance()
            if head_distance == 0:
                time.sleep(0.05)
                continue
            distance_to_wall = visual_positioning.head_distance_to_wall_distance(head_distance, robot_interface.head_vertical)

            time.sleep(0.01)

            robot_interface.get_current_position()

            _marker_name, pos = visual_positioning.try_get_position(
                robot_interface.head_horizontal,
                head_distance,
                distance_to_wall
            )

            valid = False
            if not pos:
                marker_name = None
            else:

                valid = _marker_name == marker_name and time.time() - marker_ts > 0.3
                valid = valid and __sqr_distance((robot_interface.current_x, robot_interface.current_y), pos) < 40 ** 2

                if _marker_name != marker_name:
                    marker_name = _marker_name
                    marker_ts = time.time()

            if valid:
                robot_interface.set_actual_pos(*pos)
            else:
                robot_interface.set_actual_pos(robot_interface.current_x,
                                               visual_positioning.distance_to_wall_to_y(distance_to_wall))

            if should_check_passage and \
                    __sqr_distance(point, (robot_interface.current_x, robot_interface.current_y)) > 15 ** 2 and \
                    __sqr_distance(move_points[point_index-1],(robot_interface.current_x, robot_interface.current_y)) > 15 ** 2 and \
                    ((robot_interface.current_y + ROBOT_DIMENSIONS[0] + GAP >= passage.p0[1]) \
                    or robot_interface.current_y - ROBOT_DIMENSIONS[2] - GAP <= passage.p1[1]):
                logger.debug(f"Collision detected: {robot_interface.current_y + ROBOT_DIMENSIONS[0] + GAP} "
                             f"{robot_interface.current_y - ROBOT_DIMENSIONS[2]} "
                             f"{move_points}")
                correction_target = (robot_interface.current_x, point[1])
                move_points.insert(point_index, correction_target)
                move_points.insert(point_index, (robot_interface.current_x, robot_interface.current_y))
                correction_point_idx.append(point_index+1)
                logger.debug(f"{move_points}")
                control_panel.send_robot_path(move_points)

                act = robot_interface.get_current_position()
                robot_interface.set_actual_pos(*point)
                time.sleep(0.3)
                robot_interface.set_actual_pos(*act)
                time.sleep(0.3)

            time.sleep(0.01)

        point_index += 1
        time.sleep(0.3)

    control_panel.send_robot_path([])
    current_movement = None
    time.sleep(1)


