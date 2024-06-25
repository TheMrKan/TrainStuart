import webview
import time
import base64
import logging

import cv2

logger: logging.Logger
window: webview.Window

def loop():
    global window
    image_element = window.dom.get_element("#cameraImage")

    camera = cv2.VideoCapture(0)

    while window is not None:
        _, img_bgr = camera.read()
        _, png = cv2.imencode(".png", img_bgr)
        image_b64 = base64.b64encode(png).decode("utf-8")
        image_element.attributes["src"] = f"data:image/png;base64, {image_b64}"
        time.sleep(0.03)

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
                  debug=True)
    