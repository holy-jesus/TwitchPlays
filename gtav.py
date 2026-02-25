from bot import Bot, Keys, Direction, RUSSIAN_WASD, RUSSIAN_KEYBOARD


bot = Bot("CHANNEL_NAME", "GTA5.exe", mouse_speed=1)

bot.press_key(["q", "й"], "q", duration=0.0, cooldown=180)

bot.register_wasd(duration=0.5, cooldown=0.5, **RUSSIAN_WASD)
bot.register_numbers(duration=0.0, cooldown=0.3)

bot.move_mouse(["i", "ш"], direction=Direction.UP, amount=15, cooldown=1)
bot.move_mouse(["k", "л"], direction=Direction.DOWN, amount=15, cooldown=1)
bot.move_mouse(["j", "о"], direction=Direction.LEFT, amount=15, cooldown=1)
bot.move_mouse(["l", "д"], direction=Direction.RIGHT, amount=15, cooldown=1)

bot.press_key(["g", "п"], Keys.SPACE, duration=0)
bot.press_key(["e", "у"], "e", duration=0)

bot.key_vote(
    commands=["f", "а"],
    key="f",
    required_votes=50,
    time_window=10,
    duration=1,
    cooldown=10,
)

bot.left_mouse_button(["x", "ч"], duration=0.5, cooldown=0.5)
bot.right_mouse_button(["c", "с"], duration=0.5, cooldown=0.5)

bot.register_all_keys(duration=0.3, cooldown=0.3, **RUSSIAN_KEYBOARD)

bot.run()
