
from typing import Callable, Optional
from multiprocessing import Pipe, Process, Manager
from multiprocessing.connection import Connection
from threading import Thread
from utils.scanner import PassportData
from utils.faces import FaceDescriptor
from utils.cv import Image
from robot.core.async_worker import *
import robot.config as config


class WorkerBusyError(Exception):
    pass


class AsyncProcessor:

    __connection: Connection
    __worker_parameters: AsyncWorker.ParametersProtocol
    __worker_process: Process
    __manager: Manager
    __response_awaiter: Optional[Thread]

    @classmethod
    def initialize(cls):

        cls.__response_awaiter = None

        cls.__manager = Manager()
        # на все объекты, получаемые из Manager, всегда должна оставаться хотя бы одна ссылка, иначе будут ошибки
        # если сохранять в локальную переменную, то после выхода из initialize ссылка пропадет
        # https://stackoverflow.com/questions/57299893/why-python-throws-multiprocessing-managers-remoteerror-for-shared-lock
        cls.__worker_parameters: AsyncWorker.ParametersProtocol = cls.__manager.Namespace()

        cls.__connection, worker_connection = Pipe()
        cls.__worker_parameters.connection = worker_connection
        cls.__worker_parameters.is_running = True
        cls.__worker_parameters.resources_dir = config.instance.resources_dir

        cls.__worker_process = Process(target=AsyncWorker, args=(cls.__worker_parameters, ))
        cls.__worker_process.daemon = True
        cls.__worker_process.start()

    @classmethod
    def shutdown(cls):
        cls.__worker_parameters.is_running = False
        cls.__worker_process.join()
        cls.__manager.shutdown()

    @classmethod
    def get_face_descriptor_async(cls, image: Image,
                                  callback: Callable[[FaceDescriptor | None], None],
                                  face_location: Optional[tuple[int, int, int, int]] = None):
        if cls.__response_awaiter:
            raise WorkerBusyError

        request = GetFaceDescriptorRequest(image, face_location)
        cls.__connection.send(request)
        cls.__await_response(callback, 4)

    @classmethod
    def read_passport_async(cls, image: Image,
                            callback: Callable[[PassportData | None], None]):
        if cls.__response_awaiter:
            raise WorkerBusyError
        
        request = ReadPassportRequest(image)
        cls.__connection.send(request)
        cls.__await_response(callback, 4)

    @classmethod
    def __await_response(cls, callback: Callable, timeout: Optional[float] = None):
        cls.__response_awaiter = Thread(target=cls.__awaiter, args=(callback, timeout))
        cls.__response_awaiter.start()

    @classmethod
    def __awaiter(cls, callback: Callable, timeout: Optional[float] = None):
        try:
            if cls.__connection.poll(timeout):
                response = cls.__connection.recv()
                callback(*response.get_callback_args())
        finally:
            cls.__response_awaiter = None







