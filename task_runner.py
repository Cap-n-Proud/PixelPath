# media_workflow/task_runner.py
import asyncio
from typing import Callable, Awaitable
import logging
from log_service import setup_logging


class TaskRunner:
    def __init__(self, config, max_concurrent=5):
        self.logger = logging.getLogger(__name__)
        self.max_concurrent = max_concurrent
        self.queue = asyncio.Queue()
        # Setup logging before using it
        setup_logging(config)  # Make sure logging is configured

        # Directly use the root logger
        self.logger = logging.getLogger()  # No need to use __name__ here

    async def add_task(self, task_func: Callable[[], Awaitable]):
        await self.queue.put(task_func)

    async def run(self):
        workers = [
            asyncio.create_task(self._worker()) for _ in range(self.max_concurrent)
        ]
        await asyncio.gather(*workers)

    async def _worker(self):
        while True:
            task_func = await self.queue.get()
            try:
                await task_func()
            except Exception as e:
                self.logger.error(f"Task failed: {e}")
            finally:
                self.queue.task_done()
