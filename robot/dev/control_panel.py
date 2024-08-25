import time
from typing import Union, Optional
import logging
from utils.cv import Image

from robot.gui.base import gui_server
from robot.hardware.cameras import CameraAccessor

__logger = logging.getLogger(__name__)

__connected = False
__last_send = 0

PATH = "/control_panel"
__streams = []


def initialize():
    gui_server.on_connected.on(PATH, __on_connected)
    gui_server.on_message_received.on(PATH, __on_message_received)
    gui_server.on_disconnected.on(PATH, __on_disconnected)

    gui_server.on_connected.on(PATH + "/main_camera", __on_connected_main_camera)
    gui_server.on_disconnected.on(PATH + "/main_camera", __on_disconnected_main_camera)


def send_image(stream_id: str, image: Image):
    if not __connected:
        return
    if stream_id not in __streams:
        __send_stream(stream_id, stream_id)
        __streams.append(stream_id)

    gui_server.send_image(PATH + "/" + stream_id, image)


def __on_connected():
    global __connected
    __connected = True

    __send_stream("main_camera", "Основная камера")


def __on_message_received(message: Union[dict, bytes]):
    pass


def __on_connected_main_camera():
    if __on_main_camera_image not in CameraAccessor.main_camera.on_image_grabbed:
        CameraAccessor.main_camera.on_image_grabbed.append(__on_main_camera_image)


def __on_main_camera_image():
    global __last_send
    t = time.time()
    if t - __last_send > 0.05:
        gui_server.send_image(PATH + "/main_camera", CameraAccessor.main_camera.image_bgr)
        __last_send = t


def __send_stream(stream_id: str, name: Optional[str] = None):
    name = name or stream_id
    url = gui_server.get_absolute_ws_url(PATH + "/" + stream_id)
    gui_server.send(PATH, {"code": "stream", "id": stream_id, "url": url, "name": name})
    __logger.debug("Sent stream: %s (%s)", name, url)


def __on_disconnected_main_camera():
    CameraAccessor.main_camera.on_image_grabbed.remove(__on_main_camera_image)


def __on_disconnected():
    global __connected
    __connected = False
