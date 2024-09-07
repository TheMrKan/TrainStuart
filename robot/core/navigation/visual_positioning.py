import time

import cv2
import numpy as np
from typing import Tuple

from robot.core.navigation import reader, chart
from robot.hardware.cameras import CameraAccessor

DISTANCE = 90
FOCAL = 900


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


def watcher():
    camera = CameraAccessor.main_camera
    last_check = 0
    try:
        while True:
            t = time.time()
            if t - last_check < 0.01:
                time.sleep(0.02)
                yield None
            last_check = t

            data, points, bit_positions = reader.read_code(camera.image_hsv)

            if None not in (data, points, bit_positions):

                num = int("".join((str(int(i))) for i in reversed(data)), 2)
                center = (round(sum([p[0] for p in points]) / len(points)),
                          round(sum([p[1] for p in points]) / len(points)))

                rx, _, ry = camera_position((camera.image_hsv.shape[1], camera.image_hsv.shape[0]), center, DISTANCE, FOCAL)

                try:
                    ax, ay = chart.get_absolute_position(f"marker_left_{num}", (rx, ry))
                except KeyError:
                    #print(f"Unknown point {num}")
                    continue

                yield ax, ay
    except StopIteration:
        pass