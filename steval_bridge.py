#!/usr/bin/python

# Modified by james lewis (@baldengineer)
# MIT License
# 2020
# Script to connect to Multicomp Pro MP730026 by BLE with the Bleak Module
# Based on bleak example
# Requires mpp730026_decode_bytearray.py to be in the same directory
# 
# Modified by Paulo Chiliguano (@pauloesteban)
# Directed by Dr Roberto Alonso Trillo
# Department of Music
# Hong Kong Baptist University
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
address = ("1538B1C1-75DD-4EB0-86B4-6045A5B6D44B") # for macOS

# This characteristic UUID is for the COMBINED sensors
# Accelerometer, magnetometer, gyroscope
CHARACTERISTIC_UUID = "00E00000-0001-11E1-AC36-0002A5D5C51B"

# Delay time
DELAY_TIME = 10800

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
    client.send_message("/sensortile", array)
    
    print(' '.join(map(hex, array)), end='\r')

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
        await asyncio.sleep(DELAY_TIME, loop=loop)
        await client.stop_notify(CHARACTERISTIC_UUID)


if __name__ == "__main__":
    import os
    import sys

    if len(sys.argv) >= 2:
        address = str(sys.argv[1])

    os.environ["PYTHONASYNCIODEBUG"] = str(1)
    print('MetaBow BridgeApp v0.1.0')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(address, loop, False))
