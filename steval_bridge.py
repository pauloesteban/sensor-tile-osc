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
import os
os.environ['PYTHONASYNCIODEBUG'] = "1"
import asyncio
# import platform
# from mp730026_decode_bytearray import print_DMM_packet

from bleak import BleakClient
from bleak import _logger as logger

from pythonosc import udp_client


client = udp_client.SimpleUDPClient("127.0.0.1", 8888)

# Change this to your meter's address
address = ("2BAD5FC0-A19B-4CA9-96C2-8A1BE352D5BD") # for macOS

# This characteristic UUID is for the COMBINED sensors
# Accelerometer, magnetometer, gyroscope
CHARACTERISTIC_UUID = "00E00000-0001-11E1-AC36-0002A5D5C51B"

# Delay time
DELAY_TIME = 10800

def notification_handler(sender, data, debug=False):
    """Simple notification handler which prints the data received.
    """
    array = bytearray(data)
    #print("{0}: {1}".format(sender, data))
    if debug:
        print("Handling...")
        print("Data is " + str(type(data)))
        print(str(sender) + " : ", end="")
    # print(' '.join(map(hex, array)), end='\r')
        #print("... done handling")
    join_array = [int.from_bytes(data[i:i+2], byteorder='little', signed=True) for i in range(0, len(data) - 1, 2)]

    # print_DMM_packet(array)
    client.send_message("/0/raw", join_array)
    
    

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
    import argparse
    parser = argparse.ArgumentParser()
    if len(sys.argv) >= 2:
        address = str(sys.argv[1])

    print('MetaBow BridgeApp v0.2.0')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(address, loop, True))
