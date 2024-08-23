import math
import time
from typing import Optional, Iterable
import logging
from threading import Event

from robot.hardware.cameras import CameraAccessor
from robot.core.person import Person, find_by_face_descriptor, add_by_face
from robot.core.async_processor import AsyncProcessor
from utils.faces import ContinuousFaceDetector, FaceLocation, FaceDescriptor
from utils.cv import Image
from robot.hardware import robot_interface
import cv2


logger = logging.getLogger(__name__)
__face_detector = ContinuousFaceDetector(lambda: CameraAccessor.main_camera.image_bgr, 400)


class InteractionTrigger:
    pass


class FaceInteractionTrigger(InteractionTrigger):

    camera_image: Image
    face_location: FaceLocation

    def __init__(self, camera_image: Image, face_location: FaceLocation):
        self.camera_image = camera_image
        self.face_location = face_location


class Interaction:

    trigger: InteractionTrigger
    person: Person

    def __init__(self, trigger: InteractionTrigger, person: Person):
        self.trigger = trigger
        self.person = person


def wait_for_interaction_trigger() -> InteractionTrigger:
    __face_detector.reset()
    while True:
        state = __face_detector.tick()
        if state == __face_detector.State.FOUND or state == __face_detector.State.TRACKING:
            return FaceInteractionTrigger(__face_detector.image, __face_detector.face)
        elif state == __face_detector.State.WAITING:
            time.sleep(0.25)
        else:
            time.sleep(0.1)


def create_interaction(trigger: InteractionTrigger) -> Interaction:
    if isinstance(trigger, FaceInteractionTrigger):
        return __create_interaction_face(trigger)

    raise ValueError(f"Unknown trigger type {type(trigger).__name__}")


def __create_interaction_face(trigger: FaceInteractionTrigger) -> Interaction:
    event = Event()
    descriptor: Optional[FaceDescriptor] = None
    exception: Optional[Exception] = None

    def success_callback(_descriptor: Optional[FaceDescriptor]):
        nonlocal descriptor
        descriptor = _descriptor
        event.set()

    def error_callback(_exception: Exception):
        nonlocal exception
        exception = _exception
        event.set()

    logger.debug("Getting descriptor of trigger face...")
    AsyncProcessor.get_face_descriptor_async(trigger.camera_image, success_callback, error_callback, trigger.face_location)
    event.wait()

    if descriptor is None:
        raise exception or Exception("Failed to get face descriptor")

    logger.debug("Got descriptor of trigger face")

    person = find_by_face_descriptor(descriptor)
    new_person = False
    if not person:
        new_person = True
        person = add_by_face(descriptor)
        logger.debug("Person was not found so a new one was added")

    logger.info(f"Creating interaction with person {person}")
    inter = Interaction(trigger, person)
    inter.new_person = new_person
    return inter


def update_face_state() -> ContinuousFaceDetector.State:
    return __face_detector.tick()


def __get_closest(val: int, values: Iterable[int]) -> int:
    return min(values, key=lambda x: abs(x-val))


DISTANCES = {
    496: 90,
    694: 50,
    810: 35,
}

DST_TO_ANGLE_MULTS = {
    90: 0.03,
    50: 0.018,
    35: 0.00675
}


def __get_distance_to_face(face_size: int) -> int:
    key = __get_closest(face_size, DISTANCES.keys())
    return DISTANCES[key]


def rotate_to_face():
    logger.debug("Rotating to face...")
    if __face_detector.face is None:
        logger.debug("Face is None. Returning...")
        return

    face_center = (int(round(__face_detector.face[0] + __face_detector.face[2] / 2)), int(round(__face_detector.face[1] + __face_detector.face[3] / 2)))
    camera_center = int(__face_detector.image.shape[1] / 2), int(__face_detector.image.shape[0] / 2)

    delta = camera_center[0] - face_center[0]
    delta_rel = abs(delta) / (__face_detector.image.shape[1] / 2)
    logger.debug(f"Delta: {delta}; Rel: {delta_rel:.2f};")

    head_angle_delta = 0
    distance = 0

    ALLOWED_DELTA_REL = 0.2
    OUT_DELTA_REL = 0.8
    if delta_rel <= ALLOWED_DELTA_REL:
        logger.debug("Delta is in allowed range. Returning...")
    elif delta_rel <= OUT_DELTA_REL:
        distance = __get_distance_to_face(int((__face_detector.face[2] + __face_detector.face[3]) / 2))
        head_angle_delta = int(round(DST_TO_ANGLE_MULTS[distance] * delta))
        logger.debug(f"Head rotation delta: {head_angle_delta}")
        logger.debug(f"Face size: {__face_detector.face[2], __face_detector.face[3]}")

        robot_interface.modify_head_rotation(head_angle_delta, 0)
    else:
        logger.debug(f"Face is too far from center. Returning...")

    image = __face_detector.image.copy()

    image = cv2.line(image,
                     (int(camera_center[0] - camera_center[0] * ALLOWED_DELTA_REL), 0),
                     (int(camera_center[0] - camera_center[0] * ALLOWED_DELTA_REL), __face_detector.image.shape[0]),
                     (150, 150, 150),
                     5)
    image = cv2.line(image,
                     (int(camera_center[0] + camera_center[0] * ALLOWED_DELTA_REL), 0),
                     (int(camera_center[0] + camera_center[0] * ALLOWED_DELTA_REL), __face_detector.image.shape[0]),
                     (150, 150, 150),
                     5)

    image = cv2.line(image,
                     (int(camera_center[0] - camera_center[0] * OUT_DELTA_REL), 0),
                     (int(camera_center[0] - camera_center[0] * OUT_DELTA_REL), __face_detector.image.shape[0]),
                     (90, 90, 90),
                     5)
    image = cv2.line(image,
                     (int(camera_center[0] + camera_center[0] * OUT_DELTA_REL), 0),
                     (int(camera_center[0] + camera_center[0] * OUT_DELTA_REL), __face_detector.image.shape[0]),
                     (90, 90, 90),
                     5)

    image = cv2.circle(image, camera_center, 5, (255, 0, 0), 4)
    image = cv2.circle(image, face_center, 5, (0, 0, 255), 4)

    image = cv2.resize(image, (600, 372))

    image = cv2.putText(image, f"Delta: {head_angle_delta}", (5, 25),
                        cv2.FONT_HERSHEY_COMPLEX, 1, (20, 220, 20), 1)
    image = cv2.putText(image, f"Face: {__face_detector.face[2], __face_detector.face[3]}", (5, 50),
                        cv2.FONT_HERSHEY_COMPLEX, 1, (20, 220, 20), 1)
    image = cv2.putText(image, f"Distance: {distance}", (5, 75),
                        cv2.FONT_HERSHEY_COMPLEX, 1, (20, 220, 20), 1)

    #cv2.imshow("Head rotation", image)
    #cv2.waitKey(1)

def reset():
    __face_detector.reset()
