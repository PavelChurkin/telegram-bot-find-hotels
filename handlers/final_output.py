import time
from aiogram.types import Message, InputMediaPhoto
from loader import bot, dp
from logs.log_info import logger
from hotels import requests_hotels
from aiogram.utils.markdown import hlink
from keyboards.inline import which

from database.base import Session, engine, Base
from database.tables import History\
    # , Photos, Hotel


@logger.catch()
async def launcher_search(msg: Message):
    await msg.edit_text('Запрос отправлен, пожалуйста подождите...')

    Base.metadata.create_all(engine)
    state = dp.get_current().current_state()
    logger.info(f'{state.user} ({state.chat}) Поиск отелей')
    dct = await state.get_data()
    hotels = await requests_hotels.search_hotels(dct)
    logger.debug(hotels)

    await msg.edit_text(f"По запросу {dct['selected_command']} нашлись следующие отели:")
    all_text = ''
    text_list = []
    days = int(dct['unix_date_out'] - dct['unix_date_in'])

    # 1) Собираем информацию в список
    for i_hotel in hotels[:dct['num_hotels']]:
        link_site = hlink(f"{i_hotel['hotel_name']}", f"{i_hotel['url']}")
        link_map = hlink(f"{i_hotel['address']}", f"{i_hotel['map_point']}")
        text = f"\nНазвание: \t{link_site}\n" \
               f"Адрес: \t{link_map}\n" \
               f"Период \t{dct['interval_date']}\n" \
               f"Цена: {i_hotel['price'] * days} руб. \t({i_hotel['price']}/ночь)\n" \
               f"Расстояние до центра: \t{i_hotel['center']} км\n" \
               f"Оценка: \t{i_hotel['rate']}"
        all_text += text + '\n'  # для истории
        text_list.append(text)

    # 2) Получаем фотографии
    urls_photos = await requests_hotels.get_all_photos(hotels[:dct['num_hotels']], dct['quality_photos'])

    if dct['bool_photos']:
        # 3) Сохраняем их в списке
        all_media = []

        for i, (urls, text) in enumerate(zip(urls_photos[:dct['num_photos']], text_list)):
            all_media.append(
                [InputMediaPhoto(media=url,
                                 caption=f'{text}' if index == 0 else None)
                 for index, url in enumerate(urls[:dct['num_photos']])
                 ]
            )
    else:
        all_media = None

    # 4) Отправляем пользователю
    for i, text in enumerate(text_list):
        if all_media:
            await bot.send_media_group(chat_id=state.chat, media=all_media[i])
        else:
            await bot.send_message(state.chat, text, disable_web_page_preview=True)

    s = Session()
    i_history = History(
        chat_id=state.chat,
        date_request=time.strftime("%d %m %Y %H:%M:%S", time.localtime(int(time.time()))),
        selected_command=dct['selected_command'],
        city=dct['correct_city'],
        text=all_text,
        hotels=str(hotels)
    )
    s.add(i_history)
    s.commit()

    await msg.answer('Предлагаю поискать что-нибудь ещё', reply_markup=which.back_button())


def db_reader():
    session = Session()
    state = dp.get_current().current_state()
    history = session.query(History).filter(History.chat_id.ilike(state.chat)).all()
    return history
