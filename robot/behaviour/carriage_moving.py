import logging
import time

from robot.behaviour.base import BaseBehaviour
from robot.core.navigation import passenger_zone, chart
from robot.hardware import robot_interface
from robot.hardware.audio import AudioOutput
from robot.hardware.robot_interface import RobotContainer, Side
from robot.gui.interaction import InteractionApp
from robot.gui.idle import IdleApp


class CarriageMovingBehaviour(BaseBehaviour):

    def __init__(self):
        super().__init__()

    def initialize(self):
        pass

    def behave(self):
        app = IdleApp()
        app.run()

        robot_interface.on_command.on("Tch", self.on_touch_received)

        vending = chart.get_point_position("vending")
        self.logger.debug("Going to vending")
        time.sleep(1)
        # robot_interface.set_actual_pos(vending[0], 60)

        robot_interface.set_actual_pos(vending[0], 0)
        robot_interface.set_head_rotation(-90, 0)

        # robot_interface.move_to(vending[0], 0)

        robot_interface.move_to(0, 0)

        passenger_zone.start()

        passenger_zone.go_to_seat(4)
        robot_interface.set_head_rotation(-70, -10, completion=False)
        app.shutdown()
        app = InteractionApp()

        app.run()
        while app.is_running:
            time.sleep(1)
        app = IdleApp()
        app.run()

        passenger_zone.go_to_seat(2)

        robot_interface.set_head_rotation(-70, -10, completion=False)
        app.shutdown()
        app = InteractionApp()

        app.run()
        while app.is_running:
            time.sleep(1)
        app = IdleApp()
        app.run()

        passenger_zone.go_to_base()

        robot_interface.set_head_rotation(-90, 0)
        robot_interface.move_to(vending[0], 0)

        robot_interface.open_container(RobotContainer.SMALL_FRONT, Side.LEFT)
        robot_interface.open_container(RobotContainer.BIG, Side.LEFT)

        time.sleep(4)

        robot_interface.close_container(RobotContainer.SMALL_FRONT)
        robot_interface.close_container(RobotContainer.BIG)

        robot_interface.move_to(0, 0)
        passenger_zone.start()
        passenger_zone.go_to_seat(2)

        AudioOutput.play_async("order_completed_eat.wav")
        robot_interface.set_head_rotation(-70, -10, completion=False)
        robot_interface.open_container(RobotContainer.SMALL_FRONT, Side.LEFT)
        time.sleep(3)
        robot_interface.close_container(RobotContainer.SMALL_FRONT)

        app.shutdown()
        app = InteractionApp(contin=True)

        app.run()
        while app.is_running:
            time.sleep(1)
        app = IdleApp()
        app.run()

        passenger_zone.go_to_seat(4)

        AudioOutput.play_async("order_completed_souvenir.wav")
        robot_interface.set_head_rotation(-70, -10, completion=False)
        robot_interface.open_container(RobotContainer.SMALL_FRONT, Side.LEFT)
        time.sleep(3)
        robot_interface.close_container(RobotContainer.SMALL_FRONT)

        app.shutdown()
        app = InteractionApp(contin=True)

        app.run()
        while app.is_running:
            time.sleep(1)
        app = IdleApp()
        app.run()

        passenger_zone.go_to_base()
        robot_interface.set_head_rotation(-90, 0)
        robot_interface.move_to(vending[0], 0)

        robot_interface.on_command.off("Tch", self.on_touch_received)

        while True:
            time.sleep(1)


    def on_touch_received(self, state: int, *args):
        if state:
            AudioOutput.play_async("blocked.wav")


