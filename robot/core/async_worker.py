from dataclasses import dataclass
from utils.cv import Image
from utils.faces import FaceDescriptor
from utils.docs_reader import PassportData
from typing import Optional, Protocol, Any, Callable, Tuple
from multiprocessing.connection import Connection
import traceback
import time


@dataclass
class ExceptionResponse:
    exception: Exception


@dataclass
class GetFaceDescriptorRequest:
    image: Image
    face_location: Optional[Tuple[int, int, int, int]]


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
        operation_timeout: bool
        """
        Устанавливается в True из AsyncProcessor.__awaiter при наступлении таймаута. 
        Устанавливается обратно в False после завершения выполнения операции в AsyncWoker. 
        Если значение True, значит уже был вызван error_callback с TimeoutError, но AsyncWoker всё еще заблокирован предыдущей операцией.
        """
        resources_dir: str

    __parameters: ParametersProtocol

    def __init__(self, parameters: ParametersProtocol):
        self.__parameters = parameters

        import utils.faces as face_util
        self.__face_util = face_util
        self.__face_util.load_dependencies(parameters.resources_dir)

        import utils.docs_reader as scanner
        self.__scanner = scanner

        self.run()

    def run(self):
        while self.__parameters.is_running:
            
                if not self.__parameters.connection.poll(timeout=0.1):
                    continue
                request = self.__parameters.connection.recv()

                handler = None
                if isinstance(request, GetFaceDescriptorRequest):
                    handler = self.__process_get_face_descriptor
                elif isinstance(request, ReadPassportRequest):
                    handler = self.__process_read_passport

                self.__process(request, handler)

    def __send_exception(self, exception: Exception):
        response = ExceptionResponse(exception)
        self.__parameters.connection.send(response)

    def __process(self,
                  request: Any,
                  request_handler: Optional[Callable]):
        try:
            if not request_handler:
                raise TypeError(f"Unknown request: {request}")

            response = request_handler(request)

            if not self.__parameters.operation_timeout:
                self.__parameters.connection.send(response)
        except Exception as e:
            traceback.print_exc()
            self.__send_exception(e)
        finally:
            self.__parameters.operation_timeout = False

    def __process_get_face_descriptor(self, request: GetFaceDescriptorRequest) -> GetFaceDescriptorResponse:
        descriptor = self.__face_util.get_face_descriptor(request.image, request.face_location)
        return GetFaceDescriptorResponse(descriptor)

    def __process_read_passport(self, request: ReadPassportRequest) -> ReadPassportResponse:
        data = self.__scanner.get_passport_data(request.image)
        # TODO: Убрать задержку после реализации get_passport_data
        time.sleep(1)
        return ReadPassportResponse(data)
