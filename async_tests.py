import asyncio

i = 0


class SampleAsyncClass:

    def __init__(self):
        asyncio.ensure_future(self._start())

    async def _start(self):
        global i
        print('Inside function', i)
        i = i + 1
        j = i
        await asyncio.sleep(1)
        print('Finished',j)
        return None

async def main():
    print('Inside async function')

    instances = [SampleAsyncClass() for i in range(2)]

    print('Now going outside main function')
    
    await asyncio.sleep(5)

    return None

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()


# import asyncio

# async def slow_operation(future):
#     await asyncio.sleep(1)
#     future.set_result('Future is done!')
# async def main():
#     future = asyncio.Future()
#     asyncio.ensure_future(slow_operation(future))
#     return future


# loop = asyncio.get_event_loop()
# loop.run_until_complete(main())
# loop.close()


# import asyncio

# async def async_foo():
#     print("async_foo started")
#     await asyncio.sleep(5)
#     print("async_foo done")

# async def main():
#     asyncio.ensure_future(async_foo())  # fire and forget async_foo()
#     print('Do some actions 1')
#     # await asyncio.sleep(5)
#     print('Do some actions 2')

# loop = asyncio.get_event_loop()
# loop.run_until_complete(main())