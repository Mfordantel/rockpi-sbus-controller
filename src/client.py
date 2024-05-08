import asyncio
import sys
from functools import partial
from random import randint
from typing import AsyncGenerator
import loguru
import socketio
import pygame
from pygame.locals import *
from src.proto import EVENT_XY, TASK_PERIOD, StructXY, clinet_config
from src.utils import Task, enable_logger, get_task_queue, init_logger

rand_int = partial(randint, -10000, 10000)

class joystick_handler(object):
    def __init__(self, id):
        self.id = id
        self.joy = pygame.joystick.Joystick(id)
        self.name = self.joy.get_name()
        self.joy.init()
        self.numaxes = min(4, self.joy.get_numaxes())
        self.axes = [0.0] * self.numaxes

    def update(self):
        pygame.event.pump()
        for i in range(self.numaxes):
            self.axes[i] = round(self.joy.get_axis(i), 3)

async def get_xy_data() -> StructXY:
    pygame.init()
    joy = joystick_handler(0)
    joy.update()
    roll, pitch, throttle, yaw = [(axis + 1) * 818 + 173 for axis in joy.axes]
    return StructXY(int(roll), int(pitch), int(throttle), int(yaw))

async def xy_task_generator():
    task_queue = get_task_queue()
    while True:
        data = await get_xy_data()
        send_data = data.model_dump()
        loguru.logger.debug(f"Create Task_XY: ({data})")
        task_queue.put(Task(EVENT_XY, send_data))
        await asyncio.sleep(TASK_PERIOD)

async def get_task() -> AsyncGenerator[Task, None]:
    task_queue = get_task_queue()
    while True:
        data = next(task_queue.get_task())
        if not data:
            await asyncio.sleep(TASK_PERIOD)
            continue
        yield data

async def manage_forever():
    config = clinet_config()
    async with socketio.AsyncSimpleClient(
        reconnection_delay=1, reconnection_delay_max=2
    ) as sio:
        loguru.logger.info(f"Connecting to url=`{config['url']}`")
        await sio.connect(**config)
        async for task in get_task():
            await sio.emit(task.event, task.data)

async def main_client():
    while True:
        try:
            await manage_forever()
        except InterruptedError:
            sys.exit(0)
        except Exception as e:
            loguru.logger.error(str(e))
            loguru.logger.warning("Reconnecting...")
        finally:
            await asyncio.sleep(2)

def main():
    init_logger("DEBUG", enable_logger=enable_logger())
    async def _main():
        asyncio.create_task(xy_task_generator())
        await main_client()
    asyncio.run(_main())

if __name__ == "__main__":
    main()
