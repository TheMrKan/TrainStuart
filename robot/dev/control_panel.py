import time
from typing import Union, Optional, List, Dict
import logging
from utils.cv import Image
from threading import Event

from robot.gui.base import gui_server
from robot.hardware.cameras import CameraAccessor, CameraHandler
from robot.core.navigation import chart
from robot.hardware import robot_interface

__logger = logging.getLogger(__name__)

PATH = "/control_panel"


class Stream:
    id: str
    path: str
    name: str
    __is_active: bool

    image: Optional[Image]
    logger: logging.Logger

    def __init__(self, id: str, name: str):
        self.id = id
        self.path = get_stream_path(id)
        self.name = name
        self.logger = logging.getLogger("Stream." + self.id)
        self.__is_active = False

        self.image = None
        gui_server.on_connected.on(self.path, self.__on_connected)
        gui_server.on_disconnected.on(self.path, self.__on_disconnected)

    def send_image(self, image):
        self.image = image
        if not self.is_active:
            return
        gui_server.send_image(self.path, self.image, 30)

    @property
    def is_active(self) -> bool:
        return self.__is_active

    @is_active.setter
    def is_active(self, value: bool):
        self.__is_active = value
        if value and self.image is not None:
            gui_server.send_image(self.path, self.image, 30)

    def __on_connected(self):
        _set_active_stream(self)

    def __on_disconnected(self):
        if self.is_active:
            _set_active_stream(None)

    def destroy(self):
        gui_server.on_connected.off(self.path, self.__on_connected)
        gui_server.on_disconnected.off(self.path, self.__on_disconnected)


class CameraStream(Stream):
    camera_handler: CameraHandler
    __last_send: float

    def __init__(self, id: str, name: str, camera_handler: CameraHandler):
        self.camera_handler = camera_handler
        self.__last_send = 0
        super().__init__(id, name)

    @Stream.is_active.setter
    def is_active(self, value):
        self.logger.debug(f"Set camera stream active: {value}")
        if value and self.__on_camera_image not in self.camera_handler.on_image_grabbed:
            self.camera_handler.on_image_grabbed.append(self.__on_camera_image)
        elif not value and self.__on_camera_image in self.camera_handler.on_image_grabbed:
            self.camera_handler.on_image_grabbed.remove(self.__on_camera_image)
        Stream.is_active.fset(self, value)

    def __on_camera_image(self):
        t = time.time()
        if t - self.__last_send > 0.2:
            self.send_image(self.camera_handler.image_bgr)
            self.__last_send = t


__streams: Dict[str, Stream] = {}
__active_stream: Optional[Stream] = None
__last_send = 0


def initialize():
    gui_server.on_connected.on(PATH, __on_connected)
    gui_server.on_message_received.on(PATH, __on_message_received)
    gui_server.on_disconnected.on(PATH, __on_disconnected)
    robot_interface.on_event.on("pos_updated", __on_robot_pos_updated)

    __create_stream("main_camera", "Камера", CameraAccessor.main_camera)
    __create_stream("documents_camera", "Документы", CameraAccessor.documents_camera)

    if is_connected():
        __send_chart()


def is_connected():
    return gui_server.is_ws_connected(PATH)


def get_stream(stream_id: str, name: Optional[str] = None) -> Stream:
    if stream_id not in __streams.keys():
        return __create_stream(stream_id, name)
    return __streams[stream_id]


def get_stream_path(stream_id: str) -> str:
    return PATH + "/" + stream_id


def update_robot_pos(x: int, y: int):
    gui_server.send(PATH, {"code": "set_robot_pos", "x": x, "y": y})


def send_robot_path(points: List[chart.Vector2]):
    gui_server.send(PATH, {"code": "robot_path", "points": points})


passport_response_event = Event()
passport_response_data: Optional[str] = None


def request_read_passport() -> Optional[str]:
    global passport_response_data

    passport_response_data = None
    passport_response_event.clear()
    gui_server.send(PATH, {"code": "passport_request"})

    passport_response_event.wait(30)
    passport_response_event.clear()
    return passport_response_data


def _set_active_stream(stream: Optional[Stream]):
    global __active_stream
    if __active_stream:
        __active_stream.is_active = False

    __active_stream = stream
    if stream:
        stream.is_active = True


def __on_connected():
    for stream in __streams.values():
        __send_stream(stream.id, stream.name)

    __send_chart()


def __on_message_received(message: Union[dict, bytes]):
    global passport_response_data

    if message["code"] == "passport_response":
        passport_response_event.set()
        passport_response_data = message.get("passport_number", None)


def __create_stream(stream_id: str, name: Optional[str] = None, camera_handler: Optional[CameraHandler] = None) -> Stream:
    stream = Stream(stream_id, name) if camera_handler is None else CameraStream(stream_id, name, camera_handler)
    __streams[stream_id] = stream
    __logger.debug("Created stream %s", stream_id)
    if is_connected():
        __send_stream(stream_id, name)
    return stream


def __send_stream(stream_id: str, name: Optional[str] = None):
    name = name or stream_id
    url = gui_server.get_absolute_ws_url(get_stream_path(stream_id))
    gui_server.send(PATH, {"code": "stream", "id": stream_id, "url": url, "name": name})
    __logger.debug("Sent stream: %s (%s)", name, url)


def __send_chart():
    logging.debug("Sending chart...")
    zones = []
    for zone in chart.zones.values():
        zones.append({
            "id": zone.id,
            "p0": zone.p0,
            "p1": zone.p1
        })

    points = []
    for point in chart.points.values():
        points.append({
            "id": point.id,
            "x": point.x,
            "y": point.y,
        })

    gui_server.send(PATH, {
        "code": "chart",
        "zones": zones,
        "points": points
    })


def __on_robot_pos_updated(x: int, y: int):
    update_robot_pos(x, y)


def __on_disconnected():
    global __connected
    __connected = False
