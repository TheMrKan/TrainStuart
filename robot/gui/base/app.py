import logging
import time
from typing import Dict, Callable, Union, Optional

import robot.gui.base.gui_server as gui_server
import robot.gui.base.navigation as gui_navigation


class BaseApp:
    NAME = "BaseApp"

    LISTENERS: Dict[str, Callable[[Union[dict, bytes]], None]] = {}
    HANDLERS: Dict[str, Callable[[dict, ], None]] = {}
    INITIAL_PAGE: Optional[str] = None

    _is_running: bool
    server_path: str
    logger: logging.Logger

    def __init__(self):
        self.logger = logging.getLogger(self.NAME)

        self.server_path = f"/app"
        self._is_running = False

    def run(self):
        self.subscribe()
        if self.INITIAL_PAGE:
            self.send_page(self.INITIAL_PAGE)
        self.is_running = True

    @property
    def is_running(self) -> bool:
        return self._is_running

    @is_running.setter
    def is_running(self, val: bool):
        self._is_running = val

    def send_page(self, name: Union[str, None]):
        gui_navigation.set_current_url(name, self.server_path)

    def subscribe(self):

        gui_server.on_message_received.on(self.server_path, self.on_message)
        for subpath, listener in self.LISTENERS.items():
            gui_server.on_message_received.on(self.server_path + "/" + subpath, listener)

    def __on_message(self, message: dict):
        code: str = message.get("code", None) or ""
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

    def unsubscribe(self):
        gui_server.on_message_received.off(self.server_path, self.on_message)
        for subpath, listener in self.LISTENERS.items():
            gui_server.on_message_received.off(self.server_path + "/" + subpath, listener)

    def shutdown(self):
        self.unsubscribe()
        #self.send_page(None)
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