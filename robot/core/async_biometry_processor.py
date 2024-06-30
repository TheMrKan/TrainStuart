import time
import numpy
from dataclasses import dataclass
from typing import Callable, Protocol, Optional, Type
from multiprocessing import Pipe, Process, Manager
from multiprocessing.connection import Connection
from threading import Thread


@dataclass
class GetFaceDescriptorRequest:
    image: numpy.ndarray
    face_location: Optional[tuple[int, int, int, int]]


@dataclass
class GetFaceDescriptorResponse:
    face_descriptor: Optional[numpy.ndarray]

    def get_callback_args(self):
        return (self.face_descriptor, )


class AsyncBiometryWorker:

    class ParametersProtocol(Protocol):
        connection: Connection
        is_running: bool

    __parameters: ParametersProtocol

    def __init__(self, parameters: ParametersProtocol):
        self.__parameters = parameters

        import face_recognition as recog
        self.__recognition = recog

        self.run()

    def run(self):
        while self.__parameters.is_running:
            if not self.__parameters.connection.poll(timeout=0.1):
                continue
            request = self.__parameters.connection.recv()

            match request:
                case GetFaceDescriptorRequest():
                    self.process_get_face_descriptor(request)
                case _:
                    pass

    def process_get_face_descriptor(self, request: GetFaceDescriptorRequest):
        descriptors = self.__recognition.face_encodings(request.image,
                                                        [request.face_location] if request.face_location is not None else None,
                                                        num_jitters=3,
                                                        model="large")
        descriptor = descriptors[0] if len(descriptors) > 0 else None
        response = GetFaceDescriptorResponse(descriptor)
        self.__parameters.connection.send(response)


class WorkerBusyError(Exception):
    pass


class AsyncBiometryProcessor:

    __connection: Connection
    __worker_parameters: AsyncBiometryWorker.ParametersProtocol
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
        cls.__worker_parameters: AsyncBiometryWorker.ParametersProtocol = cls.__manager.Namespace()

        cls.__connection, worker_connection = Pipe()
        cls.__worker_parameters.connection = worker_connection
        cls.__worker_parameters.is_running = True

        cls.__worker_process = Process(target=AsyncBiometryWorker, args=(cls.__worker_parameters, ))
        cls.__worker_process.daemon = True
        cls.__worker_process.start()

    @classmethod
    def shutdown(cls):
        cls.__worker_parameters.is_running = False
        cls.__worker_process.join()
        cls.__manager.shutdown()

    @classmethod
    def get_face_descriptor_async(cls, image: numpy.ndarray,
                                  callback: Callable[[numpy.ndarray | None], None],
                                  face_location: Optional[tuple[int, int, int, int]] = None):
        if cls.__response_awaiter:
            raise WorkerBusyError

        request = GetFaceDescriptorRequest(image, face_location)
        cls.__connection.send(request)
        cls.__await_response(callback, 2)

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







