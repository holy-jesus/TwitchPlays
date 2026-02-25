from bot import Bot, Keys, Direction, RUSSIAN_WASD, RUSSIAN_KEYBOARD


bot = Bot("CHANNEL_NAME", "javaw.exe", mouse_speed=10)

bot.register_wasd(0.3, cooldown=0.3, **RUSSIAN_WASD)
bot.register_numbers(0.1, cooldown=0.3)


bot.move_mouse(["i", "ш"], direction=Direction.UP, amount=100)
bot.move_mouse(["k", "л"], direction=Direction.DOWN, amount=100)
bot.move_mouse(["j", "о"], direction=Direction.LEFT, amount=100)
bot.move_mouse(["l", "д"], direction=Direction.RIGHT, amount=100)

bot.press_key(["g", "п"], Keys.SPACE, 0.3)
bot.key_vote(["e", "у"], "e", 10, 10, 0.3)

bot.left_mouse_button(["x", "ч"], duration=0.3)
bot.right_mouse_button(["c", "с"], duration=0.3)


bot.run()
