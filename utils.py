# Developed by Paulo Chiliguano
# Directed by Dr Roberto Alonso Trillo
# Department of Music - Hong Kong Baptist University
# 2024


import quaternion
from datetime import datetime
from os import makedirs
from os.path import expandvars, isdir, join
from platform import system
from typing import ByteString, List


Array = List[int]


def bytearray_to_fusion_data(data: ByteString) -> List[float]:
    """Converts a bytearray to a list of float numbers

    Parameters
    ----------
    data : bytearray
        bytes from BLE device

    Returns
    -------
    list
        A list of floats representing the timestamp and coordinates values
    """
    raw_list = _int_list_from_bytearray(data)
    raw_list[4:7] = _scale_gyroscope_coordinates(raw_list[4:7])

    return [float(f'{i:.1f}') for i in raw_list]


def _scale_gyroscope_coordinates(data: Array) -> Array:
    """Scale gyroscope data 1/10x as it comes multiplied

    Parameters
    ----------
    data : list
        X, Y, Z coordinates data (int16 each)

    Returns
    -------
    list
        A list of floats corresponding to coordinates data of the Blue ST gyroscope
    """
    return [0.1*i for i in data]


def _int_list_from_bytearray(data: ByteString) -> Array:
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
    timestamp = [uint16_from_bytes(data[0:step]),]
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


def _create_folder_in_desktop(dir: str):
    """
    """
    if not isdir(dir):
        makedirs(dir)


def log_file_path() -> str:
    """
    """
    if system() == "Windows":
        homefolder = expandvars(r"$HOMEPATH")
    else:
        homefolder = expandvars(r"$HOME")

    log_dir = join(homefolder, "Desktop", "Metabow Logs")

    _create_folder_in_desktop(log_dir)
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = join(log_dir, f"mb_{now}.csv")

    return filename


def pyquaternion_as_spherical_coords(elements):
    elems = quaternion.from_float_array(elements)
    return quaternion.as_spherical_coords(elems)
