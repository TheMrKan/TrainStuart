import pytesseract  # на будущее для распознавания текста
import cv2
import random
import json
import numpy as np


class PassportData:
    passport_number: str
    """
    Cерия и номер паспорта без пробелов
    """

    full_name: str
    """
    Фамилия имя отчество в верхнем регистре
    """

    date_of_birth: str
    """
    Дата рождения ДД.ММ.ГГГГ
    """

    face_descriptor: np.ndarray
    """
    Дескриптор лица
    """

    def __str__(self):
        return f"{self.full_name} ({self.date_of_birth}) [{self.passport_number}]"


class PassportNotFoundError(BaseException):
    """
    Паспорт не найден на изображении
    """
    pass


class DataRecognitionError(BaseException):
    """
    Не удалось прочитать данные с паспорта
    """
    pass


def get_passport_data(image: cv2.Mat) -> PassportData:
    """
    Находит паспорт на изображении и считывает с него ФИО, дату рождения, номер паспорта и дескриптор лица
    :param image: BGR изображение, содержащее паспорт
    :exception PassportNotFoundError:
    :exception DataRecognitionError:
    :return:
    """
    # TODO: реализовать чтение данных с изображения
    data = PassportData()
    data.passport_number = "6019767612"
    data.full_name = "ИВАНОВ ИВАН ИВАНОВИЧ"
    data.date_of_birth = "01.02.2000"
    data.face_descriptor = np.random.random_sample((128, ), )
    return data
