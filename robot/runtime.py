from robot.hardware.cameras import CameraAccessor
from robot.gui.documents_check import DocumentsCheckApp
from robot.core.async_biometry_processor import AsyncBiometryProcessor


class Runtime:

    def start(self):
        try:
            self.__main()
        finally:
            self.shutdown()

    def __main(self):
        CameraAccessor.initialize()
        AsyncBiometryProcessor.initialize()

        DocumentsCheckApp().run()

    def shutdown(self):
        AsyncBiometryProcessor.shutdown()
        CameraAccessor.shutdown()
