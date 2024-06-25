import cv2
import threading
import numpy
import logging
import time

class CameraHandler:
    index: int
    """
    Индекс камеры, который передается в конструктор cv2.VideoCapture
    """

    # изображения сразу преобразуются в разные форматы, чтобы не делать это по многу раз в нескольких местах
    # комментарии под каждой переменной, чтобы IDE показывали их для каждой переменной
    image_bgr: cv2.Mat
    """
    Последний кадр, полученный с камеры, в формате BGR. 
    Не потокобезопасный, reader_thread не работает с объектом, а только заменяет ссылку на объект нового кадра.
    При использовании желательно создавать локальную переменную со ссылкой на кадр,
    т. к. при обработке ссылка может измениться на новый кадр.
    """

    image_hsv: cv2.Mat
    """
    Последний кадр, полученный с камеры, в формате HSV. 
    Не потокобезопасный, reader_thread не работает с объектом, а только заменяет ссылку на объект нового кадра.
    При использовании желательно создавать локальную переменную со ссылкой на кадр,
    т. к. при обработке ссылка может измениться на новый кадр.
    """

    __reader_thread: threading.Thread
    __capture: cv2.VideoCapture
    __logger: logging.Logger
    __is_running: bool    # используется для остановки reader_thread

    def __init__(self, index: int):
        self.index = index
        self.__logger = logging.getLogger(__name__ + ".CameraHandler")
        self.__is_running = False

        # заглушки до получения первого кадра с камеры, чтобы код не падал при обращении к этим переменным
        # разрешение задается в обратном порядке, т. к. это размеры массива
        # третий параметр разрешения - это 3 компонента цвета (BGR)
        self.image_bgr = cv2.Mat(numpy.ndarray((600, 1024, 3)))
        self.image_hsv = cv2.Mat(numpy.ndarray((600, 1024, 3)))

        self.__capture = CameraHandler.__get_capture(self.index)

        self.__reader_thread = threading.Thread(target=self.__reader_thread)
        self.__reader_thread.daemon = True

    def start(self):
        self.__is_running = True
        self.__reader_thread.start()

    def stop(self):
        self.__is_running = False

    @staticmethod
    def __get_capture(index: int) -> cv2.VideoCapture:
        capture = cv2.VideoCapture(index)
        if not capture.isOpened():
            raise ConnectionError(f"Camera {index} is unavailable")
        return capture

    def __reader_thread(self):
        self.__logger.debug(f"Camera {self.index} has started capturing")
        while self.__is_running:
            try:
                # к сведению: на слабом ноуте timeit показал, что на выполнение read() уходит в среднем 33 мс
                ret, bgr = self.__capture.read()
                if not ret:
                    self.__logger.warning(f"Failed to get image from camera {self.index}")
                    time.sleep(0.3)
                    continue
                
                hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

                self.image_bgr = bgr
                self.image_hsv = hsv

            except Exception as e:
                self.__logger.error(f"An error occured in reader thread of camera {self.index}", exc_info=e)
                time.sleep(0.5)
        self.__logger.debug(f"Camera {self.index} has stopped capturing")