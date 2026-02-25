import asyncio
import time
import math
from collections import deque

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

        self.ahk.add_hotkey(
            Keys.SHIFT.DOWN + Keys.BACKSPACE.DOWN, self.stop, lambda x, e: print(x, e)
        )
        self.ahk.add_hotkey("F12", self.toggle_pause, lambda x, e: print(x, e))

        self.key_end_times: dict[str | Key, float] = {}
        self.pressed: dict[str | Key, bool] = {}

        self.pending_x = 0.0
        self.pending_y = 0.0

        self.consensus_trackers: dict[str, deque] = {}

    def start(self):
        self.ahk.start_hotkeys()
        self.loop.create_task(self.__mouse_movement_loop())

    def stop(self):
        print("STOP")
        self.loop.stop()

    def toggle_pause(self):
        print("PAUSE")
        self.paused.set() if self.paused.is_set() else self.paused.clear()

    async def move_mouse(self, x: int, y: int, speed: int):
        await self.ahk.mouse_move(
            x=x,
            y=y,
            speed=speed,
            blocking=False,
            relative=True,
        )

    def press_key(self, key: str | Key, duration: int | float | None):
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

    def vote_for_key(
        self,
        key: str | Key,
        required_votes: int,
        time_window: int | float,
        duration: int | float | None,
    ):
        """
        Добавляет голос за действие. Если голосов достаточно за указанное время — нажимает кнопку.

        :param key: Кнопка для нажатия (например, "tab")
        :param required_votes: Сколько команд нужно для срабатывания (например, 10)
        :param time_window: За какое время (в секундах) (например, 5.0)
        :param duration: Сколько держать кнопку (None или 0 = просто клик)
        """
        now = time.time()

        if key not in self.consensus_trackers:
            self.consensus_trackers[key] = deque()

        tracker = self.consensus_trackers[key]

        tracker.append(now)

        while tracker and tracker[0] < now - time_window:
            tracker.popleft()

        print(f"Голоса за {key}: {len(tracker)} / {required_votes}")

        if len(tracker) >= required_votes:
            print(f"Консенсус достигнут! Выполняем {key}.")
            tracker.clear()

            self.press_key(key, duration)
            return True

        return False

    async def __click_key(self, key: str | Key):
        # Чтобы не отпускать зажатую клавишу
        if not self.pressed.get(key, False):
            if key in Keys._MOUSE_BUTTONS:
                await self.ahk.click(button=key)
            else:
                await self.ahk.key_press(key, release=True)

    async def __key_release_loop(self, key: str | Key):
        if key in Keys._MOUSE_BUTTONS:
            await self.ahk.click(button=key, direction="D")
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
        if key in Keys._MOUSE_BUTTONS:
            await self.ahk.click(button=key, direction="U")
        else:
            await self.ahk.key_up(key)
        self.pressed[key] = False

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
