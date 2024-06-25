from bestconfig import Config
from typing import Protocol

class ConfigProtocol(Protocol):
    logging: dict

instance: ConfigProtocol

# реализация property для модулей
# проверяет, загружен ли конфиг перед тем, как его отдать
# нужно на случай обращения к конфигу в обход вызова load() в main.py
def __getattr__(name):
    if name == "instance":
        if instance is None:
            load()
        return instance
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

def load():
    global instance
    instance = Config()