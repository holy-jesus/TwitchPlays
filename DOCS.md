# Документация TwitchPlays Bot

Здесь описан основной API модуля бота для создания Twitch Plays интерактивов. Вся работа происходит через класс `Bot` из `bot.py`.

## Класс `Bot`

### Инициализация

```python
Bot(channel: str, process: str, mouse_speed: int = 15, prefix: str = "!", cooldown: int = 0, loop = None)
```
- `channel` — название канала на Twitch.
- `process` — имя процесса игры (например, `"GTA5.exe"`, `"javaw.exe"`). Если передать `"*"`, команды будут работать везде (игнорирует активное окно).
- `mouse_speed` — скорость плавного движения мыши. Чем меньше, тем медленнее мышь будет перемещаться до нужной позиции.
- `prefix` — префикс команд (по умолчанию `!`). Если оставить пустую строку `""`, бот будет реагировать на простые слова без символов.
- `cooldown` — кулдаун по умолчанию для всех команд (в секундах).
- `loop` — event loop asyncio (если не передан, создаст или возьмет текущий).

---

## Регистрация команд

Методы регистрации привязывают команды из чата к действиям. Практически все принимают параметры:
- `commands: str | list[str]` — строка или список строк, на которые будет реагировать бот (с учетом префикса).
- `duration: int | float` — длительность зажатия клавиши (в секундах). При значении `0` происходит простой клик.
- `cooldown: int | float | None` — кулдаун конкретно для этой команды. `None` означает использование глобального кулдауна.

### `register_wasd`
```python
bot.register_wasd(duration=0.3, cooldown=0.3, w=["w"], a=["a"], s=["s"], d=["d"])
```
Быстрая регистрация кнопок W, A, S, D. По умолчанию принимает списки алиасов. Вы можете использовать константу `RUSSIAN_WASD` для автоматической развертки кириллических аналогов (Ц, Ф, Ы, В).

### `register_numbers`
```python
bot.register_numbers(duration=0, cooldown=None)
```
Создает команды для цифр от `0` до `9`. Зритель пишет `!1` — нажимается клавиша `1`.

### `press_key`
```python
bot.press_key(commands=["g", "п"], key=Keys.SPACE, duration=0.3, cooldown=0)
```
Регистрирует собственную кнопку.
- `key` — название кнопки. Клавиши AHK находятся в перечислении `Keys` (например, `Keys.SPACE`, `Keys.ENTER`). Для обычных букв можно передавать строку `"e"`.

### `register_all_keys`
```python
bot.register_all_keys(duration=0.3, cooldown=0.3, **kwargs)
```
Позволяет передать словарь с клавишами в формате `{"имя кнопки": ["список", "макросов", "команд"]}`. Рекомендуется вызывать **в последнюю очередь**.

### `left_mouse_button` и `right_mouse_button`
```python
bot.left_mouse_button(commands=["x", "клик"], duration=0.5, cooldown=0.5)
bot.right_mouse_button(commands=["c", "пкм"], duration=0.5, cooldown=0.5)
```
Отвечает за нажатия ЛКМ и ПКМ. Длительность `duration` определяет, как долго кнопка мыши будет зажата.

### `move_mouse`
```python
bot.move_mouse(commands=["i", "ш"], direction=Direction.UP, amount=15, cooldown=1)
```
Перемещает курсор (камеру).
- `direction` — направление движения. Варианты из класса `Direction`: `UP`, `DOWN`, `LEFT`, `RIGHT`.
- `amount` — сила сдвига курсора (в пикселях по соответствующей оси).

### `key_vote` (Democracy Mode)
```python
bot.key_vote(
    commands=["f", "а"], key="f",
    required_votes=25, time_window=10,
    duration=1, cooldown=10
)
```
Режим голосования. Кнопка `key` нажмется на время `duration`, только если чат за время `time_window` (секунд) отправит команду `required_votes` раз.

---

## Запуск
После конфигурации вызовите `bot.run()`. Этот метод блокирующий и запускает event-loop библиотеки Twitch API и модуля AHK.

```python
bot.run()
```
