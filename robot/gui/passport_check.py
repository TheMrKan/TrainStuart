import webview
import time
import base64
import logging
import cv2

from robot.hardware.cameras import CameraAccessor
import robot.config as config


logger: logging.Logger
window: webview.Window


def loop():
    global window
    image_element = window.dom.get_element("#cameraImage")
    while window is not None:
        _, png = cv2.imencode(".png", CameraAccessor.main_camera.image_bgr)
        image_b64 = base64.b64encode(png).decode("utf-8")
        image_element.attributes["src"] = f"data:image/png;base64, {image_b64}"


def on_window_closed():
    logger.debug("Window is closed")
    global window
    window = None


def start():
    global window
    global logger

    logger = logging.getLogger(__name__)

    window = webview.create_window("StuartGUI",
                                   url="./gui/assets/document_check.html",
                                   fullscreen=True)
    
    window.events.closed += on_window_closed
    
    webview.start(func=loop,
                  http_server=True,
                  debug=config.instance.passport_check.show_dev_tools)
    