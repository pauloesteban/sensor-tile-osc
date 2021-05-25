import asyncio
from bleak import discover
import time

async def run():
    devices = await discover()
    for d in devices:
        print(d)

while True:
	loop = asyncio.get_event_loop()
	loop.run_until_complete(run())
	time.sleep(1)