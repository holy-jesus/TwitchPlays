from twitchAPI.chat import ChatMessage
import asyncio
import functools
from typing import Callable

from aiohttp.helpers import sentinel
from ahk import AsyncAHK
from ahk.keys import Key
from twitchAPI.type import ChatEvent
from twitchAPI.chat import Chat, EventData, ChatCommand
from twitchAPI.chat.middleware import ChannelUserCommandCooldown, BaseCommandMiddleware

from .controller import Controller, Direction, Keys


class FakeUser:
    login = "justinfan1337"


class FakeTwitch:
    session_timeout = sentinel

    async def get_refreshed_user_auth_token():
        return "kappa"

    def has_required_auth(*args, **kwargs):
        return True

    async def get_users():
        while True:
            yield FakeUser


class ActiveWindowMiddleware(BaseCommandMiddleware):
    def __init__(self, ahk: AsyncAHK, process_name: str):
        self.process_name = process_name
        self.ahk = ahk

    async def can_execute(self, cmd: ChatCommand):
        if self.process_name == "*":
            return True
        active_window = await self.ahk.get_active_window()
        if (
            active_window
            and await active_window.get_process_name() == self.process_name
        ):
            return True
        return False

    async def was_executed(self, cmd: ChatCommand):
        pass


class PausedMiddleware(BaseCommandMiddleware):
    def __init__(self, paused: asyncio.Event):
        self.paused = paused

    async def can_execute(self, cmd: ChatCommand):
        if self.paused.is_set():
            return False
        return True

    async def was_executed(self, cmd: ChatCommand):
        pass


class OnlyModsMiddleware(BaseCommandMiddleware):
    async def can_execute(self, command: ChatCommand):
        return command.room.name == command.user.name or command.user.mod

    async def was_executed(self, cmd: ChatCommand):
        pass


class Bot:
    def __init__(
        self,
        channel: str,
        process: str,
        /,
        mouse_speed: int = 15,
        prefix: str = "!",
        cooldown: int = 6,
        loop: asyncio.AbstractEventLoop | None = None,
    ):
        self.channel = channel
        self.process = process
        self.cooldown = cooldown

        if loop is None:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

        self.loop = loop

        self.paused = asyncio.Event()
        self.controller = Controller(self.loop, self.paused, mouse_speed)

        self.chat = Chat(FakeTwitch)

        self.chat.set_prefix(prefix)

        self.chat.register_command_middleware(
            ActiveWindowMiddleware(self.controller.ahk, self.process)
        )
        self.chat.register_command_middleware(PausedMiddleware(self.paused))

        self.chat.register_event(ChatEvent.READY, self.__on_ready)
        self.chat.register_event(ChatEvent.JOINED, self.__on_joined)
        self.chat.register_event(ChatEvent.MESSAGE, self.__on_message)

    def run(self):
        try:
            self.loop.run_until_complete(self.start())
            self.loop.run_forever()
        except KeyboardInterrupt:
            self.loop.run_until_complete(self.stop())
        except asyncio.CancelledError:
            self.loop.run_until_complete(self.stop())

    async def start(self):
        self.controller.start()
        await self.chat  # bruh
        self.chat.start()

    async def stop(self):
        self.chat.stop()
        self.loop.stop()

    async def toggle_pause(self):
        self.paused.set() if self.paused.is_set() else self.paused.clear()

    def register_numbers(
        self, /, seconds: int = 0, cooldown: int | float | None = None
    ):
        """
        Registers commands for numbers 0-9
        !0 - presses 0
        !1 - presses 1
        ...etc
        """
        for number in range(0, 10):
            self.__register_command(
                str(number),
                functools.partial(self.__press_key, str(number), seconds),
                cooldown,
            )

    def register_wasd(
        self,
        duration: int | float = 0.3,
        /,
        w: list[str] = ["w"],
        a: list[str] = ["a"],
        s: list[str] = ["s"],
        d: list[str] = ["d"],
        cooldown: int | float | None = None,
    ):
        self.__register_command(
            w,
            functools.partial(self.__press_key, "w", duration),
            cooldown,
        )
        self.__register_command(
            a,
            functools.partial(self.__press_key, "a", duration),
            cooldown,
        )
        self.__register_command(
            s,
            functools.partial(self.__press_key, "s", duration),
            cooldown,
        )
        self.__register_command(
            d,
            functools.partial(self.__press_key, "d", duration),
            cooldown,
        )

    def move_mouse(
        self,
        commands: list[str],
        direction: Direction,
        amount: int = 25,
        cooldown: int | float | None = None,
    ):
        if direction == Direction.UP:
            x = 0
            y = -amount
        elif direction == Direction.DOWN:
            x = 0
            y = amount
        elif direction == Direction.LEFT:
            x = -amount
            y = 0
        elif direction == Direction.RIGHT:
            x = amount
            y = 0
        self.__register_command(
            commands,
            functools.partial(self.__move_mouse, x, y),
            cooldown,
        )

    def press_key(
        self,
        commands: list[str],
        key: Key | str,
        seconds: int | float = 0,
        cooldown: int | float | None = None,
    ):
        self.__register_command(
            commands, functools.partial(self.__press_key, key, seconds), cooldown
        )

    def left_mouse_button(
        self,
        commands: list[str],
        cooldown: int | float | None = None,
    ):
        self.__register_command(
            commands, functools.partial(self.__press_key, Keys.LMB), cooldown
        )

    def right_mouse_button(
        self,
        commands: list[str],
        cooldown: int | float | None = None,
    ):
        self.__register_command(
            commands, functools.partial(self.__press_key, Keys.RMB), cooldown
        )

    async def __mouse_button_loop(self, button: str):
        queue = self.queues[button]
        is_held = False
        while True:
            try:
                await asyncio.wait_for(queue.get(), 0.4)
                if not is_held:
                    await self.ahk.click(button=button, direction="D")
                    is_held = True
            except asyncio.TimeoutError:
                if is_held:
                    await self.ahk.click(button=button, direction="U")
                    is_held = False
            except asyncio.CancelledError:
                if is_held:
                    await self.ahk.click(button=button, direction="U")
                break

    # twitchAPI callbacks

    async def __on_ready(self, event: EventData):
        print(f"Successfully connected to Twitch")
        await self.chat.join_room(self.channel)

    async def __on_joined(self, event: EventData):
        print(f"Joined {self.channel}")

    async def __on_message(self, message: ChatMessage):
        print(f"{message.user.name}: {message.text}")

    async def __press_key(
        self, key: str | Key, duration: int | float | None, _: ChatCommand
    ):
        self.controller.press_and_extend_key(key, duration)

    async def __move_mouse(self, x: int, y: int, _: ChatCommand):
        self.controller.add_mouse_movement(x, y)

    def __register_command(
        self, commands: str | list[str], func: Callable, cooldown: int | float | None
    ):
        """
        0 to disable cooldown
        None to use default
        """
        if isinstance(commands, str):
            commands = [commands]

        middlewares = []
        if cooldown or (cooldown is None and self.cooldown):
            middlewares.append(ChannelUserCommandCooldown(cooldown or self.cooldown))

        for command in commands:
            registered = self.chat.register_command(
                command, func, command_middleware=middlewares
            )
            if not registered:
                raise ValueError(f"Command {command} is already registered")
