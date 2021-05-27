#!/usr/bin/python

# Modified by james lewis (@baldengineer)
# MIT License
# 2020
# Script to connect to Multicomp Pro MP730026 by BLE with the Bleak Module
# Based on bleak example
# Requires mpp730026_decode_bytearray.py to be in the same directory
# 
# Modified by Paulo Chiliguano (@pauloesteban)
# 2021

import logging
import asyncio
# import platform
# from mp730026_decode_bytearray import print_DMM_packet

from bleak import BleakClient
from bleak import _logger as logger

from pythonosc import udp_client


client = udp_client.SimpleUDPClient("127.0.0.1", 7400)

# Change this to your meter's address
address = ("590E8F0B-DD3C-4A35-9889-755DCA9D66B9") # for macOS

# This characteristic UUID is for the Heart Rate BLE message
CHARACTERISTIC_UUID = "00400000-0001-11e1-ac36-0002a5d5c51b"

def notification_handler(sender, data, debug=False):
    """Simple notification handler which prints the data received.
    """
    #print("{0}: {1}".format(sender, data))
    if (debug): print("Handling...")
    if (debug): print("Data is " + str(type(data)))
    

    array = bytearray(data)
    
    if (debug): print(str(sender) + " : ", end="")
    if (debug): 
        for arr in array:
            print(hex(arr))
        print("")
    if (debug): print("... done handling")
    # print_DMM_packet(array)
    client.send_message("/gyro", array)
    for arr in array:
        print(hex(arr), end=" ")
    print("\r")

async def run(address, loop, debug=False):
    if debug:
        import sys

        # loop.set_debug(True)
        l = logging.getLogger("asyncio")
        l.setLevel(logging.DEBUG)
        h = logging.StreamHandler(sys.stdout)
        h.setLevel(logging.DEBUG)
        l.addHandler(h)
        logger.addHandler(h)

    async with BleakClient(address, loop=loop) as client:
        x = await client.is_connected()
        logger.info("Connected: {0}".format(x))

        await client.start_notify(CHARACTERISTIC_UUID, notification_handler)
        await asyncio.sleep(460.0, loop=loop)
        await client.stop_notify(CHARACTERISTIC_UUID)


if __name__ == "__main__":
    import os
    import sys

    if len(sys.argv) >= 2:
        address = str(sys.argv[1])

    os.environ["PYTHONASYNCIODEBUG"] = str(1)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(address, loop, False))
