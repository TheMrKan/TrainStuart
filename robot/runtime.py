from robot.hardware.cameras import CameraAccessor
from robot.gui.documents_check import DocumentsCheckApp
from robot.gui.idle import IdleApp
from robot.core.async_processor import AsyncProcessor
from robot.core.tickets import TicketsRepository
import robot.core.route as route


class Runtime:

    def start(self):
        try:
            self.__main()
        finally:
            self.shutdown()

    def __main(self):
        CameraAccessor.initialize()
        AsyncProcessor.initialize()
        TicketsRepository.load()
        route.initialize()

        DocumentsCheckApp().run()

        while not route.is_service_finished():
            idle_app = IdleApp()
            idle_app.run()

            if idle_app.next:
                break

    def shutdown(self):
        AsyncProcessor.shutdown()
        CameraAccessor.shutdown()
