from bot import Bot, Keys, Direction, RUSSIAN_WASD, RUSSIAN_KEYBOARD


bot = Bot("CHANNEL_NAME", "PlayGTAV.exe", mouse_speed=25)

bot.register_wasd(0.7, cooldown=0.7, **RUSSIAN_WASD)
bot.register_all_keys(cooldown=0.3, **RUSSIAN_KEYBOARD)
bot.register_numbers(cooldown=0.3)

bot.move_mouse(["i", "ш"], direction=Direction.UP, amount=150)
bot.move_mouse(["k", "л"], direction=Direction.DOWN, amount=150)
bot.move_mouse(["j", "о"], direction=Direction.LEFT, amount=150)
bot.move_mouse(["l", "д"], direction=Direction.RIGHT, amount=150)

bot.press_key(["g", "п"], Keys.SPACE, 0.3)
bot.press_key(["e", "у"], "e", 0.3)

bot.key_vote(["f", "а"], "f", 10, 10, 0.3, 10)

bot.left_mouse_button(["x", "ч"], duration=0.3)
bot.right_mouse_button(["c", "с"], duration=0.3)


bot.run()
