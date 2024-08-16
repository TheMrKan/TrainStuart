import logging
import time
from typing import Union

from robot.gui.idle import IdleApp
from robot.gui.interaction import InteractionApp
from robot.core import route, interaction


class StationIdleBehaviour:

    __logger: logging.Logger
    __app: Union[IdleApp, InteractionApp]

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

        self.__app.shutdown()
        self.__app = InteractionApp()
        self.__app.run()

        try:
            inter = interaction.create_interaction(trigger)
            self.__logger.debug("Interaction created")
            time.sleep(1)
            self.__app.set_interaction(inter)

            while True:
                state = interaction.check_face_state()
                if state == state.LOST or state == state.WAITING:
                    self.__logger.debug("Face lost. Stopping interaction...")
                    break
                time.sleep(0.25)

        finally:
            self.__app.shutdown()
            self.__app = IdleApp()
            self.__app.run()

            interaction.reset()