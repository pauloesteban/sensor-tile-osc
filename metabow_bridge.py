#!/usr/bin/python

# Modified by Paulo Chiliguano (@pauloesteban) and KA HO Wong
# Directed by Dr Roberto Alonso Trillo
# Department of Music - Hong Kong Baptist University
# 2022
#
#
# Based on bleak example
# Modified by james lewis (@baldengineer)
# MIT License
# 2020
import asyncio
import tkinter as tk

from datetime import datetime
from functools import partial
from typing import Union  # For later use with type hint on running loop, see below

from bleak import (
    BleakClient,
    BleakScanner,
)

from pythonosc import udp_client

from gesture_model import GestureModel
from utils import bytearray_to_fusion_data, log_file_path


simple_udp_client = udp_client.SimpleUDPClient("127.0.0.1", 8888)
CHARACTERISTIC_UUID = "00E00000-0001-11E1-AC36-0002A5D5C51B"
st_devices = {}
filename = log_file_path()
model = GestureModel()


def device_found(device, _):
    if device.name == "AM1V330":
        print(f"\033[92m {device.name} found\033[0m")
        st_devices[device.address] = device


def notification_handler(device_number:int, sender: int, data: bytearray):
    """Simple notification handler
    """
    join_array = bytearray_to_fusion_data(data)
    simple_udp_client.send_message(f"/{device_number}/raw", join_array)
    model.tick(join_array[1:4], join_array[4:7], join_array[7:10])
    simple_udp_client.send_message(f"/{device_number}/quaternion", model.quaternion.elements.tolist())
    simple_udp_client.send_message(f"/{device_number}/motion_acceleration/sensor_frame", model.movement_acceleration.tolist())
    
    with open(filename, 'a') as f:
        join_str = " ".join(str(e) for e in join_array[1:])
        f.write(f'{device_number} {datetime.now().strftime("%Y%m%d_%H%M%S.%f")} {join_str}\n')


async def connect_to_device(i, device):
    async with BleakClient(device) as client:
        print(f"\033[92mYou are connected to Device {i} - {device.name}\033[0m")
        await client.start_notify(CHARACTERISTIC_UUID, partial(notification_handler, i))
        while True:
            await asyncio.sleep(1.0)
        # await client.stop_notify(CHARACTERISTIC_UUID)


async def main():
    scanner = BleakScanner()
    scanner.register_detection_callback(device_found)
    await scanner.start()
    await asyncio.sleep(5.0)
    await scanner.stop()
    await asyncio.gather(*(connect_to_device(i, device) for i, (_, device) in enumerate(st_devices.items())))


class Window(tk.Tk):
    def __init__(self, loop: asyncio.unix_events._UnixSelectorEventLoop):  # Maybe different type hint on Windows
        self.root = tk.Tk()
        self.loop = loop
        self.scanner = BleakScanner()

        title = tk.Label(text="METABOW OSC BRIDGE")
        title.grid(row=0, columnspan=2, padx=(8, 8), pady=(16, 0))

        start_scan_button = tk.Button(
            text="Start Scan",
            width=10,
            command=lambda: self.loop.create_task(self.start_scan()),
        )
        
        start_scan_button.grid(row=1, column=0, sticky=tk.W, padx=8, pady=8)

        stop_scan_button = tk.Button(
            text="Stop Scan",
            width=10,
            command=lambda: self.loop.create_task(self.stop_scan()),
        )

        stop_scan_button.grid(row=1, column=1, sticky=tk.W, padx=8, pady=8)

        self.resultsContents = tk.StringVar()
        self.devices = tk.Label(textvariable=self.resultsContents)
        self.devices.grid(row=2, columnspan=2, padx=(8, 8), pady=(16, 0))
        self.resultContents.set("A")
        # entries = tk.Entry(
        #     self.root,
        #     textvariable="test"
        # )

        # entries.grid(row=3, sticky=tk.W, padx=8, pady=8)


    async def show(self):
        while True:
            self.root.update()
            await asyncio.sleep(0.01)

    
    async def start_scan(self):
        self.scanner.register_detection_callback(device_found)
        await self.scanner.start()
        await asyncio.sleep(3.0)
    

    async def stop_scan(self):
        await self.scanner.stop()


async def metabow():
    window = Window(asyncio.get_running_loop())
    await window.show()


if __name__ == '__main__':

    asyncio.run(metabow())