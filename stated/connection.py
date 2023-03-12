import asyncio
from asyncio import StreamReader
from asyncio import StreamWriter
from logging import log


async def handle_client(reader: StreamReader, writer: StreamWriter):
    data = await reader.read(100)
    message = data.decode()
    addr = writer.get_extra_info("peername")
    print(f"Received {message!r} from {addr!r}")

    print(f"Send: {message!r}")
    writer.write(data)
    await writer.drain()

    print("Close the connection")
    writer.close()
    await writer.wait_closed()


async def run_server():
    server = await asyncio.start_server(handle_client, "localhost", 9000)
    async with server:
        await server.serve_forever()


asyncio.run(run_server())
