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
    iserial.send_command("M", x, y, completion=True)


def rotate_to(angle: int):
    iserial.send_command("R", angle, completion=True)


def set_actual_pos(x: int, y: int):
    iserial.send_command("P", x, y, completion=True)


def set_head_rotation(horiz: int, vert: int):
    iserial.send_command("H", horiz, vert, completion=True)


def open_container(container: RobotContainer, side: Side):
    iserial.send_command("C", container.value, side.value, completion=True)


def close_container(container: RobotContainer):
    iserial.send_command("C", container.value, 0, completion=True)


def get_camera_distance() -> int:
    return iserial.send_request("Hd")[0]


