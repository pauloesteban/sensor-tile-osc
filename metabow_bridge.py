#!/usr/bin/python

# Modified by Paulo Chiliguano (@pauloesteban) and KA HO Wong
# Directed by Dr Roberto Alonso Trillo
# Department of Music - Hong Kong Baptist University
# 2022

import asyncio
import tkinter as tk
from datetime import datetime
from functools import partial
from tkinter import ttk
from tkinter.messagebox import YES, showerror, askyesno
from bleak import (
    BleakClient,
    BleakScanner,
)
from bleak.exc import BleakError

from pythonosc import udp_client
from gesture_model import GestureModel
from utils import bytearray_to_fusion_data, log_file_path


LOCAL_ADDRESS = "127.0.0.1"
UDP_PORT = 8888
UDP_CLIENT = udp_client.SimpleUDPClient(LOCAL_ADDRESS, UDP_PORT)
CHARACTERISTIC_UUID = "00E00000-0001-11E1-AC36-0002A5D5C51B"
DEVICE_NAME = "AM1V330"
AM1V330_DEVICES = {}
LOG_NAME = log_file_path()
MODEL = GestureModel()


def notification_handler(device_number:int, sender: int, data: bytearray):
    """Simple notification handler
    """
    join_array = bytearray_to_fusion_data(data)
    MODEL.tick(join_array[1:4], join_array[4:7], join_array[7:10])
    UDP_CLIENT.send_message(f"/{device_number}/raw", join_array)
    UDP_CLIENT.send_message(f"/{device_number}/quaternion", MODEL.quaternion.elements.tolist())
    UDP_CLIENT.send_message(f"/{device_number}/motion_acceleration/sensor_frame", MODEL.movement_acceleration.tolist())
    
    # with open(LOG_NAME, 'a') as f:
    #     join_str = " ".join(str(e) for e in join_array[1:])
    #     f.write(f'{device_number} {datetime.now().strftime("%Y%m%d_%H%M%S.%f")} {join_str}\n')


class Window(tk.Tk):
    def __init__(self, loop: asyncio.unix_events._UnixSelectorEventLoop):  # Delete type hint when building on Windows
        self.root = tk.Tk()
        self.root.title("Metabow OSC bridge")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_exit)
        self.loop = loop
        self.port0 = tk.StringVar()
        self.port0.set(8888)
        self.ports_frame = self.create_ports_frame(self.root)
        self.ports_frame.grid(column=0, row=0, padx=10, pady=10, sticky=tk.NW)
        self.devices_frame = self.create_scanner_frame(self.root)
        self.devices_frame.grid(column=1, row=0, padx=10, pady=10)
        self.refresh_listbox = False
        self.selected_devices_keys = []
        self.is_notify_loop = True
        self.is_destroyed = False

        try:
            self.scanner = BleakScanner(self.device_detected)
        except BleakError:
            showerror("Error", "Bluetooth device is turned off.")
            self.is_destroyed = True

    
    def on_exit(self):
        if askyesno("Exit", "Do you want to quit the application?"):
            self.is_destroyed = True


    def create_ports_frame(self, container):
        label_frame = ttk.Labelframe(container, text='UDP Ports', relief=tk.RIDGE)
        label_frame.grid(row=0, column=0, sticky=tk.W)
        title = ttk.Label(label_frame, text=f"Device Port:")
        title.grid(row=0, column=0, sticky=tk.W)
        self.port0_spinbox = ttk.Spinbox(label_frame, from_=1024, to=49151, textvariable=self.port0, width=10)
        self.port0_spinbox.grid(row=0, column=1, sticky=tk.W)
        
        # for widget in frame.winfo_children():
        #     widget.grid(padx=0, pady=5)

        return label_frame


    def items_selected(self, event):
        selected_ix = self.devices_listbox.curselection()
        selected_devices_keys = [self.devices_listbox.get(i) for i in selected_ix]
        self.selected_devices = [AM1V330_DEVICES[i] for i in selected_devices_keys]

    
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

        self.disconnect_button = ttk.Button(
            label_frame,
            text="Disconnect",
            width=10,
            command=lambda: self.loop.create_task(self.disconnect()),
        )
        self.disconnect_button.state(['disabled'])
        self.disconnect_button.grid(row=0, column=3, sticky=tk.W)

        self.devices_listbox = tk.Listbox(label_frame, width=50, selectmode='extended')
        self.devices_listbox.grid(row=1, columnspan=4, sticky=tk.W)
        self.devices_listbox.insert(0, "Please press Scan...")
        self.devices_listbox.bind('<<ListboxSelect>>', self.items_selected)
        self.devices_listbox.config(state=tk.DISABLED)

        return label_frame

    
    async def device_detected(self, device, _):
        if device.name == DEVICE_NAME:
            AM1V330_DEVICES[device.address] = device  # bleak.backends.device.BLEDevice
        await asyncio.sleep(1.0)


    async def start_scan(self):
        await self.scanner.start()
        self.devices_listbox.config(state=tk.NORMAL)
        self.devices_listbox.delete(0, 'end')
        self.start_scan_button.state(['disabled'])
        self.stop_scan_button.state(['!disabled'])
        self.connect_button.state(['disabled'])
        self.refresh_listbox = True
    

    async def stop_scan(self):
        self.start_scan_button.state(['!disabled'])
        self.stop_scan_button.state(['disabled'])
        self.connect_button.state(['!disabled'])
        self.refresh_listbox = False
        await self.scanner.stop()


    async def connect(self):
        if len(self.selected_devices) == 0:
            return
        self.is_notify_loop = True
        self.port0_spinbox.state(['disabled'])
        self.connect_button.state(['disabled'])
        self.disconnect_button.state(['!disabled'])
        self.devices_listbox.config(state=tk.DISABLED)
        await asyncio.gather(*(self.notify(i, device) for i, device in enumerate(self.selected_devices)))

    
    async def notify(self, i, device):
        async with BleakClient(device) as client:
            await client.start_notify(CHARACTERISTIC_UUID, partial(notification_handler, i))
            while self.is_notify_loop:
                await asyncio.sleep(1.0)
            await client.stop_notify(CHARACTERISTIC_UUID)


    async def disconnect(self):
        self.is_notify_loop = False
        self.port0_spinbox.state(['!disabled'])
        self.disconnect_button.state(['disabled'])
        await asyncio.sleep(1.0)


    def populate_devices(self):
        if len(AM1V330_DEVICES):
            self.devices_listbox.delete(0, 'end')

            for k, v in AM1V330_DEVICES.items():
                self.devices_listbox.insert('end', k)

    
    async def show(self):
        while not self.is_destroyed:
            if self.refresh_listbox:
                self.populate_devices()
            self.root.update()
            await asyncio.sleep(0.1)

        self.root.destroy()


class App:
    async def metabow(self):
        self.window = Window(asyncio.get_running_loop())
        await self.window.show()


if __name__ == '__main__':
    asyncio.run(App().metabow())