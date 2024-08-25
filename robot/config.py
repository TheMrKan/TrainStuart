from bestconfig import Config
from bestconfig.config_provider import ConfigProvider
from typing import Protocol, Optional, Tuple


class HardwareConfig(Protocol):
    main_camera: int
    documents_camera: int
    main_camera_resolution: str
    documents_camera_resolution: str
    dummy_robot: bool
    serial: str


class PassportCheckAppConfig(Protocol):
    show_dev_tools: bool


class IdleAppConfig(Protocol):
    show_dev_tools: bool


class RouteConfig(Protocol):
    boarding_duration: int
    service_duration: int


class ServerConfig(Protocol):
    host: str
    polling_interval: float


class GUIConfig(Protocol):
    loading_page: str


class ConfigProtocol(Protocol):
    logging: dict
    hardware: HardwareConfig
    passport_check: PassportCheckAppConfig
    idle: IdleAppConfig
    route: RouteConfig
    resources_dir: str
    server: ServerConfig
    gui: GUIConfig


# чтобы показывались методы из ConfigProvider
class ConfigProtocolInherited(ConfigProtocol, ConfigProvider):
    pass


instance: Optional[ConfigProtocolInherited] = None


# реализация property для модулей
# проверяет, загружен ли конфиг перед тем, как его отдать
# нужно на случай обращения к конфигу в обход вызова load() в main.py
def __getattr__(name):
    global instance
    if name == "instance":
        if instance is None:
            load()
        return instance
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def load():
    global instance
    instance = Config()


def try_parse_resolution(resolution_str: str) -> Tuple[bool, int, int]:
    """
    Извлекает из строки вида '1920x1080' ширину и высоту
    :param resolution_str: Строка, содержащая два целых числа, разделенных маленькой латинской буквой 'x', где первое число - ширина, а второе - высота
    :return: Кортеж из трех значений. Первое - получилось ли спарсить строку, второе и третье - ширина и высота. Если первое значение False, то остальные будут равны 0
    """
    if not resolution_str:
        return False, 0, 0

    w_str, h_str = resolution_str.split("x", 1)
    if w_str.isdigit() and h_str.isdigit():
        return True, int(w_str), int(h_str)

    return False, 0, 0
