# Created by Paulo Chiliguano (@pauloesteban)
# Directed by Dr Roberto Alonso Trillo
# Department of Music - Hong Kong Baptist University
# 2022


from typing import ByteString, List


Array = List[int]


def int_list_from_bytearray(data: ByteString) -> Array:
    """Converts a bytearray to a list of signed integers

    Parameters
    ----------
    data : bytearray
        bytes from BLE device

    Returns
    -------
    list
        A list of integers representing the timestamp and coordinates values
    """
    step = 2
    timestamp = [uint16_from_bytes(data[0:step])]
    sensor_data = [int16_from_bytes(data[i:i+step]) for i in range(step, len(data) - 1, step)]

    return timestamp + sensor_data


def int16_from_bytes(data: ByteString) -> int:
    """Converts Little Indian (LE) bytes into integer

    Parameters
    ----------
    data : bytearray
        bytes subset in LE order

    Returns
    -------
    int
        Equivalent int16 signed integer
    """

    return int.from_bytes(data, byteorder='little', signed=True)


def uint16_from_bytes(data: ByteString) -> int:
    """Converts Little Indian (LE) bytes into unsigned integer

    Parameters
    ----------
    data : bytearray
        bytes subset in LE order

    Returns
    -------
    int
        Equivalent uint16 integer
    """

    return int.from_bytes(data, byteorder='little', signed=False)