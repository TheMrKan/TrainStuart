import time

from robot.hardware.cameras import CameraAccessor
from robot.core.async_processor import AsyncProcessor
from robot.core.tickets import TicketsRepository
import robot.core.route as route
import robot.core.server as server
import robot.core.calls as calls
import robot.hardware.serial_interface as iserial
from robot.gui.base import gui_server, navigation as gui_navigation
from robot.gui.startup import StartupApp


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

        startup_app.set_status("Настройка камер...")
        CameraAccessor.initialize()

        startup_app.set_status("Загрузка обработчика...")
        AsyncProcessor.initialize()

        startup_app.set_status("Получение билетов...")
        TicketsRepository.load()

        startup_app.set_status("Получение информации о маршруте...")
        route.initialize()
        #iserial.setup()

        startup_app.set_status("Подключение к серверу поезда...")
        server.start_polling()

        startup_app.set_status("Подключение кнопок вызова...")
        calls.initialize()

        startup_app.set_status("Готово!")

        try:
            while True:
                time.sleep(3)
        except KeyboardInterrupt:
            pass

        startup_app.shutdown()


    def shutdown(self):
        server.stop_polling()
        AsyncProcessor.shutdown()
        CameraAccessor.shutdown()
        gui_server.stop()
        gui_navigation.shutdown()
