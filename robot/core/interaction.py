import time
from typing import Optional
import logging
from threading import Event

from robot.hardware.cameras import CameraAccessor
from robot.core.person import Person, find_by_face_descriptor, add_by_face
from robot.core.async_processor import AsyncProcessor
from utils.faces import ContinuousFaceDetector, FaceLocation, FaceDescriptor
from utils.cv import Image


logger = logging.getLogger(__name__)
__face_detector = ContinuousFaceDetector(lambda: CameraAccessor.main_camera.image_bgr, 200)


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


def check_face_state() -> ContinuousFaceDetector.State:
    return __face_detector.tick()


def reset():
    __face_detector.reset()
