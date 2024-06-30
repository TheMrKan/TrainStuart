import cv2
import threading
import numpy
import logging
import time
import robot.config as config


logger = logging.getLogger(__name__)


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

    width: int
    height: int

    __reader_thread: threading.Thread | None
    __capture: cv2.VideoCapture
    __logger: logging.Logger
    __image_grabbed: threading.Event
    __is_running: bool    # используется для остановки reader_thread

    def __init__(self, index: int, width: int = 0, height: int = 0):
        self.index = index
        self.__logger = logging.getLogger(__name__ + ".CameraHandler")
        self.__is_running = False

        self.width = width
        self.height = height

        self.__capture = CameraHandler.__get_capture(self.index)
        if width > 0:
            self.__capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        if height > 0:
            self.__capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        self.image_bgr = cv2.Mat(numpy.zeros((width, height, 3), dtype=numpy.uint8))
        self.image_hsv = cv2.Mat(numpy.zeros((width, height, 3), dtype=numpy.uint8))

        self.__image_grabbed = threading.Event()

        self.__reader_thread = self.__produce_reader_thread()

    def start(self):
        self.__is_running = True
        self.__image_grabbed.clear()
        self.__reader_thread.start()

    def await_first_frame(self, timeout: float | None = None):
        self.__image_grabbed.wait(timeout)

    def stop(self):
        self.__image_grabbed.clear()
        self.__is_running = False
        if self.__reader_thread:
            self.__reader_thread.join()

    @staticmethod
    def __get_capture(index: int) -> cv2.VideoCapture:
        capture = cv2.VideoCapture(index=index)
        if not capture.isOpened():
            capture.release()
            raise ConnectionError(f"Camera {index} is unavailable")
        return capture

    def __produce_reader_thread(self):
        thread = threading.Thread(target=self.__reader_thread_worker)
        thread.daemon = True
        return thread


    def __grab_image(self) -> bool:
        """
        Считывает изображение с камеры и записывает его в двух форматах в self.image_bgr и self.image_hsv
        :return: True, если удалось считать изображение; иначе False
        """
        ret, bgr = self.__capture.read()
        if not ret:
            return False

        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        self.image_bgr = bgr
        self.image_hsv = hsv

        self.__image_grabbed.set()
        return True

    def __reader_thread_worker(self):
        self.__logger.debug(f"Camera {self.index} has started capturing")
        while self.__is_running:
            try:
                # к сведению: на слабом ноуте timeit показал, что на выполнение read() уходит в среднем 33 мс
                success = self.__grab_image()
                if not success:
                    self.__logger.warning(f"Failed to get image from camera {self.index}")
                    time.sleep(0.3)
                    continue

            except Exception as e:
                self.__logger.error(f"An error occured in reader thread of camera {self.index}", exc_info=e)
                time.sleep(0.5)
        self.__capture.release()
        self.__logger.debug(f"Camera {self.index} has stopped capturing")
        self.__reader_thread = None


class CameraAccessor:
    main_camera: CameraHandler = None
    documents_camera: CameraHandler = None

    @classmethod
    def initialize(cls):

        logger.info("Initializing cameras...")

        main_camera_index = config.instance.hardware.main_camera
        documents_camera_index = config.instance.hardware.documents_camera

        main_resolution = config.instance.get("hardware.main_camera_resolution", "0x0")
        main_resol_valid, main_width, main_height = config.try_parse_resolution(main_resolution)
        if not main_resol_valid:
            logger.warning(f"Invalid resolution for the main camera: {main_resolution}. Using default.")

        documents_resolution = config.instance.get("hardware.documents_camera_resolution", "0x0")
        documents_resol_valid, documents_width, documents_height = config.try_parse_resolution(documents_resolution)
        if not documents_resol_valid:
            logger.warning(f"Invalid resolution for the documents camera: {main_resolution}. Using default.")

        cls.main_camera = CameraHandler(main_camera_index, main_width, main_height)
        cls.main_camera.start()
        if documents_camera_index != main_camera_index:
            try:
                cls.documents_camera = CameraHandler(documents_camera_index, documents_width, documents_height)
                cls.documents_camera.start()
            except ConnectionError:
                logger.warning(f"Failed to connect to the documents camera ({documents_camera_index}). Using the main camera")
                cls.documents_camera = cls.main_camera
        else:
            cls.documents_camera = cls.main_camera

        logger.info("Cameras initialization completed")

    @classmethod
    def shutdown(cls):
        cls.main_camera.stop()
        cls.documents_camera.stop()
        logger.info("Cameras are shutted down")

