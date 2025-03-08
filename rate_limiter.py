import asyncio
import time
import os

class RateLimiter:
    def __init__(self):
        self.locks: dict[int, asyncio.Lock] = {}
        self.cooldowns: dict[tuple[int, str], float] = {}
        self.upcoming_acquire: tuple[int, str, float] = None
        self.running_aquires: set[int] = set()

    async def acquire(self, user_id: int, command: str, cooldown: float):
        now = time.monotonic()
        key = (user_id, command)
        if user_id not in self.locks:
            self.locks[user_id] = asyncio.Lock()

        if key in self.cooldowns:
            if self.cooldowns[key] >= now:
                return True

        await self.locks[user_id].acquire()

        self.cooldowns[key] = now + cooldown
        return False

    async def release(self, user_id: int):
        if user_id in self.locks and self.locks[user_id].locked():
            self.locks[user_id].release()
