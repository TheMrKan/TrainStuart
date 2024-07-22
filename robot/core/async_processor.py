
from typing import Callable, Optional, Any, TypeAlias
from multiprocessing import Pipe, Process, Manager
from multiprocessing.connection import Connection
from threading import Thread
from dataclasses import dataclass
from utils.scanner import PassportData
from utils.faces import FaceDescriptor
from utils.cv import Image
from robot.core.async_worker import *
import robot.config as config


class WorkerBusyError(Exception):
    pass


class TimeoutError(Exception):
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
        cls.__worker_parameters.operation_timeout = False

        cls.__worker_process = Process(target=AsyncWorker, args=(cls.__worker_parameters, ))
        cls.__worker_process.daemon = True
        cls.__worker_process.start()

    @classmethod
    def shutdown(cls):
        cls.__worker_parameters.is_running = False
        cls.__worker_process.join()
        cls.__manager.shutdown()

    @classmethod
    def is_worker_busy(cls) -> bool:
        return cls.__response_awaiter or cls.__worker_parameters.operation_timeout
        

    @classmethod
    def get_face_descriptor_async(cls, image: Image,
                                  success_callback: Callable[[FaceDescriptor | None], None],
                                  error_callback: Callable[[Exception], None],
                                  face_location: Optional[tuple[int, int, int, int]] = None):
        if cls.is_worker_busy():
            raise WorkerBusyError

        request = GetFaceDescriptorRequest(image, face_location)
        cls.__connection.send(request)
        cls.__await_response(success_callback, error_callback, 5)

    @classmethod
    def read_passport_async(cls, image: Image,
                            success_callback: Callable[[PassportData | None], None],
                            error_callback: Callable[[Exception], None],):
        if cls.is_worker_busy():
            raise WorkerBusyError
        
        request = ReadPassportRequest(image)
        cls.__connection.send(request)
        cls.__await_response(success_callback, error_callback, 5)

    @classmethod
    def __await_response(cls, 
                         success_callback: Callable, 
                         error_callback: Callable[[Exception], None], 
                         timeout: Optional[float] = None):
        cls.__response_awaiter = Thread(target=cls.__awaiter, args=(success_callback, error_callback, timeout))
        cls.__response_awaiter.start()

    @classmethod
    def __awaiter(cls, 
                  success_callback: Callable, 
                  error_callback: Callable[[Exception], None], 
                  timeout: Optional[float] = None):
        is_timeout = not cls.__connection.poll(timeout)
        cls.__response_awaiter = None

        if is_timeout:
            cls.__worker_parameters.operation_timeout = True
            error_callback(TimeoutError())
            return

        response = cls.__connection.recv()
        if isinstance(response, ExceptionResponse):
            error_callback(response.exception)
        else:
            success_callback(*response.get_callback_args())
                

            







