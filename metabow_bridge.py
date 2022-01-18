#!/usr/bin/python

# Based on bleak example
# Modified by james lewis (@baldengineer)
# MIT License
# 2020
# 
# Modified by Paulo Chiliguano (@pauloesteban)
# Directed by Dr Roberto Alonso Trillo
# Department of Music - Hong Kong Baptist University
# 2021


import asyncio

from bleak import (
    BleakClient,
    discover,
)

from pythonosc import udp_client


simple_udp_client = udp_client.SimpleUDPClient("127.0.0.1", 8888)
CHARACTERISTIC_UUID = "00E00000-0001-11E1-AC36-0002A5D5C51B"
DELAY_TIME = 10800


def notification_handler(sender, data, debug=False):
    """Simple notification handler
    """
    join_array = [int.from_bytes(data[i:i+2], byteorder='little', signed=True) for i in range(0, len(data) - 1, 2)]
    simple_udp_client.send_message("/0/raw", join_array)


async def discover_steval():
    await asyncio.sleep(1)
    devices = await discover()
    print(devices)
    for d in devices:
        print(d.address)
        if d.name == "AM1V330":
            return d.address

async def main():
    while True:
        address = await discover_steval()
        
        if address:
            print("\033[92mYou are connected to AM1V330 (STEVAL)!")
            break

    async with BleakClient(str(address)) as client:
        await client.start_notify(CHARACTERISTIC_UUID, notification_handler)
        await asyncio.sleep(DELAY_TIME)
        await client.stop_notify(CHARACTERISTIC_UUID)


if __name__ == '__main__':
    asyncio.run(main())