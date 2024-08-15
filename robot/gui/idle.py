from typing import Optional
import time

from robot.gui.base.app import BaseApp
from robot.config import instance as config
import robot.core.route as route


class IdleApp(BaseApp):

    NAME = "Idle"

    INITIAL_PAGE = "rest"



