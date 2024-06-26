import logging.config
import logging

import robot.config as config


logger: logging.Logger


def main():
    global logger
    config.load()

    logging.config.dictConfig(config.instance.logging)
    logger = logging.getLogger(__name__)
    logger.info("Logger is configured")

    # импорт после настроек логгера, чтобы logging.getLogger в модулях работал корректно
    from robot.runtime import Runtime

    runtime = Runtime()
    runtime.start()


if __name__ == "__main__":
    main()