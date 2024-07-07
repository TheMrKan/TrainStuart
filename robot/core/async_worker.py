from dataclasses import dataclass
from utils.cv import Image
from utils.faces import FaceDescriptor
from utils.scanner import PassportData
from typing import Optional, Protocol
from multiprocessing.connection import Connection
import traceback
import time


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
        resources_dir: str

    __parameters: ParametersProtocol

    def __init__(self, parameters: ParametersProtocol):
        self.__parameters = parameters

        import utils.faces as face_util
        self.__face_util = face_util
        self.__face_util.load_dependencies(parameters.resources_dir)

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


    def __process_get_face_descriptor(self, request: GetFaceDescriptorRequest):
        descriptor = self.__face_util.get_face_descriptor(request.image, request.face_location)
        response = GetFaceDescriptorResponse(descriptor)
        self.__parameters.connection.send(response)

    def __process_read_passport(self, request: ReadPassportRequest):
        data = self.__scanner.get_passport_data(request.image)
        time.sleep(1)
        response = ReadPassportResponse(data)
        self.__parameters.connection.send(response)