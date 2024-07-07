import time
import cv2
import math
import numpy
import face_recognition as recog
from typing import TypeAlias


FaceDescriptor: TypeAlias = numpy.ndarray


class Recognizer:

    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier("../utils/haarcascade_frontalface_alt.xml")

    def get_face_encoding(self, image: numpy.ndarray, bounds: list = None) -> FaceDescriptor:
        encodings = recog.face_encodings(image, known_face_locations=bounds, num_jitters=5, model="large")

        # any(encodings) выдает ошибку. encodings.any() не всегда работает, т. к. иногда возвращается tuple
        if len(encodings) == 0:
            return None
        return encodings[0]

    def get_face_encoding_from_file(self, file_path: str):
        image = cv2.imread(file_path)
        return self.get_face_encoding(image)

    def find_face(self, image: numpy.ndarray) -> tuple[int, int, int, int] | None:

        faces = self.face_cascade.detectMultiScale(
                image,
                scaleFactor=1.4,
                minNeighbors=3,
                minSize=(300, 300)
        )

        # any(faces) выдает ошибку. faces.any() не всегда работает, т. к. иногда возвращается tuple
        if len(faces) == 0:
            return None

        return faces[0]

    def get_matching_encoding_index(self, target_encoding: FaceDescriptor, encodings: list):
        if not any(encodings):
            return -1

        compared = list(recog.face_distance(encodings, target_encoding))
        m = min(compared)
        if m > 0.5:
            return -1
        try:
            return compared.index(m)
        except ValueError as ex:
            return -1
        
    def compare_faces(self, face_a: FaceDescriptor, face_b: FaceDescriptor) -> float:
       return recog.face_distance([face_b], face_a)[0]
    





