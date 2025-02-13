from typing import IO, Optional, TypedDict
from dataclasses import dataclass
from server.core import passengers
import base64
import os
import requests
import json


def load_file(file: IO) -> str:
    return base64.b64encode(file.read()).decode("utf-8")


def process_ocr(b64img: str):
    print("Running OCR...")
    #return "3620896892"
    data = {
        "mimeType": "image",
        "languageCodes": ["ru", "en"],
        "model": "passport",
        "content": b64img}

    url = "https://ocr.api.cloud.yandex.net/ocr/v1/recognizeText"
    headers = {"Content-Type": "application/json",
               "Authorization": "Api-Key {:s}".format(os.getenv("YAPI_KEY")),
               "x-folder-id": os.getenv("YAPI_FOLDER"),
               "x-data-logging-enabled": "true"}

    w = requests.post(url=url, headers=headers, data=json.dumps(data))
    w.raise_for_status()
    result = w.json()

    entities = result["result"]["textAnnotation"]["entities"]
    print(entities)
    for e in entities:
        if e["name"] == "number":
            return e["text"]
    return None
