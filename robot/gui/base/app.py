import logging
import time
from typing import Dict, Callable, Union, Optional
from threading import Event

import robot.gui.base.gui_server as gui_server
import robot.gui.base.navigation as gui_navigation
from utils.cancelations import await_event


class BaseApp:
    NAME = "BaseApp"

    LISTENERS: Dict[str, Callable[[Union[dict, bytes]], None]] = {}
    HANDLERS: Dict[str, Callable[[dict, ], None]] = {}
    INITIAL_PAGE: Optional[str] = None

    _is_running: bool
    _wait_code: Optional[str]
    _wait_event: Optional[Event]
    _wait_connected: Optional[Event]
    auth: Optional[str]
    last_message: Optional[dict]
    server_path: str
    logger: logging.Logger

    def __init__(self, auth: Optional[str] = "SAME"):
        self.logger = logging.getLogger(self.NAME)

        self.server_path = f"/app"
        self.auth = auth
        self._is_running = False

        self._wait_code = None
        self._wait_event = None
        self._wait_connected = None

    def run(self):
        self.subscribe()
        if self.INITIAL_PAGE:
            self.send_page(self.INITIAL_PAGE, self.auth)
        self.is_running = True

    @property
    def is_running(self) -> bool:
        return self._is_running

    @is_running.setter
    def is_running(self, val: bool):
        self._is_running = val

    def send_page(self, name: Union[str, None], auth: Optional[str] = "SAME"):
        if auth != "SAME":
            if auth is None:
                auth = ""
            name += f"?auth={auth}"
        gui_navigation.set_current_url(name, self.server_path)

    def subscribe(self):

        gui_server.on_message_received.on(self.server_path, self.__on_message)
        gui_server.on_connected.on(self.server_path, self.on_connected)
        for subpath, listener in self.LISTENERS.items():
            gui_server.on_message_received.on(self.server_path + "/" + subpath, listener)

    def on_connected(self):
        if self._wait_connected:
            self._wait_connected.set()

        gui_navigation.send_current_url(self.server_path)

    def __on_message(self, message: dict):
        code: str = message.get("code", None) or ""
        self.last_message = message

        if (self._wait_code == "" or self._wait_code == code) \
                and self._wait_event is not None:
            self._wait_event.set()

        handler = self.HANDLERS.get(code, None)
        if handler:
            try:
                handler(message)
            except Exception as e:
                self.logger.exception(f"Unhandled exception in the '{code}' code handler", exc_info=e)
        self.on_message(message)

    def on_message(self, message: dict):
        pass

    def send(self, code: str, subpath: str = "", **kwargs):
        self.send_raw({"code": code, **kwargs}, subpath)

    def send_raw(self, message: Union[dict, bytes], subpath: str = ""):
        path = self.server_path
        if subpath:
            path += "/" + subpath

        gui_server.send(path, message)

    def wait_message(self, code: str = "", timeout: Optional[float] = None) -> dict:
        self.wait_message_no_block(code)

        is_timeout = not await_event(self._wait_event, timeout)
        if timeout and is_timeout:
            raise TimeoutError
        self._wait_event = None
        self._wait_code = None
        return self.last_message

    def wait_message_no_block(self, code: str) -> Event:
        self._wait_code = code
        self._wait_event = Event()
        return self._wait_event

    def wait_connection(self):
        self._wait_connected = Event()
        self._wait_connected.wait()
        self._wait_connected = None

    def unsubscribe(self):
        gui_server.on_message_received.off(self.server_path, self.__on_message)
        gui_server.on_connected.off(self.server_path, self.on_connected)
        for subpath, listener in self.LISTENERS.items():
            gui_server.on_message_received.off(self.server_path + "/" + subpath, listener)

    def auth_as(self, *args):
        pass

    def shutdown(self):
        self.unsubscribe()
        self.send_page(None)
        self.is_running = False


class BaseLoopApp(BaseApp):

    def run(self):
        super().run()
        while self.is_running:
            try:
                self.loop()
            except Exception as e:
                self.logger.exception(f"An error occured in {self.NAME} app loop", exc_info=e)
            time.sleep(0.05)
        self.shutdown()

    def loop(self):
        pass