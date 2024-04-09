from dataclasses import dataclass
from functools import cache
from os import getenv
import struct
from typing import Protocol


def config_dict():
    return dict(
        host=getenv("HOST", "0.0.0.0"),
        port=int(getenv("PORT", "8100")),
        keepalive_timeout=int(getenv("KEEPALIVE_TIMEOUT", "4")),
    )


def clinet_config():
    conf = config_dict()
    client_host = getenv("CLIENT_HOST", "localhost")
    return dict(
        url=f"ws://{client_host}:{conf['port']}",
        transports=["websocket", "polling"],
        wait_timeout=2,
    )


TASK_PERIOD = 0.00001

EVENT_XY = "xy"


class IStruct(Protocol):

    @classmethod
    def __schema(cls) -> str:
        pass

    def model_dump(self) -> bytes:
        pass

    @classmethod
    def model_validate(cls, data: bytes):
        pass


@dataclass
class StructXY:
    roll: int
    pitch: int
    throttle: int
    yaw: int

    @classmethod
    @cache
    def __schema(cls) -> str:
        return ">qqqq"

    def model_dump(self) -> bytes:
        return struct.pack(self.__schema(), self.roll, self.pitch, self.throttle, self.yaw)

    @classmethod
    def model_validate(cls, data: bytes):
        values = struct.unpack(cls.__schema(), data)
        return cls(*values)
