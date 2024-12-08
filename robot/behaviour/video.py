import time

from robot.behaviour.base import BaseBehaviour
from robot.hardware.audio import AudioOutput
from robot.hardware import robot_interface
from robot.gui.idle import IdleApp

class VideoBehaviour(BaseBehaviour):

    def behave(self):
        app = IdleApp()
        app.run()

        robot_interface.set_head_rotation(90, 0)
        time.sleep(1)
        AudioOutput.play_async("video.wav")

        while True:
            time.sleep(1)