from robot.hardware.cameras import CameraAccessor
from robot.gui.documents_check import DocumentsCheckApp
from robot.core.async_processor import AsyncProcessor
from robot.core.tickets import TicketsRepository


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

        DocumentsCheckApp().run()

    def shutdown(self):
        AsyncProcessor.shutdown()
        CameraAccessor.shutdown()
