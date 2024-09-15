import robot.hardware.serial_interface as iserial
import enum
import logging

logger = logging.getLogger(__name__)

WHEELS_SPEED_X = 215 / 12


class Side(enum.Enum):
    LEFT = 1
    RIGHT = 2


class RobotContainer(enum.Enum):
    BIG = 0
    SMALL_0 = 1
    SMALL_1 = 2
    TABLET_0 = 3
    TABLET_1 = 4


head_horizontal = 0
head_vertical = 0


def initialize():
    iserial.setup()
    #iserial.await_completion()


def stop():
    iserial.send_command("S")


def move_to(x: int, y: int):
    logger.debug(f"Send move to {x} {y}")
    iserial.send_command("M", x, y, completion=True)
    logger.debug(f"Completed move to {x} {y}")


def rotate_to(angle: int):
    iserial.send_command("R", angle, completion=True)


def set_actual_pos(x: int, y: int):
    iserial.send_command("P", x, y, completion=False)


def set_head_rotation(horiz: int, vert: int, completion=True):
    global head_horizontal
    global head_vertical

    iserial.send_command("H", horiz, vert, completion=completion)


def modify_head_rotation(horiz_delta: int, vert_delta: int, completion=True):
    set_head_rotation(head_horizontal + horiz_delta, head_vertical + vert_delta, completion)


def open_container(container: RobotContainer, side: Side):
    iserial.send_command("C", container.value, side.value, completion=True)


def close_container(container: RobotContainer):
    iserial.send_command("C", container.value, 0, completion=True)


def get_camera_distance() -> int:
    return iserial.send_request("Hd")[0]


