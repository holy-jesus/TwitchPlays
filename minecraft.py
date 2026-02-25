from bot import Bot, Keys, Direction


bot = Bot("CHANNEL_NAME", "*", mouse_speed=10)

bot.register_wasd(0.3, w=["w", "ц"], a=["a", "ф"], s=["s", "ы"], d=["d", "в"])
bot.register_numbers()


bot.move_mouse(["i", "ш"], direction=Direction.UP, amount=25)
bot.move_mouse(["k", "л"], direction=Direction.DOWN, amount=25)
bot.move_mouse(["j", "о"], direction=Direction.LEFT, amount=25)
bot.move_mouse(["l", "д"], direction=Direction.RIGHT, amount=25)

bot.press_key(["g", "п"], Keys.SPACE, 0.3)
bot.press_key(["e", "у"], "e", 0.3)

bot.left_mouse_button(["x", "ч"])
bot.right_mouse_button(["c", "с"])


bot.run()
