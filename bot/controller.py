import asyncio
import time
import math

from ahk import AsyncAHK
from ahk.keys import KEYS, Key


class Keys(KEYS):
    LMB = "left"
    RMB = "right"
    LEFT_MOUSE_BUTTON = LMB
    RIGHT_MOUSE_BUTTON = RMB
    LeftMouseButton = LMB
    RightMouseButton = RMB

    _MOUSE_BUTTONS = {LMB, RMB, LEFT_MOUSE_BUTTON, RIGHT_MOUSE_BUTTON}


class Direction:
    UP = "up"
    Up = UP
    DOWN = "down"
    Down = DOWN
    LEFT = "left"
    Left = LEFT
    RIGHT = "right"
    Right = RIGHT


class Controller:
    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        paused: asyncio.Event,
        mouse_speed: int = 10,
    ):
        self.loop = loop
        self.paused = paused
        self.mouse_speed = mouse_speed

        self.ahk = AsyncAHK()

        self.ahk.add_hotkey(Keys.SHIFT + Keys.BACKSPACE, self.stop)
        self.ahk.add_hotkey("F12", self.toggle_pause)

        self.key_end_times: dict[str | Key, float] = {}
        self.pressed: dict[str | Key, bool] = {}
        self.queues: dict[str | Key, asyncio.Queue] = {}

    async def toggle_pause(self):
        self.paused.set() if self.paused.is_set() else self.paused.clear()

    async def move_mouse(self, x: int, y: int, speed: int):
        await self.ahk.mouse_move(
            x=x,
            y=y,
            speed=speed,
            blocking=False,
            relative=True,
        )

    def press_and_extend_key(self, key: str | Key, duration: int | float | None):
        if not duration:
            self.loop.create_task(self.__click_key(key))
            return

        now = time.time()

        if key in self.key_end_times and self.key_end_times[key] > now:
            self.key_end_times[key] += duration
            print(
                f"Продлеваем {key}. Осталось держать: {self.key_end_times[key] - now:.1f} сек."
            )
        else:
            self.key_end_times[key] = now + duration
            print(f"Зажимаем {key} на {duration} сек.")

            self.loop.create_task(self.__key_release_loop(key))

    def add_mouse_movement(self, dx: int, dy: int):
        self.pending_x += dx
        self.pending_y += dy

    async def __click_key(self, key: str | Key):
        # Чтобы не отпускать зажатую клавишу
        if not self.pressed[key]:
            await self.ahk.key_press(key, release=True)

    async def __key_release_loop(self, key: str | Key):
        if key in Keys._MOUSE_BUTTONS:
            await self.ahk.mouse_click(button=key)
        else:
            await self.ahk.key_down(key)
        self.pressed[key] = True

        while True:
            now = time.time()
            remaining_time = self.key_end_times[key] - now

            if remaining_time <= 0:
                break

            await asyncio.sleep(remaining_time)
        print(f"Отпускаем {key}.")
        await self.ahk.key_up(key)

        if key in self.key_end_times:
            del self.key_end_times[key]

    async def __mouse_movement_loop(self):
        """
        Фоновый цикл, который плавно поворачивает камеру.
        """
        # tick_rate - задержка цикла. 0.016 ~ это 60 FPS
        tick_rate = 0.016

        while True:
            if abs(self.pending_x) > 0 or abs(self.pending_y) > 0:

                length = math.hypot(self.pending_x, self.pending_y)

                if length <= self.mouse_speed:
                    step_x = int(self.pending_x)
                    step_y = int(self.pending_y)
                    self.pending_x = 0.0
                    self.pending_y = 0.0
                else:
                    ratio = self.mouse_speed / length
                    step_x = int(self.pending_x * ratio)
                    step_y = int(self.pending_y * ratio)

                    self.pending_x -= step_x
                    self.pending_y -= step_y

                await self.ahk.mouse_move(
                    x=step_x, y=step_y, speed=0, blocking=False, relative=True
                )

            await asyncio.sleep(tick_rate)
