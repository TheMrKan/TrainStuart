from threading import Event
from typing import Union, Optional
import logging

import robot.gui.base.gui_server as gui_server
from utils.cancelations import await_event, CancellationToken
from robot.config import instance as config


current_url: Optional[str] = None

shutdown_cancellation = CancellationToken()

logger = logging.getLogger(__name__)


def initialize():
    global current_url
    current_url = gui_server.get_absolute_http_page_url(config.gui.loading_page)
    gui_server.on_connected.on("/navigation", on_navigation_connected)


def on_navigation_connected():
    send_current_url()


def send_current_url(target: Optional[str] = None):
    message = {"code": "navigation", "url": current_url}
    if target:
        gui_server.send(target, message)
    gui_server.send("/navigation", message)
    logger.info(f"Current url: '{current_url}'")


def shutdown():
    shutdown_cancellation.cancel()
    gui_server.on_connected.off("/navigation", on_navigation_connected)


def set_current_url(url: Optional[str], target: Optional[str] = None):
    global current_url
    if not url:
        url = config.gui.loading_page

    current_url = gui_server.get_absolute_http_page_url(url)
    send_current_url(target)

