import time
from typing import Callable

from robot.hardware.cameras import CameraAccessor
from robot.core.async_processor import AsyncProcessor
from robot.core.tickets import TicketsRepository
import robot.core.route as route
import robot.core.server as server
import robot.core.calls as calls
import robot.hardware.serial_interface as iserial
from robot.gui.base import gui_server, navigation as gui_navigation
from robot.gui.startup import StartupApp
from robot.behaviour.station_idle import StationIdleBehaviour


class Runtime:

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
            self.__initialize(startup_app.set_status)
            startup_app.set_status("Готово!")
            time.sleep(1)
        except Exception as e:
            startup_app.set_status(f"Ошибка при загрузке. Выключение. {str(e)}")
            time.sleep(3)
            return
        finally:
            startup_app.shutdown()

        while not route.is_service_finished():
            StationIdleBehaviour().run()

    def __initialize(self, status_log: Callable[[str, ], None]):
        status_log("Настройка камер...")
        CameraAccessor.initialize()

        status_log("Загрузка обработчика...")
        AsyncProcessor.initialize()

        status_log("Получение билетов...")
        TicketsRepository.load()

        status_log("Получение информации о маршруте...")
        route.initialize()
        # iserial.setup()

        status_log("Подключение к серверу поезда...")
        server.start_polling()

        status_log("Подключение кнопок вызова...")
        calls.initialize()

    def shutdown(self):
        server.stop_polling()
        AsyncProcessor.shutdown()
        CameraAccessor.shutdown()
        gui_server.stop()
        gui_navigation.shutdown()
