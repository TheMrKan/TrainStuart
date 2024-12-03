from threading import Thread
import time
import requests
from typing import Optional
import logging
from urllib.parse import urljoin
from dataclasses import dataclass
from datetime import datetime
from pymitter import EventEmitter

from robot.config import instance as config

__logger = logging.Logger(__name__)

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

    url = urljoin(config.server.host, "/robot/polling")

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


def __poll(url):
    global server_poll_response

    '''response = requests.get(url)
    response.raise_for_status()
    json: dict = response.json()'''
    json = {"updated": {}}

    server_poll_response = ServerPollResponse(datetime.now(), json.get("updated", {}))


def __notify_updated():
    if not server_poll_response:
        raise AssertionError("server_poll_response is None")

    for updated_name, updated_info in server_poll_response.updated.items():
        try:
            Thread(target=events.emit,
                   args=(f"updated_{updated_name}", ),
                   kwargs=updated_info,
                   name=f"Event 'updated_{updated_name}' from 'robot.core.server.__notify_updated'").start()
        except Exception as e:
            __logger.exception(f"Failed to notify updated: {updated_name}", exc_info=e)