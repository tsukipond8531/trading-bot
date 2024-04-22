import json
import os

from src.config import TRADING_DATA_DIR


def round(num, places):
    working = str(num - int(num))
    for i, e in enumerate(working[2:]):
        if e != '0':
            return int(num) + float(working[:i + 2 + places])


def save_json_to_file(json_data, file_name):
    out_file = os.path.join(TRADING_DATA_DIR, f'{file_name}.json')
    with open(out_file, "w") as ff:
        ff.write(json.dumps(json_data, indent=4, ensure_ascii=False))
