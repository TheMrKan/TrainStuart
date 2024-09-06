import logging
import time


class BaseBehaviour:

    logger: logging.Logger

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def run(self):
        self.logger.info(f"Running {type(self).__name__} behaviour")
        try:
            self.initialize()

            while True:
                try:
                    self.behave()
                except Exception as e:
                    self.logger.exception("Unhandled exception in __behave", exc_info=e)

        finally:
            self.finalize()

    def initialize(self):
        pass

    def finalize(self):
        pass

    def behave(self):
        time.sleep(1)