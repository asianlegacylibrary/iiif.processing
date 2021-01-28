def get_image_index(image_name):
    tail_digits = 1
    while image_name[-(tail_digits + 1):].isdecimal():
        tail_digits += 1
    image_index = int(image_name[-tail_digits:])
    # print(f"image_name='{image_name}', tail_digits={tail_digits}, image_index={image_index}")
    return image_index
