import asyncio

import aiofiles as aiof

import os

FILENAME = "foos.txt"



async def bad():
    mode = 'rb+' if os.path.exists(FILENAME) else 'wb+'
    out = await aiof.open(FILENAME, mode)
    await out.seek(8,0)
    await out.write(b'\x45')
    await out.seek(0,0)
    await out.write(b'\x42')
    print("done")

loop = asyncio.get_event_loop()

server = loop.run_until_complete(bad())