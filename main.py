import logging.config
import multiprocessing
from gui import passport_check
import config
import logging

logger: logging.Logger

def main():
    global logger
    config.load()

    logging.config.dictConfig(config.instance.logging)
    logger = logging.getLogger(__name__)
    logger.info("Logger is configured")

    passport_check.start()


if __name__ == "__main__":
    main()