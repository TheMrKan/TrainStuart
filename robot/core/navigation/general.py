from typing import Optional
import time
import logging

from robot.core.navigation import visual_positioning, chart
from robot.core.navigation.chart import Vector2, Point, Zone
from robot.hardware import robot_interface
from robot.core.navigation.base_zone_controller import BaseZoneController
from robot.core.navigation.passenger_zone import PassengerZoneController
from robot.core.navigation.vending_zone import VendingZoneController


logger = logging.getLogger(__name__)

FIND_MARKER_HEAD_Y = 25
ZONE_CONTROLLERS = {
    "passenger_zone": PassengerZoneController,
    "vending_zone": VendingZoneController,
}

zone: Zone = None
zone_controller: BaseZoneController = None

HOME: Point
GATE: Point


def init():
    global HOME
    global GATE
    chart.load()

    HOME = chart.points["vending"]
    GATE = chart.points["gate"]

    for zc in ZONE_CONTROLLERS.values():
        zc.class_init()

    __set_zone(chart.zones["passenger_zone"])


def __set_zone(_zone: Zone):
    global zone
    global zone_controller
    if zone == _zone:
        return

    zone = _zone
    if zone_controller:
        zone_controller.dispose()
    zone_controller = ZONE_CONTROLLERS[zone.id]()


def go_home():
    go_to_point((HOME.x, HOME.y))


def go_to_point(pos: Vector2):
    target_zone = chart.get_zone(pos)

    if target_zone != zone:
        go_to_gate()
    __set_zone(target_zone)

    zone_controller.go_to_point(pos)


def go_to_gate():
    zone_controller.go_to_point((GATE.x, GATE.y))


def locate():
    pos = __try_locate()
    if pos is None:
        logger.warning("Failed to calculate start position via visual positioning")
        robot_interface.set_actual_pos(*chart.get_point_position("start"))
    else:
        robot_interface.set_actual_pos(*pos)

    _zone = chart.get_zone((robot_interface.current_x, robot_interface.current_y))

    if not _zone:
        raise RuntimeError(f"Failed to find a zone for the located position: "
                           f"{(robot_interface.current_x, robot_interface.current_y)}")

    __set_zone(_zone)

    logger.info(f"Start position: {robot_interface.current_x} {robot_interface.current_y} (zone: {zone.id})")


def __try_locate() -> Optional[chart.Vector2]:
    robot_interface.set_head_rotation(-90, FIND_MARKER_HEAD_Y)

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
    pos = __try_find_marker(True)
    if pos:
        return pos

    time.sleep(0.5)
    robot_interface.set_head_rotation(-90, FIND_MARKER_HEAD_Y)   # возвращаем голову прямо после поворота направо
    logger.info("Failed to find a marker on the right. Going left...")
    return __try_find_marker(False)


def __try_find_marker(direction: bool) -> Optional[chart.Vector2]:
    if __visual_find_marker_horiz(direction):
        time.sleep(0.5)
        robot_interface.set_head_rotation(-90, FIND_MARKER_HEAD_Y)

        logger.info(f"Found marker {'right' if direction else 'left'}")
        if not __go_until_marker(direction):
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


def __go_until_marker(direction: bool, timeout: float = 20, delay: float = 0.5) -> bool:
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


def __visual_find_marker_horiz(direction: bool, timeout: float = 3, delay: float = 0.2) -> bool:
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