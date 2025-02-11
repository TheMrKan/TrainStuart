from typing import IO, Optional
import cv2
from PIL import Image
from dataclasses import dataclass
import tempfile
import pytesseract
from fuzzywuzzy import process
from server.core import passengers


NUMBER_BOX = ((0.0795, 0), (0.3968, 0.1467))
SYMBOLS = set("0123456789")


class LoadedDocument:
    full: Image.Image
    passport_number_img: Image.Image

    def __init__(self, full: Image.Image, passport_number_img: Image.Image):
        self.full = full
        self.passport_number_img = passport_number_img


def load_file(file: IO) -> LoadedDocument:
    img = Image.open(file)
    w, h = img.size
    if h > w:
        img = img.rotate(-90)
        w, h = h, w
    x1, y1, x2, y2 = map(lambda a: int(round(a)), (NUMBER_BOX[0][0] * w, NUMBER_BOX[0][1] * h, NUMBER_BOX[1][0] * w, NUMBER_BOX[1][1] * h))
    cropped = img.crop((x1, y1, x2, y2))
    return LoadedDocument(img, cropped)


def process_ocr(document: LoadedDocument):
    document.passport_number_img.show()
    img = document.passport_number_img.convert('L').resize([3 * _ for _ in document.passport_number_img.size], Image.Resampling.BICUBIC)
    img.show()
    raw_result = pytesseract.image_to_string(img, "rus", "--oem 1 --psm 6")
    print("OCR Raw Result:", raw_result)

    _result = []
    for c in raw_result:
        if c in SYMBOLS:
            _result.append(c)
    result = "".join(_result)
    result = result.ljust(10, "0")
    return result


def try_find_passenger(passport_number_str: str) -> Optional[passengers.Passenger]:
    result = process.extractOne(passport_number_str,
                                tuple(passengers.with_passport()),
                                processor=lambda p: p.passport if isinstance(p, passengers.Passenger) else p,
                                score_cutoff=1)
    print("Comprasion result:", result)
    if not result:
        return None

    return result[0]
