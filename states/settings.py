from aiogram.dispatcher.filters.state import State, StatesGroup


class Settings(StatesGroup):
    choice_command = State()  # Выбор команды, уточняет параметры, если тех нет, кладёт идентификатор команды в фун().

    # Ввод города. Если не стр - повтор ввода
    check_city = State()        # Опрос хотелса. Если нет - возврат в инлайн
    correct_city = State()      # Выбор города в инлайн клаве

    set_date_in = State()       # Дата инлайн календарь. Если ввод с клавиатуры - проверка по шаблону\
    set_date_out = State()      # Дата инлайн календарь выезд.

    interval_price = State()    # минимум и максимум цен. Функция проверки принимает название состояния
    distance_center = State()   # дистанция до центра. Но вроде ненужен, если сортировка по нему

    look_info = State()
    num_hotels = State()
    num_photo = State()
    # Настройки
    look_settings = State()
    num_peoples = State()
    quality_photos = State()
#     изменение языка переводом,
#     конвертер валют
#     и расстояния,
#     стирание истории
#  асинхронный запрос
# фоновый запрос для подгрузки доп 25ти отелей
# следующие фотки / фоток больше нет/ фоток осталось
# фоновая проверка следующих фоток
