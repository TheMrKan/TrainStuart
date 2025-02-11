import cv2
import numpy
from typing import Union

Image = Union[numpy.ndarray, cv2.Mat, cv2.UMat]


def to_jpeg(image: Image) -> Image:
    return cv2.imencode('.jpg', image)[1]


def to_png(image: Image) -> Image:
    return cv2.imencode('.png', image)[1]