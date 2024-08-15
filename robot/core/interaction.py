from datetime import datetime
import time
from typing import Optional
import logging

from robot.hardware.cameras import CameraAccessor
from utils.faces import ContinuousFaceDetector


logger = logging.getLogger()
__face_detector = ContinuousFaceDetector(lambda: CameraAccessor.main_camera.image_bgr, 400)


def wait_for_interaction():
    __face_detector.reset()
    while True:
        state = __face_detector.tick()
        if state == __face_detector.State.FOUND or state == __face_detector.State.TRACKING:
            return
        elif state == __face_detector.State.WAITING:
            time.sleep(0.5)
        else:
            time.sleep(0.1)


def check_state():
    state = __face_detector.tick()


def track_face():
    while True:
        state = __face_detector.tick()
        if state == __face_detector.State.LOST:
            logger.debug("Lost interaction face")
            return

        if state == __face_detector.State.TRACKING:
            face_center = (int(round(__face_detector.face[0] + __face_detector.face[2] / 2)), int(round(__face_detector.face[1] + __face_detector.face[3] / 2)))


def reset():
    __face_detector.reset()
