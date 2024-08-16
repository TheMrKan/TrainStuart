import time
import cv2
import math
import numpy
from typing import Optional, Callable, Tuple, List
import os.path
from utils.cv import Image
from datetime import datetime
from enum import Enum


FaceDescriptor = numpy.ndarray
FaceLocation = Tuple[int, int, int, int]
"""
(X, Y, Width, Height)
"""


__recognition = None
__face_cascade = None


def load_dependencies(resources_dir: str):
    global __recognition
    global __face_cascade

    import face_recognition as recog
    __recognition = recog

    __face_cascade = cv2.CascadeClassifier(os.path.join(resources_dir, "haarcascade_frontalface_alt.xml"))


def get_face_descriptor(image: Image, face_location: Optional[FaceLocation] = None) -> Optional[FaceDescriptor]:
    if not __recognition:
        raise ImportError("'face_recognition' is not imported. Call 'load_dependencies()' first")

    # top, right, bottom, left
    face_locations_css = [(face_location[1], face_location[0] + face_location[2], face_location[1] + face_location[3], face_location[0]), ] if face_location is not None else None
    
    descriptors = __recognition.face_encodings(image,
                                               face_locations_css,
                                               num_jitters=3,
                                               model="large")
    return descriptors[0] if len(descriptors) > 0 else None


def find_face(image: Image, min_size: int = 300) -> Optional[FaceLocation]:
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


def get_nearest_descriptor_index(descriptor: FaceDescriptor, known_descriptors: List[FaceDescriptor], threshold: float = 0.5) -> int:
    """
    Находит в списке дескриптор с наибольшим процентом сходства. Если наибольший процент ниже порога, то возвращает -1
    """
    if not __recognition:
        raise ImportError("'face_recognition' is not imported. Call 'load_dependencies()' first")

    if len(known_descriptors) == 0:
        return -1

    compared = list(__recognition.face_distance(known_descriptors, descriptor))
    m = min(compared)
    if m > (1 - threshold):    # дистанция обратна проценту сходства
        return -1
    try:
        return compared.index(m)
    except ValueError:
        return -1


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
    face: Optional[FaceLocation]
    image: Optional[Image]

    __face_detected: Optional[datetime]
    __face_lost: Optional[datetime]
    __is_tracking: bool

    def __init__(self, source: Callable[[], Image], min_size: int = 500):
        self.source = source
        self.min_size = min_size
        self.face = None
        self.image = None
        self.__face_detected = None
        self.__face_lost = None
        self.__is_tracking = False

    def reset(self):
        self.__face_detected = None
        self.__face_lost = None
        self.__is_tracking = False

    def tick(self) -> State:
        self.image = self.source()
        self.face = find_face(self.image, self.min_size)

        #cv2.imshow("Main Camera", cv2.resize(self.image, (600, 372)))
        #cv2.waitKey(1)

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
