import re
from datetime import timezone
import time
from logs.log_info import logger
from aiogram.types import Message, CallbackQuery
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher import FSMContext

from loader import bot, dp
from keyboards.inline import which
from config_data.config import admin_id
from states.settings import Settings
from hotels import requests_hotels
from .final_output import launcher_search, db_reader

from aiogram_calendar import dialog_cal_callback, DialogCalendar


async def send_to_admin():
    await bot.send_message(chat_id=admin_id, text=f'Бот онлайн')


async def send_to_admin_end():
    await bot.send_message(chat_id=admin_id, text=f'Бот оффлайн')


@dp.message_handler(Command('start'), state="*")
@logger.catch()
async def begin(msg: Message, state: FSMContext):
    await state.update_data({
        'chat_id': state.chat,
        'correct_city': None,
        'interval_date': None,
        'interval_price': None,
        'distance_center': None,
        'num_hotels': 3,
        'num_photos': 3,
        'bool_photos': False,
        'num_peoples': 1,
        'num_requests': 2,
        'quality_photos': 4,
        'selected_command': None,
        'flag_checking': False,     # для возврата с настроек к уточнению, иначе выбор команды
        'json_city': None
    })
    logger.info(f'Инициация - {state.user} ({state.chat})')
    await input_command(msg)


@logger.catch()
async def input_command(msg: Message):
    await msg.answer(f'Выберите команду.', reply_markup=which.command())
    await Settings.choice_command.set()


@dp.callback_query_handler(state=Settings.choice_command, text_contains='low')
@dp.callback_query_handler(state=Settings.choice_command, text_contains='high')
@dp.callback_query_handler(state=Settings.choice_command, text_contains='best')
@logger.catch()
async def command_save(call: CallbackQuery, state: FSMContext):
    await state.update_data(selected_command=call.data)
    logger.info(f'{state.user} ({state.chat}) выбрал команду {call.data}')
    await command_check(call)


@dp.callback_query_handler(text_contains='cancel', state="*")
async def cancel_button(call: CallbackQuery, state: FSMContext):
    # logger.info(f'{state.user} ({state.chat}) отмена стэйта {await state.get_state()}')
    await state.update_data(flag_checking=False)
    await state.reset_state(with_data=False)
    await call.message.delete()
    await input_command(call.message)


@dp.callback_query_handler(text_contains='settings', state="*")
async def settings_button(call: CallbackQuery, state: FSMContext):
    dct = await state.get_data()
    logger.debug(dct)
    return await input_settings(call.message)


@dp.callback_query_handler(text_contains='history', state="*")
@logger.catch()
async def history_button(call: CallbackQuery, state: FSMContext):
    dct = await state.get_data()
    logger.info(f'{state.user} ({state.chat}) Вывод истории')

    history = db_reader()
    if len(history) == 0:
        return await call.message.edit_text("Ваша история запросов чиста", reply_markup=which.cancel_button())
    else:
        await call.message.edit_text(f"Ваши предыдущие запросы (последние {dct['num_requests']}):")
        index = len(history) - dct['num_requests'] if len(history) > dct['num_requests'] else 0
        for i_history in history[index:]:
            text = f"Дата запроса: {i_history.date_request}\nЗапрос: {i_history.selected_command}\nГород: {i_history.city}\n{i_history.text}\n"
            await call.message.answer(f"{text}", disable_web_page_preview=True)
        await call.message.answer("Нажмите 'Отмена' чтобы вернуться в меню", reply_markup=which.cancel_button())


@dp.callback_query_handler(text_contains='help', state="*")
async def help_button(call: CallbackQuery):
    await call.message.edit_text(
        text="Привет!\nДанный бот разработан в рамках дипломного проекта Skillbox. "
             "На данный момент бот имеет следующие основные 3 функции взаимодействия с сайтом Hotels.com:\n\n"
             "Lowprice\t- Узнать топ самых дешёвых отелей в городе.\n"
             "Highprice\t- Узнать топ самых дорогих отелей в городе.\n"
             "Bestdeal\t- Узнать топ отелей, наиболее подходящих по цене и расположению от центра.\n"
             "\n- Настройки имеют количество заселяемых человек и качество фото"
             "\n- Перед запросом имеется возможность увидеть все параметры или их изменить."
             "\n- Результат запроса будет сохранён в историю."
             "\nВнимание. Если нажать старт при любом вводе - все текущие настройки будут обнулены."
             "\nПоиск городов для России не работает."
             "\nДля начала диалога нажмите /start",
        reply_markup=which.cancel_button()
    )

# ########################################################################## Проверка заполненности данных


@dp.callback_query_handler(state=Settings.choice_command)
@logger.catch()
async def command_check(call_msg):
    state = dp.get_current().current_state()
    dct = await state.get_data()
    logger.debug(dct)
    if not dct['correct_city']:
        return await input_city(call_msg.message if type(call_msg) is CallbackQuery else call_msg)
    if not dct['interval_date']:
        return await input_date(call_msg.message if type(call_msg) is CallbackQuery else call_msg)
    if not dct['interval_price'] and dct['selected_command'] == 'bestdeal':
        return await input_price(call_msg.message if type(call_msg) is CallbackQuery else call_msg)
    if not dct['distance_center'] and dct['selected_command'] == 'bestdeal':
        return await input_distance_center(call_msg.message if type(call_msg) is CallbackQuery else call_msg)
    else:
        await look_info(call_msg)
# ########################################################################## Выбор города


@logger.catch()
async def input_city(msg: Message):
    state = dp.get_current().current_state()
    logger.info(f'{state.user} ({state.chat}) Ввод города')
    await msg.edit_text(f'В каком городе хотели бы остановиться?',
                        reply_markup=which.cancel_button())
    await Settings.check_city.set()


@dp.message_handler(state=Settings.check_city)
@logger.catch()
async def check_city(msg: Message):
    state = dp.get_current().current_state()
    dct = await state.get_data()
    logger.debug(dct)
    if msg.text.isdigit():
        logger.info(f'{state.user} ({state.chat}) Некорректный ввод города')
        error_msg = await msg.answer('Ошибка. Обычно в названии города цифр нет. Повторите ввод')
        time.sleep(3)
        await msg.delete()
        await error_msg.delete()
    else:
        logger.info(f'{state.user} ({state.chat}) Город принят')
        await Settings.correct_city.set()
        return await request_city(msg)


@logger.catch()
async def request_city(msg: Message):
    state = dp.get_current().current_state()
    # logger.debug(f'{state.user} ({state.chat}) request_city')
    flag = await requests_hotels.search_city(msg.text)
    dct = await state.get_data()
    logger.debug(dct)
    if flag:
        logger.info(f'{state.user} ({state.chat}) Уточнение города')
        await msg.answer(f'Уточните. По запросу {msg.text} есть следующие города:',
                         reply_markup=which.city(dct['json_city']))
    else:
        logger.info(f'{state.user} ({state.chat}) Город не найден')
        await msg.answer(f'По запросу {msg.text} городов не найдено. Повторите ввод города',
                         reply_markup=which.cancel_button())
        return await Settings.check_city.set()


@dp.message_handler(state=[Settings.correct_city, Settings.set_date_in, Settings.set_date_out, Settings.num_hotels,
                           Settings.num_photo, Settings.look_settings, Settings.look_info, Settings.choice_command])
async def error_input(msg: Message):
    error_msg = await msg.answer('Ошибка. Ввод только по встроенной клавиатуре')
    time.sleep(3)
    await error_msg.delete()
    await msg.delete()


@dp.callback_query_handler(state=Settings.correct_city)
@logger.catch()
async def choice_city(call: CallbackQuery, state: FSMContext):
    lst = call.data.split(':')
    async with state.proxy() as dct:
        # logger.debug(dct)
        dct['correct_city'] = lst[1]
        dct['city_id'] = lst[0][3:]
    logger.info(f'{state.user} ({state.chat}) Город выбран')
    return await command_check(call)

# ########################################################################## Выбор даты


@logger.catch()
async def input_date(msg: Message):
    state = dp.get_current().current_state()
    logger.info(f'{state.user} ({state.chat}) Ввод даты приезда')
    await msg.edit_text(f'Выберите дату приезда (сегодня {time.strftime("%d.%m.%Y", time.gmtime(time.time()))})',
                        reply_markup=await DialogCalendar().start_calendar())
    await Settings.set_date_in.set()


@dp.callback_query_handler(dialog_cal_callback.filter(), state=Settings.set_date_in)
@logger.catch()
async def date_in(call: CallbackQuery, callback_data: dict, state: FSMContext):
    selected, date = await DialogCalendar().process_selection(call, callback_data)
    if selected:
        if int(time.time()/86400) > int(date.replace(tzinfo=timezone.utc).timestamp()/86400):
            logger.info(f'{state.user} ({state.chat}) Некорректная дата приезда')
            error_msg = await call.message.answer('Не нужно лезть в прошлое')
            time.sleep(3)
            await error_msg.delete()
            return await input_date(call.message)
        async with state.proxy() as dct:
            logger.debug(dct)
            dct['interval_date'] = date.strftime("%d.%m.%Y")
            dct['unix_date_in'] = int(date.replace(tzinfo=timezone.utc).timestamp() / 86400)
            await call.message.edit_text(f'Выбрано {date.strftime("%d.%m.%Y")}. Выберите дату отъезда',
                                         reply_markup=await DialogCalendar().start_calendar())
            await Settings.set_date_out.set()
            logger.info(f"{state.user} ({state.chat}) Выбрана дата - {dct['interval_date']}. Ввод даты отъезда")


@dp.callback_query_handler(dialog_cal_callback.filter(), state=Settings.set_date_out)
@logger.catch()
async def date_out(call: CallbackQuery, callback_data: dict, state: FSMContext):
    selected, date = await DialogCalendar().process_selection(call, callback_data)
    if selected:
        async with state.proxy() as dct:
            if dct['unix_date_in'] >= int(date.replace(tzinfo=timezone.utc).timestamp() / 86400):
                logger.info(f'{state.user} ({state.chat}) Некорректная дата отъезда')
                error_msg = await call.message.answer('Вторая дата должна быть позже первой')
                time.sleep(4)
                await error_msg.delete()
                return await call.message.edit_reply_markup(await DialogCalendar().start_calendar())

            dct['interval_date'] += f' / {date.strftime("%d.%m.%Y")}'
            dct['unix_date_out'] = int(date.replace(tzinfo=timezone.utc).timestamp() / 86400)
            logger.info(f"{state.user} ({state.chat}) Выбрана дата - {dct['interval_date']}")
        return await command_check(call)


# ########################################################################## bestdeal


@logger.catch()
async def input_price(msg: Message):
    state = dp.get_current().current_state()
    logger.info(f'{state.user} ({state.chat}) Ввод диапазона цен')
    await msg.answer(f'Введите диапазон цен за ночь(руб.) \n(в формате ХХХ - ХХХХ)', reply_markup=which.cancel_button())
    await Settings.interval_price.set()


@dp.message_handler(state=Settings.interval_price)
@logger.catch()
async def check_price(msg: Message):
    state = dp.get_current().current_state()
    dct = await state.get_data()
    logger.debug(dct)
    price = re.findall('([0-9]+)[^0-9]+([0-9]+)', msg.text)
    if len(price) > 1:
        error_msg = await msg.answer('Ошибка. Принимаю максимум 2 числа. Повтори ввод')
        time.sleep(3)
        await error_msg.delete()
        await msg.delete()
    elif len(price) == 0:
        error_msg = await msg.answer('Ошибка. Не нашёл двух чисел. Повтори ввод')
        time.sleep(3)
        await error_msg.delete()
        await msg.delete()
    elif int(price[0][0]) > int(price[0][1]):
        error_msg = await msg.answer('Ошибка. Первое число должно быть меньше или равно второму. Повтори ввод')
        time.sleep(4)
        await error_msg.delete()
        await msg.delete()
    else:
        interval = f'{price[0][0]} - {price[0][1]}'
        await state.update_data(interval_price=interval)
        logger.info(f'{state.user} ({state.chat}) Диапазон цен принят - {interval}')
        await command_check(msg)


@logger.catch()
async def input_distance_center(msg: Message):
    state = dp.get_current().current_state()
    logger.info(f'{state.user} ({state.chat}) Ввод расстояния до центра')
    await msg.answer('Введите желаемое максимальное расстояние до центра (км)',
                     reply_markup=which.cancel_button())
    await Settings.distance_center.set()


@dp.message_handler(state=Settings.distance_center)
@logger.catch()
async def check_distance_center(msg: Message):
    state = dp.get_current().current_state()
    dct = await state.get_data()
    logger.debug(dct)
    distance = re.findall('([0-9]+)', msg.text)
    if len(distance) > 1:
        error_msg = await msg.answer('Ошибка. Ожидаю максимум 1 число. Повтори ввод')
        time.sleep(3)
        await error_msg.delete()
        await msg.delete()
    elif len(distance) == 0:
        error_msg = await msg.answer('Ошибка. Не вижу цифр. Повтори ввод')
        time.sleep(3)
        await error_msg.delete()
        await msg.delete()
    else:
        await state.update_data(distance_center=distance[0])
        logger.info(f'{state.user} ({state.chat}) Диапазон цен принят - {distance[0]}')
        await command_check(msg)

# ##########################################################################


@logger.catch()
async def look_info(call_msg):  # смешанный тип из-за последнего ввода bestdeal, все прочие последний - колбэк
    state = dp.get_current().current_state()
    await state.update_data(flag_checking=True)
    dct = await state.get_data()
    logger.info(f"{state.user} ({state.chat}) Предложение изменить выбранные настройки для {dct['selected_command']}")
    if type(call_msg) is CallbackQuery:
        await call_msg.message.edit_text(text=f"Текущий запрос - {dct['selected_command']}. Всё так?",
                                         reply_markup=which.parameter_change(dct))
    else:
        await call_msg.answer(text=f"Текущий запрос - {dct['selected_command']} Всё так?",
                              reply_markup=which.parameter_change(dct))
    await Settings.look_info.set()


@dp.callback_query_handler(state=Settings.look_info)
@logger.catch()
async def look_info_callback(call: CallbackQuery, state: FSMContext):
    if 'correct_city' in call.data:
        return await input_city(call.message)
    if 'interval_date' in call.data:
        return await input_date(call.message)
    if 'interval_price' in call.data:
        return await input_price(call.message)
    if 'distance_center' in call.data:
        return await input_distance_center(call.message)

    if 'num_hotels' in call.data:
        return await input_num_hotels(call.message)
    if 'num_photos' in call.data:
        return await input_num_photo(call.message)
    if 'bool_photos' in call.data:
        async with state.proxy() as dct:
            dct['bool_photos'] = not dct['bool_photos']
            await call.message.edit_reply_markup(which.parameter_change(dct))
    if 'ok' in call.data:
        await state.update_data(flag_cheking=False)
        return await launcher_search(call.message)
    if 'final back' in call.data:
        await call.message.delete()
        await input_command(call.message)


# ###################################### final output #################################### #

# ##################################### доп настройки
# ##################################### Выбор количества отелей
@logger.catch()
async def input_num_hotels(msg: Message):
    state = dp.get_current().current_state()
    logger.info(f'{state.user} ({state.chat}) Запрос количества отелей')
    await msg.edit_text(f'Выберите количество отображаемых отелей за один запрос',
                        reply_markup=which.num_hotels())
    await Settings.num_hotels.set()


@dp.callback_query_handler(state=Settings.num_hotels)
@logger.catch()
async def choice_num_hotels(call: CallbackQuery, state: FSMContext):
    await state.update_data(num_hotels=int(call.data))
    logger.info(f'{state.user} ({state.chat}) Отелей выбрано - {int(call.data)}')
    await command_check(call)


# ##################################### Выбор количества фото
@logger.catch()
async def input_num_photo(msg: Message):
    state = dp.get_current().current_state()
    logger.info(f'{state.user} ({state.chat}) Запрос количества фото')
    await msg.edit_text(f'Выберите количество отображаемых фото за один запрос',
                        reply_markup=which.num_photos())
    await Settings.num_photo.set()


@dp.callback_query_handler(state=Settings.num_photo)
@logger.catch()
async def choice_num_photo(call: CallbackQuery, state: FSMContext):
    await state.update_data(num_photos=int(call.data))
    logger.info(f'{state.user} ({state.chat}) Фото выбрано - {int(call.data)}')
    await command_check(call)


# ##################################### Настройки
@logger.catch()
async def input_settings(msg: Message):
    state = dp.get_current().current_state()
    logger.info(f'{state.user} ({state.chat}) Просмотр настроек')
    dct = await state.get_data()
    await msg.edit_text(f'Настройки:', reply_markup=which.settings(dct))
    await Settings.look_settings.set()


@dp.callback_query_handler(state=Settings.look_settings)
@logger.catch()
async def choice_settings(call: CallbackQuery, state: FSMContext):
    logger.info(f'{state.user} ({state.chat}) Изменение настроек - {call.data}')
    if 'quality_photos' in call.data:
        q = int(call.data.split(':')[1])
        if q > 4:
            await state.update_data(quality_photos=1)
        else:
            await state.update_data(quality_photos=q)
        dct = await state.get_data()
        await call.message.edit_reply_markup(which.settings(dct))
    if 'num_peoples' in call.data:
        q = int(call.data.split(':')[1])
        if q > 3:
            await state.update_data(num_peoples=1)
        else:
            await state.update_data(num_peoples=q)
        dct = await state.get_data()
        await call.message.edit_reply_markup(which.settings(dct))
    if 'num_requests' in call.data:
        q = int(call.data.split(':')[1])
        if q > 5:
            await state.update_data(num_requests=1)
        else:
            await state.update_data(num_requests=q)
        dct = await state.get_data()
        await call.message.edit_reply_markup(which.settings(dct))

    if 'back' in call.data:
        dct = await state.get_data()
        logger.info(f'Настройки сохранены')
        if dct['flag_checking']:
            return await command_check(call)
        await call.message.delete()
        await input_command(call.message)
