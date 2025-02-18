import robot.hardware.serial_interface as iserial
import enum
import logging
from pymitter import EventEmitter
from typing import Tuple

logger = logging.getLogger(__name__)

WHEELS_SPEED_X = 215 / 12
WHEELS_SPEED_Y_RIGHT = 44 / 5
WHEELS_SPEED_Y_LEFT = 82 / 5


class Side(enum.Enum):
    LEFT = 1
    RIGHT = 2


class RobotContainer(enum.Enum):
    BIG = 0
    SMALL_BACK = 1
    SMALL_FRONT = 2
    TABLET_BACK = 3
    TABLET_FRONT = 4


head_horizontal = 0
head_vertical = 0
current_x, current_y = 0, 0
on_command: EventEmitter
on_event = EventEmitter()


def initialize():
    iserial.setup()

    global on_command
    on_command = iserial.on_command

    global current_x, current_y
    current_x, current_y = get_current_position()


def move_to(x: int, y: int, completion: bool = True):
    global current_x, current_y
    logger.debug(f"Send move to {x} {y}")
    iserial.send_command("M", x, y, completion=True, completion_timeout=30)
    current_x = x
    current_y = y
    on_event.emit("pos_updated", current_x, current_y)
    logger.debug(f"Completed move to {x} {y}")


def move_to_line(side: Side):
    side_converted = 1 if side == Side.RIGHT else -1
    logger.debug(f"Send move to line {side} ({side_converted})")
    iserial.send_command("Ln", side_converted, completion=True, completion_timeout=30)
    logger.debug(f"Completed move to line {side} ({side_converted})")


def set_speed_correction(correction: int):
    """
    При движении прямо: >0 - доворот направо, <0 - налево
    При движении назад инвертировать
    Модуль: 100 - очень сильно доворачивает
    """
    iserial.send_command("Sc", int(correction))


def rotate_to(angle: int):
    iserial.send_command("R", angle, completion=True)


def set_actual_pos(x: int, y: int):
    global current_x, current_y
    current_x, current_y = x, y
    on_event.emit("pos_updated", current_x, current_y)
    iserial.send_command("P", x, y, completion=False)


def set_head_rotation(horiz: int, vert: int, completion=True):
    global head_horizontal
    global head_vertical
    logger.debug(f"Head rotation: {horiz} {vert}")

    iserial.send_command("H", horiz, vert, completion=completion, completion_timeout=15)
    head_horizontal = horiz
    head_vertical = vert


class RotationDirection(enum.Enum):
    LEFT = -1
    STOP = 0
    RIGHT = 1


current_head_rotation_direction = RotationDirection.STOP


def head_horizontal_run(direction: RotationDirection):
    """
    Запускает бесконечное вращение головы. Обязательно должна быть вызвана функция остановки.
    :param direction: >1 - вправо, <1 - влево, 0 - остановка
    """
    global current_head_rotation_direction

    if direction == current_head_rotation_direction:
        return

    current_head_rotation_direction = direction
    iserial.send_command("Hi", direction.value)


def modify_head_rotation(horiz_delta: int, vert_delta: int, completion=True):
    set_head_rotation(head_horizontal + horiz_delta, head_vertical + vert_delta, completion)


def open_container(container: RobotContainer, side: Side, completion=True):
    iserial.send_command("C", container.value, side.value, completion=completion, completion_timeout=5)


def close_container(container: RobotContainer, completion=True):
    iserial.send_command("C", container.value, 0, completion=completion, completion_timeout=5)


def get_camera_distance() -> int:
    """
    :return: 0, если не удалось получить значение, иначе дистанцию в сантиметрах
    """
    response = iserial.send_request("Hd", timeout=1)
    if not response:
        return 0
    dst = round(response[0] / 10)
    if 10 <= dst <= 200:
        return dst
    return 0


def get_current_position() -> Tuple[int, int]:
    global current_x, current_y
    current_x, current_y = iserial.send_request("P", timeout=1)[:2]
    on_event.emit("pos_updated", current_x, current_y)
    return current_x, current_y


