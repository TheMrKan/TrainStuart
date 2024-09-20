import cv2
import cv2 as cv
import numpy as np
from typing import Tuple, Optional, List, Union, Any
import math
import timeit

COLOR_RANGES = [
    [(0, 140, 140), (10, 255, 255)],
    [(160, 160, 160), (180, 255, 255)]
]
MIN_CODE_RECT_AREA = 1500
CONTOURS_APPROX_EPSILON = 10
BIT_CHECK_NEIGHBOURS = 5
PADDING = 0.2

CODE_SIZE = 2

Point = Tuple[int, int]
Line = Tuple[Point, Point]

DEBUG = False


def _find_code_rect(hsv_image: cv.UMat,
                    min_area: float,
                    color_ranges: List[Tuple[Tuple[int, int, int], Tuple[int, int, int]]],
                    approx_epsilon: float) -> Optional[Tuple[Point, Point, Point, Point]]:
    mask = np.zeros(hsv_image.shape[:2], np.uint8)
    for crange in color_ranges:
        mask |= cv.inRange(hsv_image, crange[0], crange[1])

    if DEBUG:
        cv2.imshow("Mask", cv2.resize(mask, (int(1024 / 2), int(576 / 2))))
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

    if 0 in points.shape:
        print("Zero shape")
        return False

    mask = np.zeros(points.shape[:2], np.uint8)
    for crange in color_ranges:
        mask += cv.inRange(points, crange[0], crange[1])
    #cv2.imshow("Bit value mask", cv2.resize(mask, (int(1024 / 2), int(576 / 2))))
    #cv2.waitKey(1)

    count = np.count_nonzero(mask)
    total = mask.shape[0] * mask.shape[1]
    return count / total


def read_code(image_hsv: cv.UMat) -> Tuple[Optional[List[bool]], Optional[Tuple[Point, Point, Point, Point]], Optional[List[Point]]]:
    code_rect = _find_code_rect(image_hsv, MIN_CODE_RECT_AREA, COLOR_RANGES, CONTOURS_APPROX_EPSILON)
    if code_rect is None:
        return None, None, None

    bit_positions = _get_bit_positions(code_rect, CODE_SIZE, PADDING)

    values = []
    for pos in bit_positions:
        values.append(_get_bit_value(image_hsv, pos, BIT_CHECK_NEIGHBOURS, COLOR_RANGES) >= 0.5)

    return values, tuple(code_rect), bit_positions


def test():
    global DEBUG
    DEBUG = True

    print("Debug 0")
    cap = cv2.VideoCapture(0)
    print("Debug 1")
    '''cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    print("Debug 2")
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    print("Debug 3")
    cap.set(cv2.CAP_PROP_EXPOSURE, 25)
    cap.set(cv2.CAP_PROP_FPS, 60)'''
    print("Debug 4")

    cv2.namedWindow("Image")
    cv2.resizeWindow("Image", 500, 281)

    cv2.namedWindow("Mask")
    cv2.resizeWindow("Mask", 500, 281)

    cv2.namedWindow("Mask", cv2.WINDOW_NORMAL)
    cv2.imshow("Mask", np.zeros((576, 1024), np.uint8))

    r = COLOR_RANGES[0]
    cv.createTrackbar('H0', 'Mask', r[1][0], 255, lambda x: None)
    cv.createTrackbar('S0', 'Mask', r[0][1], 255, lambda x: None)
    cv.createTrackbar('V0', 'Mask', r[0][2], 255, lambda x: None)

    r = COLOR_RANGES[1]
    cv.createTrackbar('H1', 'Mask', r[0][0], 255, lambda x: None)
    cv.createTrackbar('S1', 'Mask', r[0][1], 255, lambda x: None)
    cv.createTrackbar('V1', 'Mask', r[0][2], 255, lambda x: None)

    print(timeit.timeit("_, img = cap.read()", number=90, globals={"cap": cap}))

    try:
        while True:
            _, img = cap.read()
            #img = cv2.resize(img, (int(1920 / 2), int(1080 / 2)))

            h, s, v = cv.getTrackbarPos('H0', 'Mask'), cv.getTrackbarPos('S0', 'Mask'), cv.getTrackbarPos('V0', 'Mask')
            r = COLOR_RANGES[0]
            r[1] = (h, r[1][1], r[1][2])
            r[0] = (r[0][0], s, v)

            h, s, v = cv.getTrackbarPos('H1', 'Mask'), cv.getTrackbarPos('S1', 'Mask'), cv.getTrackbarPos('V1', 'Mask')
            r = COLOR_RANGES[1]
            r[0] = h, s, v

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
                    color = (0, 255, 0) if values[i] >= 0.5 else (0, 0, 255)
                    cv.putText(img, str(round(values[i], 2)), (p[0], p[1] - 15), cv.FONT_HERSHEY_COMPLEX, 0.7, (255, 255, 0), 2)
                    cv.circle(img, p, 2, color, 3)
            else:
                pass

            cv2.imshow("Image", cv2.resize(img, (500, 281)))
            cv.waitKey(1)
    finally:
        cap.release()


if __name__ == "__main__":
    test()


