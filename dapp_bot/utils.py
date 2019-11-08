import math
import random
import string
import base64


def reduction_addr(addr, lenght=15):
    if len(addr) <= lenght:
        return addr
    len_visible_part = math.ceil(lenght / 2 - 1.5)
    number_points = lenght - len_visible_part * 2
    return addr[:len_visible_part + 2] + '.' * number_points + addr[-len_visible_part + 2:]


def create_sequence(length=10):
    path_list = random.sample(string.ascii_lowercase + string.digits, length)
    return ''.join(path_list)


def encode_to_base64(sequence):
    return base64.b64encode(str(sequence).encode('u8')).decode()



