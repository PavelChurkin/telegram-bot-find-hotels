from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
# engine = create_engine("mysql+mysqlconnector://my_name:root@localhost:3306/my_db", echo=True)

engine = create_engine('sqlite:///database/sqlite_hotels.db', echo=True)
Session = sessionmaker(bind=engine)
Base = declarative_base()




























# для себя. Временное решение через json -
# создание бд
# dct = {'chat_id': 2088786132,
#        'date_request': '18 07 2022 19:07:29',
#        'selected_command': 'lowprice',
#        'city': 'Шарлоттенбург',
#        'text': 'Название: \t<a href="https://www.hotels.com/ho377867">Pestana Berlin Tiergarten</a>\nАдрес: \t<a href="http://maps.google.com/maps?z=12&t=m&q=loc:52.50859,13.349449">10787, Stuelerstrasse 6</a>\nПериод \t28.09.2022 / 29.09.2022\nЦена: 8039 руб. \t(8039/ночь)\nРасстояние до центра: \t0.6 км\nОценка: \t8.8/10 по 1974 отзывам\n'}
# __lst = []
# __lst.append(dct)
# with open('history.json', 'w', encoding='utf-8') as f:
#     json.dump(__lst, f, ensure_ascii=False)
#     # __lst = json.loads(f.read())


"""
    # запись
    # with open('database/history.txt', 'r', encoding='utf-8') as f:
    #     data = eval(f.read())
    dct = {
        'chat_id': state.chat,
        'date_request': time.strftime("%d %m %Y %H:%M:%S", time.localtime(int(time.time()))),
        'selected_command': __data['selected_command'],
        'city': __data['correct_city'],
        'text': __all_text
        # '__hotels': __hotels,
        # '__photos': __photos
    }
    with open('database/history.json', 'r', encoding='utf-8') as f:
        __lst = json.load(f)
        __lst.append(dct)
    with open('database/history.json', 'w', encoding='utf-8') as f:
        json.dump(__lst, f, ensure_ascii=False)

    
"""

# воспроизведение
# with open('database/history.json', 'r', encoding='utf-8') as f:
#     data = json.load(f)
# __history = []
# __lst = [__history.append(i) if i['chat_id'] == state.chat else None for i in data]
# __index = len(__history) - dct['num_requests'] if len(__history) > dct['num_requests'] else 0
# __history = __history[__index:]
# __text = ''
# for i_dict in __history:
#     __text += f"Дата запроса: {i_dict['date_request']}\nЗапрос: {i_dict['selected_command']}\nГород: {i_dict['city']}\n{i_dict['text']}\n"