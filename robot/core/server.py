from threading import Thread
import time
import requests
from typing import Optional, TypedDict, List
import logging
from urllib.parse import urljoin
from dataclasses import dataclass
from datetime import datetime
from pymitter import EventEmitter
from utils.faces import FaceDescriptor
from utils.cv import Image, to_jpeg
import numpy

from robot.config import instance as config

__logger = logging.getLogger(__name__)

__is_polling: bool
__poller_thread: Thread


@dataclass
class ServerPollResponse:
    timestamp: datetime
    updated: dict


server_poll_response: Optional[ServerPollResponse] = None
events = EventEmitter()


def start_polling():
    global __poller_thread
    global __is_polling

    url = urljoin(config.server.host, "/robot/polling/")
    __is_polling = True
    __poller_thread = Thread(target=__poller,
                             args=(url, ),
                             name="robot.core.server.__poller",
                             daemon=True)
    __poller_thread.start()
    __logger.debug(f"Started polling {url}")


def stop_polling():
    global __is_polling

    __is_polling = False
    __logger.debug("Stopped polling")


def __poller(url: str):
    global __poller_thread

    while __is_polling:
        time.sleep(config.server.polling_interval)
        if not __is_polling:
            break

        try:
            __poll(url)
            __notify_updated()
        except Exception as e:
            __logger.exception("An error occured in robot.core.server.__poller.", exc_info=e)

    __poller_thread = None
    print("Poller terminated")


def __poll(url):
    global server_poll_response

    response = requests.get(url)
    response.raise_for_status()
    json: dict = response.json()

    server_poll_response = ServerPollResponse(datetime.now(), json)


def __notify_updated():
    if not server_poll_response:
        raise AssertionError("server_poll_response is None")
    for updated_name, updated_info in server_poll_response.updated.items():
        __logger.debug("Broadcasting update: %s (%s)", updated_name, updated_info)
        try:
            Thread(target=events.emit,
                   args=(f"updated_{updated_name}", ),
                   kwargs=updated_info,
                   name=f"Event 'updated_{updated_name}' from 'robot.core.server.__notify_updated'").start()
        except Exception as e:
            __logger.exception(f"Failed to notify updated: {updated_name}", exc_info=e)


class RequestedDelivery(TypedDict):
    id: str
    item_id: str
    seat: int
    priority: int


def __get_url(rel: str):
    return urljoin(config.server.host, rel)


def get_deliveries() -> List[RequestedDelivery]:
    response = requests.get(__get_url("delivery/list/"))
    response.raise_for_status()
    return response.json()


def take_delivery(delivery_id: str):
    response = requests.post(__get_url(f"delivery/{delivery_id}/status/?status=1"))
    response.raise_for_status()


class ServerPassenger(TypedDict):
    id: str
    name: str
    seat: int
    ticket: str
    passport: str
    face_descriptor: FaceDescriptor


def get_passengers() -> List[ServerPassenger]:
    response = requests.get(__get_url("robot/passengers/"))
    response.raise_for_status()
    json = response.json()
    for item in json:
        if item["face_descriptor"] is not None:
            item["face_descriptor"] = numpy.asarray(item["face_descriptor"], dtype=numpy.float32)

    __logger.debug("Received passengers: %s", json)
    return json


class DocumentProcessingError(Exception):
    pass


def process_document(image: Image) -> str:
    files = {"file": to_jpeg(image)}
    response = requests.post(__get_url(f"robot/document/"), files=files)
    response.raise_for_status()
    json: dict = response.json()
    if not json.get("success", False):
        raise DocumentProcessingError(json.get("error", ""))

    return json["passenger_id"]
