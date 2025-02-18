import logging
import time
from utils.collections import first
from typing import Union

from robot.behaviour.base import BaseBehaviour
from robot.core.navigation import general, passenger_zone, chart
from robot.hardware import robot_interface as irobot
from robot.hardware.audio import AudioOutput
from robot.gui.interaction import InteractionApp
from robot.gui.base.app import BaseApp
from robot.gui.idle import IdleApp
from robot.core import calls, deliveries, passengers


class Target:
    seat: int

    def __init__(self, seat: int):
        self.seat = seat

    def set_completed(self):
        pass


class CallTarget(Target):

    def set_completed(self):
        calls.active_calls.remove(self.seat)


class DeliveryTarget(Target):
    delivery: deliveries.Delivery

    def __init__(self, delivery):
        super().__init__(delivery.seat)
        self.delivery = delivery

    def set_completed(self):
        deliveries.complete_delivery(self.delivery)


class CarriageMovingBehaviour(BaseBehaviour):
    RESTART_ON_EXCEPTION = False
    app: BaseApp = None

    INTERACTION_HEAD_ROT = -70, -20

    def __init__(self):
        super().__init__()

    def initialize(self):
        pass

    def __set_touch(self, enabled: bool):
        if enabled:
            irobot.on_command.on("Tch", self.on_touch_received)
        else:
            irobot.on_command.off("Tch", self.on_touch_received)

    def behave(self):
        self.app = IdleApp()
        self.app.run()

        self.__set_touch(True)

        general.locate()
        target = self.__select_target(True)
        if not target:
            general.go_home()

        while True:

            while not target:
                time.sleep(1)
                target = self.__select_target(False)
                if target:
                    break

            if isinstance(target, DeliveryTarget):
                general.go_home()
                self.__take_product(target)

            general.go_to_seat(target.seat)

            self.__interact(target)
            target.set_completed()

            target = self.__select_target(True)
            if not target:
                general.go_home()

        exit()

    def __wait_for_call(self) -> int:
        while not any(calls.active_calls):
            time.sleep(0.5)

        return first(calls.active_calls)

    def __select_target(self, force_update: bool) -> Union[CallTarget, DeliveryTarget, None]:
        if any(calls.active_calls):
            return CallTarget(first(calls.active_calls))

        delivery = deliveries.take_delivery(force_update)
        if delivery:
            return DeliveryTarget(delivery)

        return None

    def __interact(self, target: Union[CallTarget, DeliveryTarget]):
        self.__set_touch(False)
        irobot.set_head_rotation(*self.INTERACTION_HEAD_ROT, completion=False)

        if isinstance(target, DeliveryTarget):
            self.__give_product(target)

        passenger = passengers.get_by_seat(target.seat)

        self.app.shutdown()
        self.app = InteractionApp(passenger=passenger)

        self.app.run()
        while self.app.is_running:
            time.sleep(1)
        self.app = IdleApp()
        self.app.run()

        self.__set_touch(True)

    def __take_product(self, target: DeliveryTarget):
        irobot.open_container(target.delivery.container, irobot.Side.LEFT)
        time.sleep(4)
        irobot.close_container(target.delivery.container)

    def __give_product(self, target: DeliveryTarget):
        passenger = passengers.get_by_seat(target.seat)
        audio = passengers.get_name_audio(passenger.name) if passenger else None
        if audio:
            AudioOutput.play_async("hello", audio, "order_completed_eat.wav")
        else:
            AudioOutput.play_async("order_completed_eat.wav")
        irobot.open_container(target.delivery.container, irobot.Side.LEFT)
        time.sleep(6)
        irobot.close_container(target.delivery.container)

    def on_touch_received(self, state: int, *args):
        if isinstance(self.app, InteractionApp):
            return

        if state:
            AudioOutput.play_async("blocked.wav")


