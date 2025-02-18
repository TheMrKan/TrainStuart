
from robot.core.interaction import Interaction
from robot.gui.base.app import BaseApp
from robot.gui.base import navigation as gui_navigation
from robot.gui import external
from robot.hardware.audio import AudioOutput
from robot.hardware import robot_interface
from robot.hardware.robot_interface import RobotContainer, Side
from robot.core import passengers
import time
from typing import Optional


class InteractionApp(BaseApp):
    NAME = "Interaction"
    INITIAL_PAGE = "interaction"

    interaction: Interaction
    contin: bool
    passenger: Optional[passengers.Person]

    def __init__(self, contin=False, passenger: Optional[passengers.Person] = None):
        super().__init__(auth=(passenger.ticket if passenger else None))
        self.contin = contin
        self.passenger = passenger

    def run(self):
        super().run()
        audios = ["other_help"] if self.contin else ["help"]
        if self.passenger:
            name_audio = passengers.get_name_audio(self.passenger.name)
            if name_audio:
                audios.insert(0, name_audio)

            self.send("greetings", name=self.passenger.name)

        AudioOutput.play_async(*audios)

    def set_interaction(self, interaction: Interaction):
        self.interaction = interaction
        if self.interaction.person.name:
            self.send("greetings", name=self.interaction.person.name)
        if not self.interaction.new_person:
            self.logger.debug("Send not a new person")
            self.send("message", message="Ваш поезд на 3 платформе")
            self.send("greetings", name="Михаил")

    def on_message(self, message: dict):
        if message["code"] == "action":
            if message["name"] == "none":
                self.shutdown()
                return
            self.handle_action(message["name"])

    def handle_action(self, action_name: str):
        self.logger.info("Handing action %s", action_name)
        if action_name in ("food", "souvenirs"):
            url = external.get_server_url(external.SHOP)
        elif action_name == "taxi":
            url = external.TAXI
        elif action_name == "hotels":
            url = external.HOTELS
        elif action_name == "tablet":
            self.give_tablet()
            return
        else:
            self.logger.warning("Unknown action '%s'", action_name)
            return

        self.logger.debug("Redirecting to external URL: %s", url)
        gui_navigation.set_current_url(url, self.server_path)
        time.sleep(0.5)
        self.send_page(self.INITIAL_PAGE)
        self.logger.debug("Waiting...")
        self.wait_connection()
        self.logger.debug("Returned")

    def give_tablet(self):
        self.logger.info("User requested a tablet")
        AudioOutput.play_async("tablet_take.wav")
        robot_interface.open_container(RobotContainer.TABLET_FRONT, Side.LEFT)    # Side инвертирован из-за ошибки в прошивке
        time.sleep(4)
        robot_interface.close_container(RobotContainer.TABLET_FRONT)
        AudioOutput.play_async("other_help.wav")

    def shutdown(self):
        if not self.is_running:
            return

        AudioOutput.play_async("goodbye.wav")
        super().shutdown()

