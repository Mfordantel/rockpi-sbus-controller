from dataclasses import dataclass
from functools import cache
from os import getenv
from queue import Queue
import sys
from typing import Generator
from loguru import logger


LOGGER_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)


def enable_logger():
    return getenv("LOGGER_ENABLE", "1") == "1"


def init_logger(
    log_level: str, log_path: str | None = None, enable_logger: bool = True
) -> None:
    logger.remove()

    if enable_logger:
        logger.add(
            sys.stderr, colorize=True, format=LOGGER_FORMAT, level=log_level
        )
        if log_path:
            logger.add(
                log_path,
                level=log_level,
                format=LOGGER_FORMAT,
                rotation="16 MB",
                compression="zip",
                serialize=True,
            )


@dataclass
class Task:
    event: str
    data: bytes


class TaskQueue:
    def __init__(self) -> None:
        self.__task_queue: list[Task] = list()

    def get_task(self) -> Generator[Task, None, None]:
        try:
            task = self.__task_queue.pop(0)
            yield task
        except IndexError:
            yield None

    def put(self, task: Task):
        if len(self.__task_queue) <= 100:
            self.__task_queue.append(task)


@cache
def get_task_queue():
    return TaskQueue()
