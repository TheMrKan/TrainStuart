import robot.hardware.serial_interface as iserial
import enum


class Side(enum.Enum):
    LEFT = 1
    RIGHT = 2


class RobotContainer(enum.Enum):
    BIG = 0
    SMALL_0 = 1
    SMALL_1 = 2
    TABLET_0 = 3
    TABLET_1 = 4


def initialize():
    iserial.setup()


def move_to(x: int, y: int):
    raise NotImplementedError


def rotate_to(angle: int):
    raise NotImplementedError


def set_actual_pos(x: int, y: int):
    raise NotImplementedError


def set_head_rotation(horiz: int, vert: int):
    raise NotImplementedError


def open_container(container: RobotContainer, side: Side):
    raise NotImplementedError


def close_container(container: RobotContainer):
    raise NotImplementedError


def get_camera_distance() -> int:
    raise NotImplementedError


