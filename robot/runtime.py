from robot.hardware.cameras import CameraAccessor
from robot.gui.documents_check import DocumentsCheckApp


class Runtime:

    def start(self):
        try:
            self.__main()
        finally:
            self.shutdown()

    def __main(self):
        CameraAccessor.initialize()

        DocumentsCheckApp().run()

    def shutdown(self):
        CameraAccessor.shutdown()
