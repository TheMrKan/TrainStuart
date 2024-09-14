import json
import websockets
from websockets.legacy.server import WebSocketServerProtocol
import asyncio
from asyncio.exceptions import TimeoutError
import threading
from bottle import Bottle, run, static_file, ServerAdapter
import logging
from typing import Tuple, Optional, Any, Union, List, Dict, Set
from pymitter import EventEmitter
from utils.cv import Image
import cv2
import urllib.parse
import multiprocessing

logger = logging.getLogger(__name__)

http_stop_event: multiprocessing.Event
http_process: multiprocessing.Process

websocket_stop_event = threading.Event()
websocket_thread: threading.Thread
websocket_loop: asyncio.BaseEventLoop

outgoing_messages: Dict[str, List[Union[dict, bytes]]] = {}
ws_connected: Set[str] = set()

on_connected = EventEmitter()
on_message_received = EventEmitter()
on_disconnected = EventEmitter()


async def websocket_server(websocket: WebSocketServerProtocol, path: str):
    ws_connected.add(path)
    await emit_connected(path)

    while not websocket_stop_event.is_set():
        try:
            try:
                incoming_message = await asyncio.wait_for(websocket.recv(), 0.3)
                await handle_incoming_message(path, incoming_message)
            except TimeoutError:
                pass

            path_outgoing_messages: Optional[List[Union[dict, bytes]]] = outgoing_messages.get(path, None)
            if path_outgoing_messages:
                for msg in path_outgoing_messages:
                    #logger.debug("Sending outgoing message to %s", path)
                    await send_outgoing_message(websocket, msg)
                path_outgoing_messages.clear()
        except websockets.exceptions.WebSocketException:
            break
        except Exception as e:
            logger.exception("An error occurred in websocket_server", exc_info=e)

    ws_connected.remove(path)
    await emit_disconnected(path)


async def emit_connected(path: str):
    threading.Thread(target=on_connected.emit,
                     args=(path, )).start()


async def emit_disconnected(path: str):
    threading.Thread(target=on_disconnected.emit,
                     args=(path,)).start()


async def handle_incoming_message(path: str, message: Union[str, bytes]):
    if isinstance(message, str):
        message = json.loads(message)
    threading.Thread(target=on_message_received.emit,
                     args=(path, message)).start()


async def send_outgoing_message(websocket: WebSocketServerProtocol, message: Union[dict, bytes]):
    if isinstance(message, dict):
        message = json.dumps(message)
    try:
        await asyncio.wait_for(websocket.send(message), 1)
    except TimeoutError:
        logger.debug("Outgoing message timeout")


def run_websocket():
    global websocket_loop
    asyncio.set_event_loop(asyncio.new_event_loop())
    server = websockets.serve(websocket_server, "robot", 8001)
    websocket_loop = asyncio.get_event_loop()
    websocket_loop.run_until_complete(server)

    logger.debug("Websocket server is running")
    websocket_loop.run_forever()
    logger.debug("Websocket server is stopped")


def run_http():
    global http_process
    global http_stop_event

    http_stop_event = multiprocessing.Event()
    import robot.gui.base.http as http
    http_process = multiprocessing.Process(target=http.run,
                                           args=(http_stop_event, ),
                                           name="robot.gui.base.gui_server.http",
                                           daemon=True)
    http_process.start()


def get_absolute_ws_url(rel_path: str) -> str:
    return urllib.parse.urljoin("ws://robot:8001/", rel_path)


def get_absolute_http_page_url(rel_path: str) -> str:
    return urllib.parse.urljoin("http://robot:8000/", rel_path)


def get_absolute_http_static_url(rel_path: str) -> str:
    return urllib.parse.urljoin("http://robot:8000/static/", rel_path)


def start():
    global websocket_thread
    global http_thread

    logger.debug("Starting GUI server...")

    websocket_thread = threading.Thread(target=run_websocket, daemon=True, name="robot.gui.gui_server.websocket")
    websocket_thread.start()

    run_http()

    logger.info("GUI server is running")


def send(path: str, message: Union[dict, bytes], queue_limit: int = 0):
    outgoing_messages.setdefault(path, [])
    queue = outgoing_messages[path]

    l = len(queue)
    if queue_limit > 0:
        if l >= queue_limit:
            queue.clear()
    queue.append(message)


def send_image(path: str, image: Image):
    _, img = cv2.imencode(".png", image)
    send(path, img.tobytes(), 1)


def is_ws_connected(path: str):
    return path in ws_connected


def stop():
    logger.debug("Stopping GUI server...")
    websocket_stop_event.set()
    websocket_loop.call_soon_threadsafe(websocket_loop.stop)
    http_stop_event.set()

    websocket_thread.join()
    logger.info("GUI server is stopped")

