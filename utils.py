import json
from tkinter import Tk

from utils.config import ENCODING


def decode_data(data: bytes) -> dict:
        return json.loads(data.decode(ENCODING))


def encode_data(data: dict) -> bytes:
        return json.dumps(data).encode(ENCODING)


def get_name_by_value(collection: dict, collection_value):
    return [k for k, v in collection.items() if v == collection_value] [0]


def get_tk_root():
    root = Tk()
    root.geometry("350x400")
    root.resizable(0, 0)
    return root

