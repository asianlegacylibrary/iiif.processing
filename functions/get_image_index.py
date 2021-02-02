import re
from pathlib import Path


def get_trailing_number(s):
    m = re.search(r'\d+$', s)
    return int(m.group()) if m else 0


def standardize_digits(image_name):
    img = Path(image_name).stem
    idx = get_trailing_number(img)
    standard_idx = "{0:0=4d}".format(idx)
    return standard_idx


def get_image_index(image_name):
    tail_digits = 1
    while image_name[-(tail_digits + 1):].isdecimal():
        tail_digits += 1
    image_index = int(image_name[-tail_digits:])
    # print(f"image_name='{image_name}', tail_digits={tail_digits}, image_index={image_index}")
    return image_index
