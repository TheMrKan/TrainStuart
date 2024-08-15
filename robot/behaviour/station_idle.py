import logging
import time

from robot.gui.idle import IdleApp
from robot.core import route, interaction


class StationIdleBehaviour:

    __logger: logging.Logger
    __app: IdleApp

    def __init__(self):
        self.__logger = logging.getLogger('StationIdleBehaviour')
        self.__app = IdleApp()

    def run(self):
        try:
            self.__initialize()

            while True:
                try:
                    self.__behave()
                except Exception as e:
                    self.__logger.exception("Unhandled exception in __behave", exc_info=e)

        finally:
            self.__finalize()

    def __initialize(self):
        self.__app.run()

    def __finalize(self):
        self.__app.shutdown()

    def __behave(self):
        self.__logger.debug("Waiting for interaction...")
        trigger = interaction.wait_for_interaction_trigger()
        self.__logger.debug("Interaction triggered")
        inter = interaction.create_interaction(trigger)
        self.__logger.debug("Interaction created")
