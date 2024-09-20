
from robot.core.interaction import Interaction
from robot.gui.base.app import BaseApp
from robot.gui.base import navigation as gui_navigation
from robot.gui import external
import time


class InteractionApp(BaseApp):
    NAME = "Interaction"
    INITIAL_PAGE = "interaction"

    interaction: Interaction

    def __init__(self):
        super().__init__()

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
        if action_name in ("food", "souvenirs"):
            url = external.get_server_url(external.SHOP)
        elif action_name == "taxi":
            url = external.TAXI
        elif action_name == "hotels":
            url = external.HOTELS
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

