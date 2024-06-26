from bestconfig import Config
from typing import Protocol


class HardwareConfigProtocol(Protocol):
    main_camera: int
    documents_camera: int


class PassportCheckAppConfig(Protocol):
    show_dev_tools: bool


class ConfigProtocol(Protocol):
    logging: dict
    hardware: HardwareConfigProtocol
    passport_check: PassportCheckAppConfig


instance: ConfigProtocol | None = None


# реализация property для модулей
# проверяет, загружен ли конфиг перед тем, как его отдать
# нужно на случай обращения к конфигу в обход вызова load() в main.py
def __getattr__(name):
    global instance
    if name == "instance":
        #if instance is None:
            #load()
        return instance
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def load():
    global instance
    instance = Config()

