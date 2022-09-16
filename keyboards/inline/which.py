from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def command():
    commands = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Lowprice', callback_data='lowprice'),
             InlineKeyboardButton(text='Highprice', callback_data='highprice'),
             InlineKeyboardButton(text='Bestdeal', callback_data='bestdeal')],
            [InlineKeyboardButton(text='Настройки', callback_data='settings'),
             InlineKeyboardButton(text='История', callback_data='history'),
             InlineKeyboardButton(text='Помощь', callback_data='help')]
        ]
    )
    return commands


def city(json_city: list):
    cities = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=f'{i["caption"]}',
                                               callback_data=f'id_{i["destinationId"]}:{i["name"]}')]
                         for i in json_city]
    )
    cities.add(InlineKeyboardButton(text='Отмена', callback_data='cancel'))
    return cities


def parameter_change(dct: dict):
    parameters = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f'Город:\t{dct["correct_city"]}',
                                  callback_data='correct_city')],
            [InlineKeyboardButton(text=f'Временной интервал:\t{dct["interval_date"]}',
                                  callback_data='parameter:interval_date')]
        ]
    )
    if dct['selected_command'] == 'bestdeal':
        parameters.row(InlineKeyboardButton(text=f'Ценовой диапазон:\t{dct["interval_price"]} руб.',
                                            callback_data='interval_price'))
        parameters.row(InlineKeyboardButton(text=f'Расстояние до центра:\t{dct["distance_center"]} км',
                                            callback_data='distance_center'))
    parameters.row(InlineKeyboardButton(text=f'Отелей:\t{dct["num_hotels"]}',
                                        callback_data='num_hotels'))
    bool_photo = "Да" if dct["bool_photos"] else "Нет"
    parameters.insert(InlineKeyboardButton(text=f'С фото:\t{bool_photo}',
                                           callback_data='bool_photos'))
    if dct["bool_photos"]:
        parameters.insert(InlineKeyboardButton(text=f'Фото:\t{dct["num_photos"]}',
                                               callback_data='num_photos'))
    parameters.row(InlineKeyboardButton(text='Назад', callback_data='cancel'),
                   InlineKeyboardButton(text='Настройки', callback_data='settings'),
                   InlineKeyboardButton(text='Да', callback_data='ok'))
    return parameters


def num_hotels():
    num_hotel = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=f'{i}',
                                               callback_data=f'{i}') for i in range(1, 6)],
                         [InlineKeyboardButton(text=f'{i}',
                                               callback_data=f'{i}') for i in range(6, 11)],
                         [InlineKeyboardButton(text=f'{i}',
                                               callback_data=f'{i}') for i in range(11, 16)],
                         [InlineKeyboardButton(text=f'{i}',
                                               callback_data=f'{i}') for i in range(16, 21)],
                         [InlineKeyboardButton(text=f'{i}',
                                               callback_data=f'{i}') for i in range(21, 26)]
                         ]
    )
    return num_hotel


def num_photos():
    num_photo = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=f'{i}',
                                               callback_data=f'{i}') for i in range(1, 6)],
                         [InlineKeyboardButton(text=f'{i}',
                                               callback_data=f'{i}') for i in range(6, 11)]]
    )
    return num_photo


def settings(dct: dict):
    state = {1: "Наихудшее", 2: "Плохое", 3: "Хорошее", 4: "Наилучшее"}
    setting = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=f'Количество человек: {dct["num_peoples"]}',
                                               callback_data=f'num_peoples:{dct["num_peoples"] + 1}')],
                         [InlineKeyboardButton(text=f'Качество фото: {state[dct["quality_photos"]]}',
                                               callback_data=f'quality_photos:{dct["quality_photos"] + 1}')],
                         [InlineKeyboardButton(text=f'Количество последних запросов в истории: {dct["num_requests"]}',
                                               callback_data=f'num_requests:{dct["num_requests"] + 1}')],
                         [InlineKeyboardButton(text='Назад', callback_data='back')]]
    )
    return setting


def cancel_button():
    cancel = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Отмена', callback_data='cancel')]
        ]
    )
    return cancel


def back_button():
    back = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Назад к настройке запросов', callback_data='final back')]
        ]
    )
    return back
