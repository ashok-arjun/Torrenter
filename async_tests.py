# import asyncio

# i = 0


# class SampleAsyncClass:

#     def __init__(self):
#         asyncio.ensure_future(self._start())

#     async def _start(self):
#         global i
#         print('Inside function', i)
#         i = i + 1
#         j = i
#         await asyncio.sleep(1)
#         print('Finished',j)
#         return None

# async def main():
#     print('Inside async function')

#     instances = [SampleAsyncClass() for i in range(2)]

#     print('Now going outside main function')
    
#     await asyncio.sleep(5)

#     return None

# loop = asyncio.get_event_loop()
# loop.run_until_complete(main())
# loop.close()








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












# import asyncio

# async def handle_echo(reader, writer):
#     data = await reader.read(100)
#     message = data.decode()
#     addr = writer.get_extra_info('peername')
#     print("Received %r from %r" % (message, addr))

#     print("Send: %r" % message)
#     writer.write(data)
#     await writer.drain()

#     print("Close the client socket")
#     writer.close()

# loop = asyncio.get_event_loop()
# coro = asyncio.start_server(handle_echo, '127.0.0.1', 8888, loop=loop)
# server = loop.run_until_complete(coro)

# # Serve requests until Ctrl+C is pressed
# print('Serving on {}'.format(server.sockets[0].getsockname()))
# try:
#     loop.run_forever()
# except KeyboardInterrupt:
#     pass

# # Close the server
# server.close()
# loop.run_until_complete(server.wait_closed())
# loop.close()



# import asyncio

# async def wait_for_data(loop):

#     # Register the open socket to wait for data
#     reader, writer = await asyncio.open_connection(63.210.25.139, 6884)

#     print('Connected')


# loop = asyncio.get_event_loop()
# loop.run_until_complete(wait_for_data(loop))
# loop.close()


import asyncio

class Foo(object):
    def __init__(self):
        self.state = 0

    def __aiter__(self):
        return self

    def __anext__(self):
        def later():
            try:
                print(f'later: called when state={self.state}')

                self.state += 1
                if self.state == 3:
                    future.set_exception(StopAsyncIteration())
                else:
                    future.set_result(self.state)
            finally:
                print(f'later: left when state={self.state}')

        print(f'__anext__: called when state={self.state}')
        try:
            future = asyncio.Future()

            loop.call_later(0.1, later)

            return future
        finally:
            print(f'__anext__: left when state={self.state}')

async def main():
    print('==== async for ====')
    foo = Foo()
    async for x in foo:
        print('>', x)

    print('==== __anext__() ====')
    foo = Foo()
    a = foo.__anext__()
    b = foo.__anext__()
    c = foo.__anext__()
    print('>', await a)
    print('>', await b)
    print('>', await c)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.run_until_complete(asyncio.gather(*asyncio.Task.all_tasks()))
loop.close()