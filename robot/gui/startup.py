from typing import Union

import robot.gui.base.navigation as gui_navigation
from robot.gui.base import gui_server
from robot.gui.base.app import BaseApp


class StartupApp(BaseApp):

    APP_NAME = "StartupApp"

    def run(self):
        super().run()
        gui_navigation.set_current_url("initializing")

    def set_status(self, message: str):
        self.send({"code": "status", "status": message})

    def shutdown(self):
        gui_navigation.set_current_url(None)
        super().shutdown()
