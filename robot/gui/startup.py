from typing import Union

import robot.gui.base.navigation as gui_navigation
from robot.gui.base import gui_server


class StartupApp:

    APP_NAME = "StartupApp"

    def __init__(self):
        pass

    def run(self):
        gui_navigation.set_current_url("initializing")

    def set_status(self, message: str):
        gui_server.send(f"/apps/{self.APP_NAME}", {"code": "status", "status": message})

    def shutdown(self):
        gui_navigation.set_current_url(None)
