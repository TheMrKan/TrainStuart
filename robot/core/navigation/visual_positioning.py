import time
import math
import cv2
import numpy as np
from typing import Tuple, Optional

from robot.core.navigation import reader, chart
from robot.hardware.cameras import CameraAccessor
from robot.dev import control_panel
#from utils.faces import ContinuousDetector

FOCAL = 900

SPEED = 258.5 / 12

MIN_WALL_DISTANCE = 100
MAX_WALL_DISTANCE = 145


def camera_position(image_size: Tuple[int, int], marker: Tuple[int, int],
                    distance: float, focal: float) -> Tuple[int, int, int]:
    w, h = image_size
    x_i, y_i = marker

    x_center, y_center = w / 2, h / 2

    delta_x, delta_y = x_i - x_center, y_i - y_center

    x_m = (delta_x * distance) / focal
    y_m = (delta_y * distance) / focal
    z_m = distance

    x_camera = -x_m
    y_camera = -y_m
    z_camera = -z_m

    return round(x_camera), round(y_camera), round(z_camera)


def head_distance_to_wall_distance(head_distance: float, head_rotation_y: float) -> int:
    # 10 - расстояние от камеры до центра робота. Работает только для поворота головы на -90
    # 6 - относителньно постоянная ошибка из-за несоответствия угла вертикального поворота
    return round(head_distance * math.cos(math.radians(head_rotation_y)) + 10 + 6)


def wall_distance_to_head_distance(wall_distance: float, head_rotation_y: float) -> int:
    # 10 - расстояние от камеры до центра робота. Работает только для поворота головы на -90
    # 6 - относителньно постоянная ошибка из-за несоответствия угла вертикального поворота
    return round((wall_distance - 10 - 6) / math.cos(math.radians(head_rotation_y)))


WALL_Y = 100

def distance_to_wall_to_y(distance_to_wall: int) -> int:
    return WALL_Y - distance_to_wall


def y_to_distance_to_wall(y) -> int:
    return WALL_Y - y


def is_marker_visible() -> bool:
    data, points, bit_positions = reader.read_code(CameraAccessor.main_camera.image_hsv)
    return None not in (data, points, bit_positions)


def try_get_position(head_rotation_x: int, head_distance: int, distance_to_wall: int) \
        -> Tuple[Optional[str], Optional[chart.Vector2]]:
    data, points, bit_positions = reader.read_code(CameraAccessor.main_camera.image_hsv)

    side = ""
    num = 0
    ax, ay = 0, 0
    try:
        if None in (data, points, bit_positions):
            return None, None

        num = int("".join((str(int(i))) for i in reversed(data)), 2)
        center = (round(sum([p[0] for p in points]) / len(points)),
                  round(sum([p[1] for p in points]) / len(points)))

        rx, _, _ = camera_position((CameraAccessor.main_camera.image_hsv.shape[1],
                                    CameraAccessor.main_camera.image_hsv.shape[0]),
                                    center, head_distance, FOCAL)

        side = "left" if head_rotation_x <= 0 else "right"

        ax, ay = chart.get_absolute_position(f"marker_{side}_{num}", (rx, -distance_to_wall))
        # print(f"Distance: {distance}, X: {ax}, Y: {ay}")
        return f"marker_{side}_{num}", (ax, ay)
    except KeyError:
        print(f"Unknown point {f'marker_{side}_{num}'}")
        return None, None
    finally:
        stream = control_panel.get_stream("visual_positioning", "Позиционирование")
        if stream.is_active:
            img = CameraAccessor.main_camera.image_bgr.copy()
            cv2.putText(img, f"{ax} {ay}", (30, 30), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 1)
            cv2.putText(img, f"{num}", (30, 70), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 1)
            if None not in (data, points, bit_positions):
                for p in points:
                    cv2.rectangle(img, (p[0] - 5, p[1] - 5), (p[0] + 5, p[1] + 5), (255, 255, 0), 2)

                for i, p in enumerate(bit_positions):
                    color = (0, 255, 0) if data[i] else (0, 0, 255)
                    #cv2.putText(img, str(i), (p[0], p[1] - 15), cv2.FONT_HERSHEY_COMPLEX, 0.9, (60, 80, 255), 2)
                    cv2.circle(img, p, 2, color, 3)
            stream.send_image(img)


