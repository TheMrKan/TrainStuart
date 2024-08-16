from typing import Union

import robot.gui.base.navigation as gui_navigation
from robot.gui.base.app import BaseApp


class StartupApp(BaseApp):

    NAME = "Startup"
    INITIAL_PAGE = "initializing"

    def set_status(self, message: str):
        self.send("status", status=message)

