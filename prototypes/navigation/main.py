import scanner
import cv2
import numpy as np
from typing import Tuple
import chart

DISTANCE = 129
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
last_ax, last_ay = 0, 0

chart.load_map()

while True:
    _, img = cap.read()

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    chart_image = np.full((500, 500, 3), 255, np.uint8)
    cx, cy = round(img.shape[1] / 2), round(img.shape[0] / 2)

    cv2.line(chart_image, (cx - 140, 0), (cx - 140, img.shape[0]), (0, 255, 0), 5)
    cv2.line(chart_image, (cx + 140, 0), (cx + 140, img.shape[0]), (0, 255, 0), 5)

    chart_points = chart.get_points()
    for point in chart_points:
        cv2.circle(chart_image, (cx + point.x, cy + point.y), 5, (0, 0, 255), 5)

    data, points, bit_positions = scanner.read_code(hsv)

    if None not in (data, points, bit_positions):
        for p in points:
            cv2.circle(img, p, 4, (255, 255, 0), 3)

        num = int("".join((str(int(i))) for i in reversed(data)), 2)
        center = (round(sum([p[0] for p in points]) / len(points)),
                  round(sum([p[1] for p in points]) / len(points)))
        cv2.circle(img, center, 6, (0, 255, 255), 4)

        rx, _, ry = camera_position((img.shape[1], img.shape[0]), center, DISTANCE, FOCAL)

        try:
            ax, ay = chart.get_absolute_position(f"R{num}", rx, ry)
            last_ax, last_ay = ax, ay
        except KeyError:
            print(f"Unknown point {num}")
            ax, ay = last_ax, last_ay

        print(f"Point: {num}\tX: {ax}\tY: {ay}")

        vx, vy = cx - ax, cy - ay
        cv2.circle(chart_image, (vx, vy), 5, (255, 255, 0), 5)

    cv2.imshow("Image", cv2.resize(img, (500, 288)))
    cv2.imshow("Chart", chart_image)
    cv2.waitKey(1)
