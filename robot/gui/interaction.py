
from robot.core.interaction import Interaction

from robot.gui.base.app import BaseApp


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
            self.send("message", message="Хм... Я уже видел вас!")
