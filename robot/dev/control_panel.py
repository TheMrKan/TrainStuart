import time
from typing import Union
import cv2

from robot.gui.base import gui_server
from robot.hardware.cameras import CameraAccessor


__connected = False
__last_send = 0


def initialize():
    gui_server.on_connected.on("/control_panel", __on_connected)
    gui_server.on_message_received.on("/control_panel", __on_message_received)
    gui_server.on_disconnected.on("/control_panel", __on_disconnected)

    gui_server.on_connected.on("/control_panel/main_camera", __on_connected_main_camera)
    gui_server.on_disconnected.on("/control_panel/main_camera", __on_disconnected_main_camera)


def __on_connected():
    global __connected
    __connected = True


def __on_message_received(message: Union[dict, bytes]):
    pass


def __on_connected_main_camera():
    if __on_main_camera_image not in CameraAccessor.main_camera.on_image_grabbed:
        CameraAccessor.main_camera.on_image_grabbed.append(__on_main_camera_image)


def __on_main_camera_image():
    global __last_send
    t = time.time()
    if t - __last_send > 0.05:
        _, img = cv2.imencode(".png", CameraAccessor.main_camera.image_bgr)

        gui_server.send("/control_panel/main_camera", img.tobytes(), 1)
        __last_send = t


def __on_disconnected_main_camera():
    CameraAccessor.main_camera.on_image_grabbed.remove(__on_main_camera_image)


def __on_disconnected():
    global __connected
    __connected = False
