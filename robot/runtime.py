import time
from typing import Callable
import logging

from robot.hardware.cameras import CameraAccessor
from robot.core.async_processor import AsyncProcessor
from robot.core.tickets import TicketsRepository
import robot.core.route as route
import robot.core.server as server
import robot.core.calls as calls
from robot.hardware import robot_interface
from robot.gui.base import gui_server, navigation as gui_navigation
from robot.gui.startup import StartupApp
from robot.behaviour.station_idle import StationIdleBehaviour
from robot.behaviour.carriage_moving import CarriageMovingBehaviour
from robot.dev import control_panel
from robot.core.navigation import chart
from robot.gui.documents_check import DocumentsCheckApp


class Runtime:

    __logger: logging.Logger

    def __init__(self):
        self.__logger = logging.getLogger(__name__)

    def start(self):
        try:
            self.__main()
        finally:
            self.shutdown()

    def __main(self):
        gui_navigation.initialize()
        gui_server.start()

        startup_app = StartupApp()
        startup_app.run()

        try:
            def status_log(msg: str):
                startup_app.set_status(msg)
                self.__logger.info(msg)

            self.__initialize(status_log)
            startup_app.set_status("Готово!")
            time.sleep(1)
        except Exception as e:
            startup_app.set_status(f"Ошибка при загрузке. Выключение. {str(e)}")
            self.__logger.error("An error occured while loading", exc_info=e)
            time.sleep(3)
            return
        finally:
            startup_app.shutdown()

        '''while True:
            app = DocumentsCheckApp()
            try:
                app.run()
            except Exception as e:
                self.__logger.exception("An error occured in DocumentsCheckApp", exc_info=e)
            finally:
                app.shutdown()'''

        CarriageMovingBehaviour().run()
        while True:
            time.sleep(1)

    def __initialize(self, status_log: Callable[[str, ], None]):
        status_log("Настройка камер...")
        CameraAccessor.initialize()

        status_log("Загрузка обработчика...")
        AsyncProcessor.initialize()

        status_log("Получение билетов...")
        TicketsRepository.load()

        status_log("Получение информации о маршруте...")
        route.initialize()

        status_log("Подключение оборудования...")
        robot_interface.initialize()

        status_log("Подключение к серверу поезда...")
        server.start_polling()

        status_log("Подключение кнопок вызова...")
        calls.initialize()

        chart.load()

        status_log("Настройка панели управления...")
        control_panel.initialize()

    def shutdown(self):
        server.stop_polling()
        AsyncProcessor.shutdown()
        CameraAccessor.shutdown()
        gui_server.stop()
        gui_navigation.shutdown()
