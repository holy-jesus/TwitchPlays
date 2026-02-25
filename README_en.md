# TwitchPlays Bot

A Python-based bot for creating "Twitch Plays" style interactive streams, allowing viewers to control gameplay through Twitch chat commands.

The bot utilizes [twitchAPI](https://github.com/Teekeks/twitchAPI) to read chat messages and [ahk](https://github.com/spyoungtech/ahk) (AutoHotkey) to emulate keystrokes and mouse movements specifically inside a targeted game window.

## Features
* **Active Window Targeting**: Chat commands are executed only if the specified game process (e.g., `GTA5.exe`, `javaw.exe`) is actively focused.
* **Cooldowns**: Built-in support for command cooldowns to prevent spamming.
* **Voting System (Democracy)**: Configure commands that invoke an action only after receiving a specific number of votes within a timeframe.
* **Smooth Mouse Movement**: Fluid mouse/camera control with adjustable speed via a background loop.
* **Hotkeys**: Easily pause or stop the bot using physical keyboard hotkeys.
* **Command Aliases**: Support for multiple spelling variations (e.g., Cyrillic/Latin keyboard layouts).

## Requirements
* Python 3.10+
* AutoHotkey (AHK) v1.x installed (must be available in PATH).
* Python dependencies: `twitchAPI`, `ahk`

## Quick Start
Example setup for Minecraft:
```python
from bot import Bot, Keys, Direction, RUSSIAN_WASD

# Initialize the bot for a specific channel, targeting "javaw.exe"
bot = Bot("CHANNEL_NAME", "javaw.exe", mouse_speed=10)

# Register movement commands (WASD)
bot.register_wasd(0.3, cooldown=0.3, **RUSSIAN_WASD)

# Run the bot
bot.run()
```

## PC Hotkeys
* `F12` — Toggle Pause. While paused, viewers can send commands but they will be ignored.
* `Shift` + `Backspace` — Force stop the bot completely.

*API Documentation can be found in [DOCS.md](DOCS.md).*
[Русская версия](README.md)
