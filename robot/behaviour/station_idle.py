import logging
import time
from typing import Union

from robot.gui.idle import IdleApp
from robot.gui.interaction import InteractionApp
from robot.core import route, interaction
from robot.hardware import robot_interface
from robot.behaviour.base import BaseBehaviour


class StationIdleBehaviour(BaseBehaviour):

    __app: Union[IdleApp, InteractionApp]

    def __init__(self):
        super().__init__()
        self.__app = IdleApp()

    def initialize(self):
        self.__app.run()

    def finalize(self):
        self.__app.shutdown()

    def behave(self):
        robot_interface.set_head_rotation(90, 20)

        self.logger.debug("Waiting for interaction...")
        trigger = interaction.wait_for_interaction_trigger()
        self.logger.debug("Interaction triggered")

        self.__app.shutdown()
        self.__app = InteractionApp()
        self.__app.run()

        try:
            inter = interaction.create_interaction(trigger)
            self.logger.debug("Interaction created")
            time.sleep(1)
            self.__app.set_interaction(inter)

            while True:
                state = interaction.update_face_state()
                if state == state.LOST or state == state.WAITING:
                    self.logger.debug("Face lost. Stopping interaction...")
                    break
                interaction.rotate_to_face()
                #time.sleep(0.1)

        finally:
            self.__app.shutdown()
            self.__app = IdleApp()
            self.__app.run()

            interaction.reset()
