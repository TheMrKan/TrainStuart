import enum
import time
import logging
import math

from robot.hardware.robot_interface import *

__logger = logging.getLogger(__name__)

HEAD_HORIZONTAL_SPEED = 9 / 180
HEAD_VERTICAL_SPEED = 2 / 30

head_horizontal = 0
head_vertical = 0

wheels_x, wheels_y = 0, 0


def initialize():
    time.sleep(5)


def stop():
    pass


def move_to(x: int, y: int):
    global wheels_x, wheels_y
    dst = math.sqrt((wheels_x - x) ** 2 + (wheels_y - y) ** 2)
    time.sleep(dst / WHEELS_SPEED_X)
    wheels_x, wheels_y = x, y


def rotate_to(angle: int):
    time.sleep(1)


def set_actual_pos(x: int, y: int):
    pass


def set_head_rotation(horiz: int, vert: int, completion=True):
    global head_horizontal
    global head_vertical
    horiz_distance = abs(head_horizontal - horiz)
    vert_distance = abs(head_vertical - vert)
    head_horizontal = horiz
    head_vertical = vert
    delay = horiz_distance * HEAD_HORIZONTAL_SPEED + vert_distance * HEAD_VERTICAL_SPEED
    __logger.debug(f"[SIMULATE {delay:.1f} s] Head rotation: {head_horizontal} {head_vertical}")

    if delay:
        time.sleep(delay)


def modify_head_rotation(horiz_delta: int, vert_delta: int, completion=True):
    set_head_rotation(head_horizontal + horiz_delta, head_vertical + vert_delta, completion)


def open_container(container: RobotContainer, side: Side):
    time.sleep(1)


def close_container(container: RobotContainer):
    time.sleep(1)


def get_camera_distance() -> int:
    return 0


