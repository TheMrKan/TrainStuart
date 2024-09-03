import cv2
import cv2 as cv
import numpy as np
from typing import Tuple, Optional, List
import math

COLOR_RANGES = [
    ((0, 100, 30), (10, 255, 255)),
    ((170, 100, 30), (180, 255, 255))
]
MIN_CODE_RECT_AREA = 1500
CONTOURS_APPROX_EPSILON = 10
BIT_CHECK_NEIGHBOURS = 5
PADDING = 0.2

CODE_SIZE = 2

Point = Tuple[int, int]
Line = Tuple[Point, Point]


def _find_code_rect(hsv_image: cv.UMat,
                    min_area: float,
                    color_ranges: List[Tuple[Tuple[int, int, int], Tuple[int, int, int]]],
                    approx_epsilon: float) -> Optional[Tuple[Point, Point, Point, Point]]:
    mask = np.zeros(hsv_image.shape[:2], np.uint8)
    for crange in color_ranges:
        print(crange)
        mask |= cv.inRange(hsv_image, crange[0], crange[1])
    cv2.imshow("Mask", mask)
    cv2.waitKey(1)
    contours, _ = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

    biggest_area = 0
    biggest = None
    for cnt in contours:
        area = cv.contourArea(cnt)
        if area > biggest_area and area > min_area:
            approx: List[List[np.ndarray]] = cv.approxPolyDP(cnt, approx_epsilon, True)
            if len(approx) == 4:
                biggest = [(c[0][0], c[0][1]) for c in approx]
                biggest_area = area

    return biggest


def _put_points_between(p1: Point, p2: Point, count: int, padding: float) -> List[Point]:
    points = []

    # сдвигаем точки ближе друг к другу в соответствие с padding
    delta = p2[0] - p1[0], p2[1] - p1[1]
    p1 = p1[0] + delta[0] * padding, p1[1] + delta[1] * padding
    p2 = p2[0] - delta[0] * padding, p2[1] - delta[1] * padding

    delta = p2[0] - p1[0], p2[1] - p1[1]
    part_x = delta[0] / (count * 2)
    part_y = delta[1] / (count * 2)
    for i in range(0, count):
        point_x = int(p1[0] + part_x + part_x * i * 2)
        point_y = int(p1[1] + part_y + part_y * i * 2)
        points.append((point_x, point_y))
    return points


def _get_vertical_factor(p1: Point, p2: Point) -> float:
    x_delta = abs(p2[0] - p1[0])
    if x_delta == 0:
        return math.inf

    y_delta = abs(p2[1] - p1[1])
    return y_delta / x_delta


def _get_two_vertical_lines(*lines: Line) -> Tuple[Line, Line]:
    srtd = sorted(lines, key=lambda t: _get_vertical_factor(t[0], t[1]), reverse=True)
    return srtd[0], srtd[1]


def _get_bit_positions(code_rect: Tuple[Point, Point, Point, Point], code_size: int, padding: float) -> List[Point]:
    line_1, line_2 = _get_two_vertical_lines(
        (code_rect[0], code_rect[1]),
        (code_rect[1], code_rect[2]),
        (code_rect[2], code_rect[3]),
        (code_rect[3], code_rect[0]))

    edge_points_1 = sorted(_put_points_between(line_1[0], line_1[1], code_size, padding), key=lambda p: p[1])
    edge_points_2 = sorted(_put_points_between(line_2[0], line_2[1], code_size, padding), key=lambda p: p[1])

    positions = []

    for i in range(code_size):
        positions += sorted(_put_points_between(edge_points_1[i], edge_points_2[i], code_size, padding), key=lambda p: p[0])

    return positions


def _get_bit_value(image_hsv: cv.UMat, position: Point, neighbours: int, color_ranges: List[Tuple[Tuple[int, int, int], Tuple[int, int, int]]]) -> bool:
    min_x, max_x = position[0]-neighbours, position[0]+neighbours+1
    min_y, max_y = position[1]-neighbours, position[1]+neighbours+1
    points = image_hsv[min_y:max_y, min_x:max_x]

    average_color = np.mean(points, axis=0)[2]
    for crange in color_ranges:
        _is_in_range = all(current >= minimum for current, minimum in zip(average_color, crange[0]))
        _is_in_range &= all(current <= maximum for current, maximum in zip(average_color, crange[1]))
        if _is_in_range:
            return True
    return False


def read_code(image_hsv: cv.UMat) -> Tuple[Optional[List[bool]], Optional[Tuple[Point, Point, Point, Point]], Optional[List[Point]]]:
    code_rect = _find_code_rect(image_hsv, MIN_CODE_RECT_AREA, COLOR_RANGES, CONTOURS_APPROX_EPSILON)
    if code_rect is None:
        return None, None, None

    bit_positions = _get_bit_positions(code_rect, CODE_SIZE, PADDING)

    values = []
    for pos in bit_positions:
        values.append(_get_bit_value(image_hsv, pos, BIT_CHECK_NEIGHBOURS, COLOR_RANGES))

    return values, tuple(code_rect), bit_positions


def read_qr_code(bgr_image: cv.UMat) -> Optional[str]:

    qcd = cv2.QRCodeDetector()
    retval, decoded_info, points, straight_qrcode = qcd.detectAndDecodeMulti(bgr_image)
    for c in decoded_info:
        if c:
            return c


def test():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    cap.set(cv2.CAP_PROP_EXPOSURE, 10)
    while True:
        _, img = cap.read()
        img = cv2.resize(img, (int(1920 / 3), int(1080 / 3)))

        cv2.imshow("Image", img)
        hsv_img = cv.cvtColor(img, cv.COLOR_BGR2HSV)

        code_rect = _find_code_rect(hsv_img, MIN_CODE_RECT_AREA, COLOR_RANGES, CONTOURS_APPROX_EPSILON)

        if code_rect is not None:

            bit_positions = _get_bit_positions(code_rect, CODE_SIZE, PADDING)

            values = []
            for pos in bit_positions:
                values.append(_get_bit_value(hsv_img, pos, BIT_CHECK_NEIGHBOURS, COLOR_RANGES))

            for p in code_rect:
                cv.rectangle(img, (p[0] - 5, p[1] - 5), (p[0] + 5, p[1] + 5), (255, 255, 0), 2)

            for i, p in enumerate(bit_positions):
                color = (0, 255, 0) if values[i] else (0, 0, 255)
                cv.putText(img, str(i), (p[0], p[1] - 15), cv.FONT_HERSHEY_COMPLEX, 0.9, (60, 80, 255), 2)
                cv.circle(img, p, 2, color, 3)
                cv.imshow(f"Test", img)
        else:
            print("Code rect not found")

        cv.waitKey(1)


if __name__ == "__main__":
    test()


