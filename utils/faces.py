import time
import cv2
import math
import numpy
from typing import Optional, Callable, Tuple
import os.path
from utils.cv import Image
from datetime import datetime
from enum import Enum


FaceDescriptor = numpy.ndarray


__recognition = None
__face_cascade = None


def load_dependencies(resources_dir: str):
    global __recognition
    global __face_cascade

    import face_recognition as recog
    __recognition = recog

    __face_cascade = cv2.CascadeClassifier(os.path.join(resources_dir, "haarcascade_frontalface_alt.xml"))


def get_face_descriptor(image: Image, face_location: Optional[tuple] = None) -> Optional[FaceDescriptor]:
    if not __recognition:
        raise ImportError("'face_recognition' is not imported. Call 'load_dependencies()' first")
    
    descriptors = __recognition.face_encodings(image,
                                             [face_location] if face_location is not None else None,
                                             num_jitters=3,
                                             model="large")
    return descriptors[0] if len(descriptors) > 0 else None


def find_face(image: Image, min_size: int = 300) -> Optional[tuple]:
    """
    Возвращает самое большое найденное лицо на изображении
    :param image: BGR изображение
    :param min_size: Минимальный размер стороны квадрата найденного лица в пикселях
    :return: (x, y, w, h) или None, если ни одно лицо не найдено
    """
    if not __face_cascade:
        raise ImportError("'haarcascade_frontalface_alt.xml' is not loaded. Call 'load_dependencies()' first")
    
    faces = __face_cascade.detectMultiScale(
                image,
                scaleFactor=1.4,
                minNeighbors=3,
                minSize=(min_size, min_size)
        )
    return sorted(faces, key=lambda loc: loc[2] * loc[3], reverse=True)[0] if len(faces) > 0 else None


def compare_faces(face_a: FaceDescriptor, face_b: FaceDescriptor) -> float:
    return round(1 - numpy.linalg.norm(face_b - face_a), 3)


class ContinuousFaceDetector:

    class State(Enum):
        WAITING = 0
        FOUND_GUESS = 1
        FOUND_GUESS_WAITING = 2
        FOUND_GUESS_FAILED = 3
        FOUND = 4
        TRACKING = 5
        LOST_GUESS = 6
        LOST_GUESS_WAITING = 7
        LOST = 8

    source: Callable[[], Image]
    face: Optional[Tuple[int, int, int, int]]

    __face_detected: Optional[datetime]
    __face_lost: Optional[datetime]
    __is_tracking: bool

    def __init__(self, source: Callable[[], Image], min_size: int = 300):
        self.source = source
        self.min_size = min_size
        self.__face_detected = None
        self.__face_lost = None
        self.__is_tracking = False

    def reset(self):
        self.__face_detected = None
        self.__face_lost = None
        self.__is_tracking = False

    def tick(self) -> State:
        image = self.source()
        self.face = find_face(image, self.min_size)

        now = datetime.now()
        if self.face is None:
            if self.__face_detected and not self.__is_tracking:
                self.__face_detected = None
                return self.State.FOUND_GUESS_FAILED
            if self.__face_lost:
                if (now - self.__face_lost).total_seconds() > 1:
                    self.reset()
                    return self.State.LOST
                else:
                    return self.State.LOST_GUESS_WAITING
            else:
                if self.__face_detected:
                    self.__face_lost = now
                    return self.State.LOST_GUESS
                return self.State.WAITING

        self.__face_lost = None

        if not self.__face_detected:
            self.__face_detected = now
            return self.State.FOUND_GUESS
        else:
            if not self.__is_tracking:
                if (now - self.__face_detected).total_seconds() > 1:
                    self.__is_tracking = True
                    return self.State.FOUND
                else:
                    return self.State.FOUND_GUESS_WAITING
            else:
                return self.State.TRACKING
