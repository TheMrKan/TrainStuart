import scanner
import cv2
import numpy as np
from typing import Tuple

DISTANCE = 140
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


cap = cv2.VideoCapture(0)
chart = np.full((500, 500, 3), 255, np.uint8)
while True:
    _, img = cap.read()

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    data, points, bit_positions = scanner.read_code(hsv)
    if None not in (data, points, bit_positions):
        for p in points:
            cv2.circle(img, p, 4, (255, 255, 0), 3)
        num = int("".join((str(int(i))) for i in data), 2)
        center = (round(sum([p[0] for p in points]) / len(points)),
                  round(sum([p[1] for p in points]) / len(points)))
        cv2.circle(img, center, 6, (0, 255, 255), 4)

        rx, ry, rz = camera_position((img.shape[1], img.shape[0]), center, DISTANCE, FOCAL)
        print(rx, ry, rz)

        chart = np.full((500, 500, 3), 255, np.uint8)
        cx, cy = round(img.shape[1] / 2), round(img.shape[0] / 2)

        cv2.line(chart, (cx - 40, 0), (cx - 40, img.shape[0]), (0, 255, 0), 5)
        cv2.line(chart, (cx + 40, 0), (cx + 40, img.shape[0]), (0, 255, 0), 5)

        cv2.circle(chart, (cx, cy), 5, (0, 0, 255), 5)
        vx, vy = cx - rx, cy - rz
        cv2.circle(chart, (vx, vy), 5, (255, 255, 0), 5)

    cv2.imshow("Image", cv2.resize(img, (500, 288)))
    cv2.imshow("Chart", chart)
    cv2.waitKey(1)
