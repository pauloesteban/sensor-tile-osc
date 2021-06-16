import asyncio
import platform

from bleak import BleakClient


async def print_services(mac_addr: str):
    async with BleakClient(mac_addr) as client:
        svcs = await client.get_services()
        print("Services:")
        for service in svcs:
            print(service)


mac_addr = (
    "24:71:89:cc:09:05"
    if platform.system() != "Darwin"
    else "590E8F0B-DD3C-4A35-9889-755DCA9D66B9"
)
loop = asyncio.get_event_loop()
loop.run_until_complete(print_services(mac_addr))