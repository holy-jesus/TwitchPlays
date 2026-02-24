from twitchAPI.chat import ChatMessage
import asyncio
import functools
from typing import Callable

from aiohttp.helpers import sentinel
from ahk import AsyncAHK
from ahk.keys import Key, KEYS
from twitchAPI.type import ChatEvent
from twitchAPI.chat import Chat, EventData, ChatCommand
from twitchAPI.chat.middleware import ChannelUserCommandCooldown, BaseCommandMiddleware


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


class Keys(KEYS):
    LMB = "left"
    RMB = "right"
    LEFT_MOUSE_BUTTON = LMB
    RIGHT_MOUSE_BUTTON = RMB
    LeftMouseButton = LMB
    RightMouseButton = RMB


class Direction:
    UP = "up"
    Up = UP
    DOWN = "down"
    Down = DOWN
    LEFT = "left"
    Left = LEFT
    RIGHT = "right"
    Right = RIGHT


class Bot:
    def __init__(
        self,
        channel: str,
        process: str,
        /,
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

        self.ahk = AsyncAHK()
        self.chat = Chat(FakeTwitch)
        self.paused = asyncio.Event()

        self.ahk.add_hotkey(Keys.SHIFT + Keys.BACKSPACE, self.stop)
        self.ahk.add_hotkey("F12", self.toggle_pause)

        self.chat.set_prefix(prefix)

        self.chat.register_command_middleware(
            ActiveWindowMiddleware(self.ahk, self.process)
        )
        self.chat.register_command_middleware(PausedMiddleware(self.paused))

        self.chat.register_event(ChatEvent.READY, self.__on_ready)
        self.chat.register_event(ChatEvent.JOINED, self.__on_joined)
        self.chat.register_event(ChatEvent.MESSAGE, self.__on_message)

        self.queues: dict[str, asyncio.Queue] = {}

    def run(self):
        try:
            self.loop.run_until_complete(self.start())
            self.loop.run_forever()
        except KeyboardInterrupt:
            self.loop.run_until_complete(self.stop())

    async def start(self):
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
        seconds: int | float = 0.3,
        /,
        w: list[str] = ["w"],
        a: list[str] = ["a"],
        s: list[str] = ["s"],
        d: list[str] = ["d"],
        cooldown: int | float | None = None,
    ):
        self.__register_command(
            w,
            functools.partial(self.__press_key, "w", seconds),
            cooldown,
        )
        self.__register_command(
            a,
            functools.partial(self.__press_key, "a", seconds),
            cooldown,
        )
        self.__register_command(
            s,
            functools.partial(self.__press_key, "s", seconds),
            cooldown,
        )
        self.__register_command(
            d,
            functools.partial(self.__press_key, "d", seconds),
            cooldown,
        )

    def move_mouse(
        self,
        commands: list[str],
        direction,
        amount: int = 25,
        speed: int = 10,
        cooldown: int | float | None = None,
    ):
        if direction == Direction.UP:
            y = -amount
            x = 0
        elif direction == Direction.DOWN:
            y = amount
            x = 0
        elif direction == Direction.LEFT:
            y = 0
            x = -amount
        elif direction == Direction.RIGHT:
            y = 0
            x = amount
        self.__register_command(
            commands,
            functools.partial(
                self.ahk.mouse_move,
                x=x,
                y=y,
                speed=speed,
                blocking=False,
                relative=True,
            ),
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
        # TODO тут пока что cooldown ломает всё немного совсем чутьчуть
        self.queues["left"] = asyncio.Queue()
        self.__register_command(
            commands, functools.partial(self.__mouse_button, "left"), cooldown
        )

    def right_mouse_button(
        self,
        commands: list[str],
        cooldown: int | float | None = None,
    ):
        self.queues["right"] = asyncio.Queue()
        self.loop.create_task(self.__mouse_button_loop("right"))
        self.__register_command(
            commands, functools.partial(self.__mouse_button, "right"), cooldown
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
        print(f"Logged in as {self.chat.username}")
        await self.chat.join_room(self.channel)

    async def __on_joined(self, event: EventData):
        print(f"Joined {self.channel}")

    async def __on_message(self, message: ChatMessage):
        print(f"{message.user.name}: {message.text}")

    async def __mouse_button(self, button: str, _: ChatCommand):
        self.queues[button].put_nowait(True)

    async def __press_key(
        self, key: Key | str, seconds: int | float | None, _: ChatCommand
    ):
        if not seconds:
            await self.ahk.key_press(key, release=True, blocking=False)
        else:
            await self.ahk.key_down(key)
            await asyncio.sleep(seconds)
            await self.ahk.key_up(key)

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
            middlewares.append(
                ChannelUserCommandCooldown(cooldown or self.cooldown)
            )

        for command in commands:
            registered = self.chat.register_command(
                command, func, command_middleware=middlewares
            )
            if not registered:
                raise ValueError(f"Command {command} is already registered")
