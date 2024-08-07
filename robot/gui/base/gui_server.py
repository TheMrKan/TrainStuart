import json
import websockets
from websockets.legacy.server import WebSocketServerProtocol
import asyncio
from asyncio.exceptions import TimeoutError
import threading
from bottle import Bottle, run, static_file, ServerAdapter
import logging
from typing import Tuple, Optional, Any, Union
from pymitter import EventEmitter

logger = logging.getLogger(__name__)


class StoppableServer(ServerAdapter):
    def run(self, handler):
        from wsgiref.simple_server import make_server, WSGIRequestHandler

        if self.quiet:
            class QuietHandler(WSGIRequestHandler):
                def log_request(*args, **kw): pass
            handler_class = QuietHandler
        else:
            handler_class = WSGIRequestHandler

        self.server = make_server(self.host, self.port, handler, handler_class=handler_class)
        self.server.serve_forever()

    def stop(self):
        self.server.shutdown()


bottle_app = Bottle()
http_thread: threading.Thread
http_server: StoppableServer

STATIC_DIR = "gui/assets/static"
TEMPLATES_DIR = "gui/assets"

websocket_stop_event = threading.Event()
websocket_thread: threading.Thread
websocket_loop: asyncio.BaseEventLoop

outgoing_messages = {}

on_connected = EventEmitter()
on_message_received = EventEmitter()
on_disconnected = EventEmitter()


@bottle_app.route('/static/<filename:path>')
def http_static(filename):
    return static_file(filename, root=STATIC_DIR)


@bottle_app.route('<page:path>')
def http_page(page):
    return static_file(page + ".html", root=TEMPLATES_DIR)


async def websocket_server(websocket: WebSocketServerProtocol, path: str):
    await emit_connected(path)

    while not websocket_stop_event.is_set():
        try:
            try:
                incoming_message = await asyncio.wait_for(websocket.recv(), 0.3)
                await handle_incoming_message(path, incoming_message)
            except TimeoutError:
                pass

            outgoing_message: Union[dict, bytes, None] = outgoing_messages.get(path, None)
            if outgoing_message:
                await send_outgoing_message(websocket, outgoing_message)
                del outgoing_messages[path]
        except websockets.exceptions.WebSocketException:
            break
        except Exception as e:
            logger.exception("An error occured in websocket_server", exc_info=e)

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
    await websocket.send(message)


def run_websocket():
    global websocket_loop
    asyncio.set_event_loop(asyncio.new_event_loop())
    server = websockets.serve(websocket_server, "localhost", 8001)
    websocket_loop = asyncio.get_event_loop()
    websocket_loop.run_until_complete(server)

    logger.debug("Websocket server is running")
    websocket_loop.run_forever()
    logger.debug("Websocket server is stopped")


def run_http():
    global http_server
    http_server = StoppableServer(host="localhost", port=8000, quite=True)
    logger.debug("HTTP server is running")
    run(bottle_app, server=http_server)
    logger.debug("HTTP server is stopped")


def get_absolute_ws_url(rel_path: str) -> str:
    return "ws://localhost:8001/" + rel_path


def get_absolute_http_page_url(rel_path: str) -> str:
    return "http://localhost:8000/" + rel_path


def get_absolute_http_static_url(rel_path: str) -> str:
    return "http://localhost:8000/static/" + rel_path


def start():
    global websocket_thread
    global http_thread

    logger.debug("Starting GUI server...")

    websocket_thread = threading.Thread(target=run_websocket, daemon=True, name="robot.gui.gui_server.websocket")
    websocket_thread.start()

    http_thread = threading.Thread(target=run_http, daemon=True, name="robot.gui.gui_server.http")
    http_thread.start()

    logger.info("GUI server is running")


def send(path: str, message: Union[dict]):
    outgoing_messages[path] = message


def stop():
    logger.debug("Stopping GUI server...")
    websocket_stop_event.set()
    websocket_loop.call_soon_threadsafe(websocket_loop.stop)
    http_server.stop()

    websocket_thread.join()
    http_thread.join()
    logger.info("GUI server is stopped")

