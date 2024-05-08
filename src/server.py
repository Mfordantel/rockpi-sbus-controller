import sys
import socketio
from aiohttp import web
import struct
import serial

from src.proto import EVENT_XY, StructXY, config_dict
from src.utils import enable_logger, init_logger
import loguru

sio = socketio.AsyncServer(async_mode="aiohttp")

uart = serial.Serial("/dev/ttyS2", baudrate=100000, timeout=0, parity=serial.PARITY_EVEN, stopbits=serial.STOPBITS_TWO, bytesize=serial.EIGHTBITS)

def generate_sbus_packet(channels):
    sbus_packet = bytearray(25)
    sbus_packet[0] = 0x0F

    for i in range(16):
        if i < len(channels):
            value = channels[i]
        else:
            value = 0
        byte_index = 1 + (i * 11 // 8)
        bit_index = (i * 11) % 8
        sbus_packet[byte_index] |= int(((value & 0x07FF) << bit_index) & 0xFF)
        sbus_packet[byte_index + 1] |= int(((value & 0x07FF) << bit_index) >> 8 & 0xFF)
        if bit_index >= 6 and i < 15:
            sbus_packet[byte_index + 2] |= int(((value & 0x07FF) << bit_index) >> 16 & 0xFF)

    sbus_packet[24] = 0x00

    return bytes(sbus_packet)

def invert_sbus_packet(sbus_packet):
    return bytes(~b & 0xFF for b in sbus_packet)

@sio.on(EVENT_XY)
async def xy_event(sid, raw_data: bytes):
    data = StructXY.model_validate(raw_data)
    channels = [data.roll, data.pitch, data.throttle, data.yaw]
    sbus_packet = generate_sbus_packet(channels)
    inverted_sbus_packet = invert_sbus_packet(sbus_packet)
    loguru.logger.info(f"Generated inverted SBUS packet: {list(inverted_sbus_packet)} ({data})")

    uart.write(inverted_sbus_packet)

@sio.on("connect")
async def on_connect(sid, *args):
    loguru.logger.info(f"{sid=} connected !")

def run_server(run_args: dict):
    app = web.Application()
    sio.attach(app)
    loguru.logger.info(
        f"Create server on host={run_args['host']}; port={run_args['port']}"
    )
    return web.run_app(app, **run_args)

def main():
    init_logger("DEBUG", enable_logger=enable_logger())
    run_server(config_dict())

if __name__ == "__main__":
    sys.exit(main())
