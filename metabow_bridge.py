#!/usr/bin/python

# Developed by Paulo Chiliguano and KA HO Wong
# Directed by Dr Roberto Alonso Trillo
# HKBU Academy of Music
# 2024

import asyncio
import csv
import struct
import threading
import tomllib
import tkinter as tk
from datetime import datetime
from functools import partial
from pathlib import Path
from tkinter import ttk
from tkinter.messagebox import showerror, askyesno
from bleak import (
    BleakClient,
    BleakScanner,
)
from bleak.exc import BleakError
from pythonosc import udp_client
from gesture_model import GestureModel
from utils import bytearray_to_fusion_data, log_file_path, pyquaternion_as_spherical_coords


class FusionThread(threading.Thread):
    def __init__(self, target, args=()):
        super().__init__(target=target, args=args)
        self._fusion_data = None

    def run(self):
        self._fusion_data = self._target(self._args)

    def get_fusion_data(self):
        return self._fusion_data


class Window(tk.Tk):
    def __init__(self, loop):
        self.root = tk.Tk()
        self.root.title("Metabow OSC bridge")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_exit)
        self.loop = loop
        self.port0 = tk.IntVar()
        self.port0.set(8888)
        self.port1 = tk.IntVar()
        self.port1.set(8889)
        self.ports_frame = self.create_ports_frame(self.root)
        self.ports_frame.grid(column=0, row=0, padx=10, pady=10, sticky=tk.NW)
        self.devices_frame = self.create_scanner_frame(self.root)
        self.devices_frame.grid(column=1, row=0, padx=10, pady=10)
        self.option_address = tk.StringVar()
        self.option_address.set(0)
        self.options_frame = self.create_options_frame(self.root)
        self.options_frame.grid(column=0, row=1, padx=10, pady=10, sticky=tk.NW)
        self.animation = "░▒▒▒▒▒▒▒▒▒"
        self.monitoring_frame = self.create_monitoring_frame(self.root)
        self.monitoring_frame.grid(column=1, row=1, padx=10, pady=10, sticky=tk.NW)
        self.refresh_listbox = False
        self.selected_devices_keys = []
        self.is_notify_loop = False
        self.is_destroyed = False
        self.configuration_path = Path("metabow.toml")
        try:
            self.configuration_dict = tomllib.loads(self.configuration_path.read_text())
        except Exception as e:
            self.configuration_dict = {
                'device': {
                    'characteristic-uuid': "6e400003-b5a3-f393-e0a9-e50e24dcca9e",
                    'name': "metabow"
                    }
                }
        self.characteristic_uuid = self.configuration_dict['device']['characteristic-uuid']
        self.device_name = self.configuration_dict['device']['name']
        self.IMU_devices = {}
        self.model = GestureModel()
        self._instantiate_scanner()
        self.csv_header = [
            'ID',
            'timestamp',
            'accl_x',
            'accl_y',
            'accl_z',
            'gyro_x',
            'gyro_y',
            'gyro_z',
            'magn_x',
            'magn_y',
            'magn_z',
            'q_w',
            'q_x',
            'q_y',
            'q_z',
            'accl_sensor_frame_x',
            'accl_sensor_frame_y',
            'accl_sensor_frame_z',
            'accl_derivative_x',
            'accl_derivative_y',
            'accl_derivative_z',
            'accl_vel_x',
            'accl_vel_y',
            'accl_vel_z',
            'accl_skewness',
            'accl_tilt',
            'accl_roll'
        ]
        self.DATA_POINT_SIZE = 4  # NOTE: Corresponds to floating-point standard size in bytes
        self.NORDIC_IMU_SENSOR_DATA_POINTS = 13
        self.NORDIC_IMU_SENSOR_DATA_LEN = self.NORDIC_IMU_SENSOR_DATA_POINTS * self.DATA_POINT_SIZE
        self.NORDIC_IMU_FLAG_SIZE = 1
        self.NORDIC_IMU_PACK_FORMAT = 'f' * self.NORDIC_IMU_SENSOR_DATA_POINTS


    def _instantiate_scanner(self):
        try:
            self.scanner = BleakScanner(self.device_detected)
        except BleakError:
            showerror("Error", "Bluetooth device is turned off.")
            self.is_destroyed = True


    def _instantiate_udp_client(self):
        localhost = "127.0.0.1"
        self.udp_client = udp_client.SimpleUDPClient(localhost,
                                                     self.port0.get())
        self.udp_client_mirror = udp_client.SimpleUDPClient(localhost,
                                                            self.port1.get())


    def on_exit(self):
        if askyesno("Exit", "Do you want to quit the application?"):
            self.is_destroyed = True


    def create_ports_frame(self, container):
        label_frame = ttk.Labelframe(container, text='UDP Ports', relief=tk.RIDGE)
        label_frame.grid(row=0, column=0, sticky=tk.W)
        title = ttk.Label(label_frame, text="Device Port:")
        title.grid(row=0, column=0, sticky=tk.W)
        self.port0_spinbox = ttk.Spinbox(label_frame,
                                         from_=1024,
                                         to=49151,
                                         textvariable=self.port0,
                                         width=10)
        self.port0_spinbox.grid(row=0, column=1, sticky=tk.W)
        title1 = ttk.Label(label_frame, text="Mirror Port:")
        title1.grid(row=1, column=0, sticky=tk.W)
        self.port1_spinbox = ttk.Spinbox(label_frame,
                                         from_=1024,
                                         to=49151,
                                         textvariable=self.port1,
                                         width=10)
        self.port1_spinbox.grid(row=1, column=1, sticky=tk.W)

        return label_frame


    def create_options_frame(self, container):
        label_frame = ttk.Labelframe(container, text='Options', relief=tk.RIDGE)
        label_frame.grid(row=0, column=0, sticky=tk.W)
        self.address_checkbox = ttk.Checkbutton(label_frame, text="Use Device Identifier for OSC", variable=self.option_address)
        self.address_checkbox.grid(row=0, column=0, sticky=tk.W)

        return label_frame


    def create_monitoring_frame(self, container):
        label_frame = ttk.Labelframe(container, text='Monitoring', relief=tk.RIDGE)
        label_frame.grid(row=0, column=0, sticky=tk.W)
        self.monitoring_label = ttk.Label(label_frame, text="")
        self.monitoring_label.grid(row=0, column=0, sticky=tk.W)
        self.monitoring_label.state(['disabled'])

        return label_frame


    def items_selected(self, event):
        selected_ix = self.devices_listbox.curselection()
        selected_devices_keys = [self.devices_listbox.get(i) for i in selected_ix]
        self.selected_devices = [self.IMU_devices[i] for i in selected_devices_keys]


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
        if device.name == self.device_name:
            self.IMU_devices[device.address] = device  # bleak.backends.device.BLEDevice
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
        self.port1_spinbox.state(['disabled'])
        self.address_checkbox.state(['disabled'])
        self._instantiate_udp_client()
        self.start_scan_button.state(['disabled'])
        self.connect_button.state(['disabled'])
        self.disconnect_button.state(['!disabled'])
        self.devices_listbox.config(state=tk.DISABLED)
        self.monitoring_label.state(['!disabled'])
        self._create_csv_file()
        await asyncio.gather(*(self.notify_nordic(i, device) for i, device in enumerate(self.selected_devices)))


    async def notify_nordic(self, i, device):
        """
        This is similar as self.notify except it has not been tested for simultaneous devices
        """
        async with BleakClient(device) as client:
            while not client.is_connected:
                await asyncio.sleep(0.1)
            if self.option_address.get() == "0":
                await client.start_notify(self.characteristic_uuid, partial(self.notification_handler_for_nordic, i))
            elif self.option_address.get() == "1":
                await client.start_notify(self.characteristic_uuid, partial(self.notification_handler_for_nordic, str(device.address)))
            while self.is_notify_loop:
                await asyncio.sleep(1.0)
            await client.stop_notify(self.characteristic_uuid)


    async def notify(self, i, device):
        async with BleakClient(device) as client:
            if self.option_address.get() == "0":
                await client.start_notify(self.characteristic_uuid, partial(self.notification_handler, i))
            elif self.option_address.get() == "1":
                await client.start_notify(self.characteristic_uuid, partial(self.notification_handler, str(device.address)))
            while self.is_notify_loop:
                await asyncio.sleep(1.0)
            await client.stop_notify(self.characteristic_uuid)


    async def disconnect(self):
        self.is_notify_loop = False
        self.port0_spinbox.state(['!disabled'])
        self.port1_spinbox.state(['!disabled'])
        self.disconnect_button.state(['disabled'])
        self.start_scan_button.state(['!disabled'])
        self.address_checkbox.state(['!disabled'])
        self.monitoring_label.state(['disabled'])
        await asyncio.sleep(1.0)


    async def notification_handler_for_nordic(self, device_number: int | str, sender: int, data: bytearray):
        """
        Async callback for Nordic IMU
        """
        data_len = len(data)  # TODO: Once the value is fixed on the board, assign as a constant in the constructor
        upper_limit = data_len - self.NORDIC_IMU_FLAG_SIZE
        lower_limit = upper_limit - self.NORDIC_IMU_SENSOR_DATA_LEN

        if data[upper_limit] == 1:  # NOTE: We check the flag value
            sensor_data_unpacked = struct.unpack(
                self.NORDIC_IMU_PACK_FORMAT,
                data[lower_limit:upper_limit]
            )
            address_raw = f"/{device_number}/raw"
            self.udp_client.send_message(address_raw, sensor_data_unpacked)
        
        await asyncio.sleep(0.1)
    

    def notification_handler(self, device_number: int | str, sender: int, data: bytearray):
        """Simple notification handler
        """
        fusion_thread = FusionThread(target=bytearray_to_fusion_data,
                                     args=data)
        fusion_thread.start()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S.%f")
        address_raw = f"/{device_number}/raw"
        fusion_thread.join()
        fusion_data = fusion_thread.get_fusion_data()
        model_thread = threading.Thread(target=self.model.tick,
                                        args=(fusion_data[1:4],
                                              fusion_data[4:7],
                                              fusion_data[7:10]))
        model_thread.start()
        self.udp_client.send_message(address_raw, fusion_data)
        self.udp_client_mirror.send_message(address_raw, fusion_data)
        model_thread.join()
        write_thread = threading.Thread(target=self._write_log,
                                        args=(timestamp, device_number, fusion_data, self.model))
        write_thread.start()

        if self.port0 != self.port1:
            send_mirror_thread = threading.Thread(target=self._send_messages,
                                                args=(device_number, self.udp_client_mirror, self.model))
            send_mirror_thread.start()
            self._send_messages(device_number, self.udp_client, self.model)
            send_mirror_thread.join()
        else:
            self._send_messages(device_number, self.udp_client, self.model)
        write_thread.join()


    def _write_log(self, timestamp, device_number, fusion_data, model):
        data = [device_number,
                timestamp,
                *fusion_data[1:],
                *model.quaternion.elements.tolist(),
                *model.movement_acceleration.tolist(),
                *model.acceleration_derivative.tolist(),
                *model.movement_velocity.tolist(),
                model.skewness,
                model.tilt,
                model.roll]

        with open(self.log_name, 'a', encoding='UTF8') as f:
            writer = csv.writer(f)
            writer.writerow(data)


    def _send_messages(self, device_number, udp_client, model):
        address_quaternion = f"/{device_number}/quaternion"
        elements = model.quaternion.elements
        quaternion = elements.tolist()
        udp_client.send_message(address_quaternion, quaternion)
        spherical_coords = pyquaternion_as_spherical_coords(elements)
        udp_client.send_message(f"/{device_number}/spherical_coords", spherical_coords.tolist())
        address_sensor_frame = f"/{device_number}/motion_acceleration/sensor_frame"
        movement_accl = model.movement_acceleration.tolist()
        udp_client.send_message(address_sensor_frame, movement_accl)
        address_sensor_derivative = f"/{device_number}/motion_acceleration/sensor_derivative"
        accl_derivative = model.acceleration_derivative.tolist()
        udp_client.send_message(address_sensor_derivative, accl_derivative)
        address_sensor_velocity = f"/{device_number}/motion_acceleration/sensor_velocity"
        movement_vel = model.movement_velocity.tolist()
        udp_client.send_message(address_sensor_velocity, movement_vel)
        address_sensor_skewness = f"/{device_number}/motion_acceleration/skewness"
        skewness = model.skewness
        udp_client.send_message(address_sensor_skewness, skewness)
        address_sensor_tilt = f"/{device_number}/motion_acceleration/tilt"
        tilt = model.tilt
        udp_client.send_message(address_sensor_tilt, tilt)
        address_sensor_roll = f"/{device_number}/motion_acceleration/roll"
        roll = model.roll
        udp_client.send_message(address_sensor_roll, roll)


    def populate_devices(self):
        if len(self.IMU_devices):
            self.devices_listbox.delete(0, 'end')

            for k, v in self.IMU_devices.items():
                self.devices_listbox.insert('end', k)


    def _create_csv_file(self):
        self.log_name = log_file_path()
        with open(self.log_name, 'w', encoding='UTF8') as f:
            writer = csv.writer(f)
            writer.writerow(self.csv_header)


    async def show(self):
        while not self.is_destroyed:
            if self.refresh_listbox:
                self.populate_devices()
            if self.is_notify_loop:
                self.monitoring_label["text"] = self.animation
                self.animation = self.animation[-1] + self.animation[:-1]
            self.root.update()
            await asyncio.sleep(0.1)

        self.root.destroy()


class App:
    async def metabow(self):
        self.window = Window(asyncio.get_running_loop())
        await self.window.show()


if __name__ == '__main__':
    asyncio.run(App().metabow())
