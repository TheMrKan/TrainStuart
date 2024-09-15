import time
from typing import Optional

from robot.behaviour.base import BaseBehaviour
from robot.gui.documents_check import DocumentsCheckApp
from robot.hardware import robot_interface


class DocumentsCheckBehaviour(BaseBehaviour):

    def behave(self):
        robot_interface.move_to(0, 0)
        robot_interface.set_head_rotation(90, 20)

        app = DocumentsCheckApp()
        try:
            app.run()

            if app.success:
                robot_interface.move_to(88, 0)
                time.sleep(10)
                robot_interface.move_to(0, 0)
        finally:
            app.shutdown()


