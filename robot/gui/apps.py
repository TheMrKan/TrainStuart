import logging
import threading
import time
import webview
import os.path
from typing import Generic, Optional
from abc import abstractmethod

import robot.gui.utils as utils
from utils.cancelations import sleep, await_event, CancellationToken


class PipelineLogicError(Exception):
    """
    Базовый класс для логических ошибок во время выполнения пайплайна. Не логируются как ошибка, а просто приводят к перезапуску пайплайна.
    """
    pass


class BasePipelineAPI:

    continue_event: threading.Event
    cancellation_token: CancellationToken

    def __init__(self, cancellation_token: Optional[CancellationToken] = None):
        self.cancellation_token = cancellation_token or CancellationToken()
        self.continue_event = threading.Event()

    def send_continue(self):
        """
        Вызывается из JavaScript кода для продолжения выполнения пайплайна, который ожидает await_continue
        """
        self.continue_event.set()

    def await_continue(self, timeout: Optional[float] = None) -> bool:
        """
        Блокирует поток до тех пор, пока пользователь не нажмет кнопку "Продолжить"
        :param timeout: Таймаут ожидания
        :return: True, если ожидание прекращено из-за нажатия кнопки. False, если ожидание прекращено из-за таймаута
        """
        self.continue_event.clear()    # на случай, если send_continue был вызван не во время ожидания

        await_event(self.continue_event, timeout, self.cancellation_token)

        if self.continue_event.is_set():
            self.continue_event.clear()
            return True

        return False


class BasePipelineApp:
    """
    Базовый класс для приложений с пайплайном
    """

    NAME = "BasePipelineApp"
    """
    Название приложения. Должно быть переопределено в классе конкретного приложения. Используется в качестве названия для логгера и названия для окна
    """

    ASSETS_PATH = "./gui/assets/"
    """
    Путь до папки всех ассетов приложения (шаблоны/статика). Указывается относительно рабочей дирректории на момент выполнения приложения
    """

    PAGES = {
        "default": "loading.html"
    }
    """
    Сокращенные названия для страниц. 
    Зарезервированные имена: default - страница, которая открывается при запуске приложения. 
    default должно быть определено в каждом приложении
    """

    logger: logging.Logger
    # если window != None а is_running = False, значит приложение выключается через shutdown. Если window = None, значит приложение завершается закрытием окна
    window: Optional[webview.Window]    # когда становится None, значит окно приложения закрылось
    is_running: bool    # устанавливается в True в run; в False - в shutdown. Служит сигналом для завершения циклов в __main
    cancellation: CancellationToken
    api: BasePipelineAPI    # JS API
    app_thread: Optional[threading.Thread]    # поток, в котором выполняется функция __main. Устанавливается сразу при запуске __main

    def __init__(self):
        self.logger = logging.getLogger(self.NAME)

        self.app_thread = None
        self.is_running = False
        self.cancellation = CancellationToken()

        self.api = self.produce_api()

        self.window = webview.create_window(self.NAME,
                                            url=self.get_page_url("default"),
                                            js_api=self.api,
                                            **self.get_window_params())

    def run(self):
        """
        Запускает приложение и блокирует дальнейшее выполнение до завершения выполнения приложения
        :return:
        """
        self.window.closed += self.on_window_closed

        self.is_running = True
        webview.start(func=self.main,
                      http_server=True,
                      **self.get_webview_start_params(),
                      )

    def shutdown(self):
        """
        Сообщает потоку приложения о завершении работы и ожидает окончания работы потока
        :return:
        """
        self.logger.debug("App is shutting down...")
        self.is_running = False
        self.cancellation.cancel()
        self.api.cancellation_token.cancel()

        if self.app_thread and threading.current_thread() != self.app_thread:
            self.app_thread.join()

        if self.window:
            self.window.destroy()

        self.logger.debug("App was terminated")

    def main(self):
        self.app_thread = threading.current_thread()

        while self.check_is_running():
            try:
                self.logger.debug("App pipeline started")
                self.pipeline()
                self.logger.debug("App pipeline finished")
            except InterruptedError:
                self.logger.debug("Restarting pipeline because of interruption")
            except PipelineLogicError as ex:
                self.logger.debug(f"Restarting pipeline because of {type(ex).__name__}")
            except Exception as ex:
                self.logger.error("An error occured in the app pipeline. Restarting...", exc_info=ex)
            finally:
                continue

        if self.is_running:
            self.shutdown()

    def check_is_running(self) -> bool:
        """
        Используется для завершения работы приложения по какому-то условию.
        Как только возвращает False, работа пайплайна должна завершаться.
        Должно учитывать значение is_running и window
        :return:
        """
        return self.is_running and self.window

    @abstractmethod
    def pipeline(self):
        pass

    def send_page(self, name):
        """
        Отображает в окне указанную страницу. Если она уже отображается, то перезагружает
        :param name: Название страницы в PAGES
        """

        url = self.get_page_url(name)
        utils.send_url(self.window, url)
        self.logger.debug(f"Window location: '{name}'")

    def on_window_closed(self):
        self.logger.debug("App window was closed")
        self.window = None
        if self.is_running:
            self.shutdown()

    def get_file_url(self, filename: str) -> str:
        """
        Возвращает url до файла относительно ASSETS_PATH
        """
        return os.path.join(self.ASSETS_PATH, filename)

    def get_page_url(self, page_name: str) -> str:
        """
        get_file_url, но путь до файла берет из PAGES
        """
        return self.get_file_url(self.PAGES[page_name])

    def produce_api(self) -> BasePipelineAPI:
        return BasePipelineAPI(cancellation_token=self.cancellation)

    @staticmethod
    def get_window_params() -> dict:
        return {}

    @staticmethod
    def get_webview_start_params() -> dict:
        return {}


class BaseLoopApp(BasePipelineApp):

    def main(self):
        self.app_thread = threading.current_thread()

        try:
            self.loop_start()
        except Exception as e:
            self.logger.exception("An error occured in 'loop_start'")

        self.logger.debug("App loop started")
        while self.check_is_running():
            try:
                self.loop()
            except InterruptedError:
                self.logger.debug("Stopping loop because of interruption")
                break
            except Exception as ex:
                self.logger.error("An error occured in the app loop.", exc_info=ex)
        self.logger.debug("App loop stopped")

        try:
            self.loop_stop()
        except Exception as e:
            self.logger.exception("An error occured in 'loop_stop'")

        if self.is_running:
            self.shutdown()


    def loop_start(self):
        pass


    def loop(self):
        pass


    def loop_stop(self):
        pass

