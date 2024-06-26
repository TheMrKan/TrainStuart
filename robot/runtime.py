from robot.hardware.cameras import CameraAccessor
from robot.gui import passport_check


class Runtime:

    def start(self):
        try:
            self.__main()
        finally:
            self.shutdown()

    def __main(self):
        CameraAccessor.initialize()

        passport_check.start()

    def shutdown(self):
        CameraAccessor.shutdown()
