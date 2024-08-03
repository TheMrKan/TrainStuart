import time
import cv2
import math
import numpy
from typing import Optional
import os.path
from utils.cv import Image


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


def find_face(image: Image) -> Optional[tuple]:
    if not __face_cascade:
        raise ImportError("'haarcascade_frontalface_alt.xml' is not loaded. Call 'load_dependencies()' first")
    
    faces = __face_cascade.detectMultiScale(
                image,
                scaleFactor=1.4,
                minNeighbors=3,
                minSize=(300, 300)
        )
    return faces[0] if len(faces) > 0 else None


def compare_faces(face_a: FaceDescriptor, face_b: FaceDescriptor) -> float:
    return round(1 - numpy.linalg.norm(face_b - face_a), 3)
