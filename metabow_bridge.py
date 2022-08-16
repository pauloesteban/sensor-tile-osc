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
from tkinter import ttk
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


def notification_handler(device_number:int, sender: int, data: bytearray):
    """Simple notification handler
    """
    print(device_number, sender, data)
    # join_array = bytearray_to_fusion_data(data)
    # model.tick(join_array[1:4], join_array[4:7], join_array[7:10])
    # simple_udp_client.send_message(f"/{device_number}/raw", join_array)
    # simple_udp_client.send_message(f"/{device_number}/quaternion", model.quaternion.elements.tolist())
    # simple_udp_client.send_message(f"/{device_number}/motion_acceleration/sensor_frame", model.movement_acceleration.tolist())
    
    # with open(filename, 'a') as f:
    #     join_str = " ".join(str(e) for e in join_array[1:])
    #     f.write(f'{device_number} {datetime.now().strftime("%Y%m%d_%H%M%S.%f")} {join_str}\n')


def device_found(device, _):
    if device.name == "AM1V330":
        print(f"{device.__dict__}\033[92m found\033[0m {type(device)}")
    st_devices[device.address] = device  # bleak.backends.device.BLEDevice


async def connect_to_device(i, device):
    async with BleakClient(device) as client:
        print(f"\033[92mYou are connected to Device {i} - {device.name}\033[0m")
        await asyncio.sleep(1.0)
        # await client.start_notify(CHARACTERISTIC_UUID, partial(notification_handler, i))
        # while True:
        #     await asyncio.sleep(1.0)
        # await client.stop_notify(CHARACTERISTIC_UUID)

class Window(tk.Tk):
    def __init__(self, loop: asyncio.unix_events._UnixSelectorEventLoop):  # Delete type hint when building on Windows
        self.root = tk.Tk()
        self.root.title("Metabow OSC bridge")
        self.root.resizable(False, False)
        self.loop = loop
        self.scanner = BleakScanner()  # TODO: Catch error when Bluetooth is off
        
        self.port0 = tk.StringVar()
        self.port0.set(8888)
        self.ports_frame = self.create_ports_frame(self.root)
        self.ports_frame.grid(column=0, row=0, padx=10, pady=10, sticky=tk.NW)
        
        self.devices_frame = self.create_scanner_frame(self.root)
        self.devices_frame.grid(column=1, row=0, padx=10, pady=10)
        self.refresh_listbox = False

        self.selected_devices_keys = []


    def create_ports_frame(self, container):
        label_frame = ttk.Labelframe(container, text='UDP Ports', relief=tk.RIDGE)
        label_frame.grid(row=0, column=0, sticky=tk.W)
        title = ttk.Label(label_frame, text=f"Device Port:")
        title.grid(row=0, column=0, sticky=tk.W)
        self.osc_port = ttk.Spinbox(label_frame, from_=1024, to=49151, textvariable=self.port0, width=10)
        self.osc_port.grid(row=0, column=1, sticky=tk.W)
        
        # for widget in frame.winfo_children():
        #     widget.grid(padx=0, pady=5)

        return label_frame


    def items_selected(self, event):
        selected_ix = self.devices_listbox.curselection()
        selected_devices_keys = [self.devices_listbox.get(i) for i in selected_ix]
        self.selected_devices = [st_devices[i] for i in selected_devices_keys]

    
    def create_scanner_frame(self, container):
        label_frame = ttk.Labelframe(container, text='Devices', relief=tk.RIDGE)
        label_frame.grid(row=0, column=0, sticky=tk.W)
        self.start_scan_button = ttk.Button(
            label_frame,
            text="Scan",
            width=10,
            command=lambda: self.loop.create_task(self.start_scan()),
        )
        self.start_scan_button.grid(row=0, column=0, sticky=tk.W)
        # self.start_scan_button.focus()

        self.stop_scan_button = ttk.Button(
            label_frame,
            text="Stop Scan",
            width=10,
            command=lambda: self.loop.create_task(self.stop_scan()),
        )
        self.stop_scan_button.state(['disabled'])
        self.stop_scan_button.grid(row=0, column=1, sticky=tk.W)

        self.connect_button = ttk.Button(
            label_frame,
            text="Connect",
            width=10,
            command=lambda: self.loop.create_task(self.connect()),
        )
        self.connect_button.state(['disabled'])
        self.connect_button.grid(row=0, column=2, sticky=tk.W)

        # self.disconnect_button = ttk.Button(
        #     label_frame,
        #     text="Disconnect",
        #     width=10,
        # )
        # self.disconnect_button.state(['disabled'])
        # self.disconnect_button.grid(row=0, column=3, sticky=tk.W)

        self.devices_listbox = tk.Listbox(label_frame, width=50, selectmode='extended')
        self.devices_listbox.grid(row=1, columnspan=4, sticky=tk.W)
        self.devices_listbox.insert(0, "Please press Scan...")
        self.devices_listbox.bind('<<ListboxSelect>>', self.items_selected)
        self.devices_listbox.config(state=tk.DISABLED)

        return label_frame

    
    async def show(self):
        while True:
            if self.refresh_listbox:
                self.populate_devices()

            self.root.update()
            await asyncio.sleep(0.1)

    
    async def start_scan(self):
        self.scanner.register_detection_callback(device_found)
        await self.scanner.start()
        self.start_scan_button.state(['disabled'])
        self.stop_scan_button.state(['!disabled'])
        self.connect_button.state(['disabled'])
        self.devices_listbox.config(state=tk.NORMAL)
        self.refresh_listbox = True
        await asyncio.sleep(1.0)
    

    async def stop_scan(self):
        self.start_scan_button.state(['!disabled'])
        self.stop_scan_button.state(['disabled'])
        self.connect_button.state(['!disabled'])
        self.refresh_listbox = False
        await self.scanner.stop()


    async def connect(self):
        if len(self.selected_devices) == 0:
            return
        self.connect_button.state(['disabled'])
        self.devices_listbox.config(state=tk.DISABLED)
        await asyncio.gather(*(connect_to_device(i, device) for i, device in enumerate(self.selected_devices)))


    def populate_devices(self):
        if len(st_devices):
            self.devices_listbox.delete(0, 'end')

            for k, v in st_devices.items():
                self.devices_listbox.insert('end', k)


async def metabow():
    window = Window(asyncio.get_running_loop())
    await window.show()


if __name__ == '__main__':
    asyncio.run(metabow())