import time
import numpy
from dataclasses import dataclass
from typing import Callable, Protocol, Optional, Type
from multiprocessing import Pipe, Process, Manager
from multiprocessing.connection import Connection
from threading import Thread
import traceback
from utils.scanner import PassportData
import random
from utils.cancelations import sleep
from utils.faces import FaceDescriptor
from utils.cv import Image


@dataclass
class GetFaceDescriptorRequest:
    image: Image
    face_location: Optional[tuple[int, int, int, int]]


@dataclass
class GetFaceDescriptorResponse:
    face_descriptor: Optional[FaceDescriptor]

    def get_callback_args(self):
        return (self.face_descriptor, )
    

@dataclass
class ReadPassportRequest:
    image: Image


@dataclass
class ReadPassportResponse:
    passport_data: Optional[PassportData]

    def get_callback_args(self):
        return (self.passport_data, )
    

class AsyncWorker:

    class ParametersProtocol(Protocol):
        connection: Connection
        is_running: bool

    __parameters: ParametersProtocol

    def __init__(self, parameters: ParametersProtocol):
        self.__parameters = parameters

        import face_recognition as recog
        self.__recognition = recog

        import utils.scanner as scanner
        self.__scanner = scanner

        self.run()

    def run(self):
        while self.__parameters.is_running:
            try:
                if not self.__parameters.connection.poll(timeout=0.1):
                    continue
                request = self.__parameters.connection.recv()

                match request:
                    case GetFaceDescriptorRequest():
                        self.__process_get_face_descriptor(request)
                    case ReadPassportRequest():
                        self.__process_read_passport(request)
                    case _:
                        pass
            except Exception:
                traceback.print_exc()

    def __get_face_descriptor(self, image: Image, face_location: Optional[tuple[int, int, int, int]] = None) -> FaceDescriptor:
        descriptors = self.__recognition.face_encodings(image,
                                                        [face_location] if face_location is not None else None,
                                                        num_jitters=3,
                                                        model="large")
        descriptor = descriptors[0] if len(descriptors) > 0 else None
        return descriptor


    def __process_get_face_descriptor(self, request: GetFaceDescriptorRequest):
        descriptor = self.__get_face_descriptor(request.image, request.face_location)
        response = GetFaceDescriptorResponse(descriptor)
        self.__parameters.connection.send(response)

    def __process_read_passport(self, request: ReadPassportRequest):
        data = self.__scanner.get_passport_data(request.image)
        sleep(1)
        response = ReadPassportResponse(data)
        self.__parameters.connection.send(response)


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
        cls.__await_response(callback, 2)

    @classmethod
    def read_passport_async(cls, image: Image,
                            callback: Callable[[PassportData | None], None]):
        if cls.__response_awaiter:
            raise WorkerBusyError
        
        request = ReadPassportRequest(image)
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






