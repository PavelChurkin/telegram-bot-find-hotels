import re
import time
import requests
from requests.exceptions import ConnectTimeout
import aiohttp
import json
import asyncio

from logs.log_info import logger
from loader import dp
from config_data.config import RAPID_API_KEY


def response_checker(url, querystring, name: str):
    try:
        # online mode
        headers = {"X-RapidAPI-Host": "hotels4.p.rapidapi.com",
                   "X-RapidAPI-Key": RAPID_API_KEY}
        response = requests.request("GET", url, headers=headers, params=querystring, timeout=15)
        if response.status_code == 200:
            data = json.loads(response.text)
        else:
            logger.warning('! Нет ответа от Rapidapi')
            return 1

        # offline mode
        # if name == 'search_city':
        #     with open('hotels/_test2_сities.json', 'r', encoding='utf-8') as f:
        #         data = json.load(f)
        # if name == 'search_hotels':
        #     with open('hotels/_test5_hotels.json', 'r', encoding='utf-8') as f:
        #         data = json.load(f)
        # if name == 'search_photos':
        #     with open('hotels/_test6_photos.json', 'r', encoding='utf-8') as f:
        #         data = json.load(f)

        return data
    except ConnectTimeout as err:
        print('Время ожидания превышено. Ответ не получен - ', err)


# headers = {"X-RapidAPI-Host": "hotels4.p.rapidapi.com",
#            "X-RapidAPI-Key": RAPID_API_KEY}
# url = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"
# querystring = {"id": f"{629308}"}
# response = requests.request("GET", url, headers=headers, params=querystring, timeout=15)
# data = json.loads(response.text)
# with open('_test7_pfoto_hotels.json', 'w', encoding='utf-8') as file:
#     json.dump(data, file, indent=4, ensure_ascii=False)


@logger.catch()
async def search_city(input_city: str):
    url = "https://hotels4.p.rapidapi.com/locations/v2/search"
    querystring = {"query": f"{input_city}", "locale": "ru_RU", "currency": "RUB"}
    data = response_checker(url, querystring, 'search_city')

    # span ликвидатор
    [data['suggestions'][0]['entities'][i].update(
        caption=', '.join(re.findall('([а-яА-Я]+)', data['suggestions'][0]['entities'][i]['caption'])))
        for i, j in enumerate(data['suggestions'][0]['entities'])]
    # Подготовка для записи в FSM
    json_city = [{'destinationId': i['destinationId'],
                  'caption': i['caption'],
                  'name': i['name']}
                 for i in data['suggestions'][0]['entities']]
    state = dp.get_current().current_state()
    await state.update_data(json_city=json_city)
    print("data in FSM")
    return False if len(data['suggestions'][0]['entities']) == 0 else True


@logger.catch()
async def search_hotels(dct: dict):
    url = "https://hotels4.p.rapidapi.com/properties/list"
    date = [time.strftime("%Y-%m-%d", time.localtime(dct['unix_date_in'] * 86400)),
            time.strftime("%Y-%m-%d", time.localtime(dct['unix_date_out'] * 86400))]
    page_number = 1
    querystring = {"destinationId": dct['city_id'], "pageNumber": page_number, "pageSize": "25",
                   "checkIn": date[0], "checkOut": date[1], "adults1": dct['num_peoples'],
                   "sortOrder": "PRICE", "locale": "ru_RU", "currency": "RUB", "landmarkIds": "City Center"}
    if dct['selected_command'] == 'highprice':
        querystring.update({"sortOrder": 'PRICE_HIGHEST_FIRST'})
    if dct['selected_command'] == 'bestdeal':
        price = dct['interval_price'].split(' - ')
        querystring.update({"sortOrder": 'DISTANCE_FROM_LANDMARK', 'priceMin': int(price[0]), 'priceMax': int(price[1])})

    # adults1 - количество взрослых в одном номере, adults2 - во втором, до 8ми, children1 - сколько лет
    # landmark - в ответе - можно сортировать по нему
    # sortOrder - BEST_SELLER | STAR_RATING_HIGHEST_FIRST | STAR_RATING_LOWEST_FIRST |
    # DISTANCE_FROM_LANDMARK | GUEST_RATING | PRICE_HIGHEST_FIRST | PRICE
    # Также есть themeIds, amenityIds, accommodationIds, guestRatingMin, landmarkIds = айди места
    # logger.debug(f'querystring = {querystring}')

    data = response_checker(url, querystring, 'search_hotels')['data']['body']['searchResults']['results']
    list_hotels = [{'hotel_id': i_dict['id'],
                    'hotel_name': i_dict['name'],
                    'address': f'{i_dict["address"].get("postalCode")}, {i_dict["address"].get("streetAddress")}',
                    'url': f'https://www.hotels.com/ho{i_dict["id"]}',
                    'map_point': f'http://maps.google.com/maps?z=12&t=m&q=loc:{i_dict["coordinate"]["lat"]},{i_dict["coordinate"]["lon"]}',
                    'center': float(re.sub(',', '.', i_dict['landmarks'][0]['distance'][:-3])),
                    'price': 0,
                    'interval_date': dct['interval_date'],
                    'rate': '0'}
                   for i_dict in data]
    # if dct['selected_command'] == 'bestdeal':
    #     list_hotels = filter(lambda x: x['center'] < dct['distance_center'], list_hotels)
    # logger.info(list_hotels)
    for i, i_dict in enumerate(list_hotels):
        if data[i].get('guestReviews'):
            i_dict.update(rate=f"{data[i]['guestReviews']['unformattedRating']}/10 по {data[i]['guestReviews']['total']} отзывам")
        if data[i].get('ratePlan'):
            i_dict.update(price=int(data[i]['ratePlan']['price']['exactCurrent']))
    return list_hotels


# синхронно
@logger.catch()
def search_photos(hotel_id: int, quantity: int):
    url = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"
    querystring = {"id": f"{hotel_id}"}
    data = response_checker(url, querystring, 'search_photos')
    lst = [str(i_image['sizes'][int(len(i_image['sizes']) - len(i_image['sizes']) * (quantity / 4))]['suffix'])
           for i_image in data['hotelImages']]
    lst2 = [i_image['baseUrl'].replace('{size}', lst[i])
            for i, i_image in enumerate(data['hotelImages'])]
    return lst2


# асинхронно
@logger.catch()
async def a_search_photos(client, url, query_params, quantity: int, headers):
    async with client.get(url, params=query_params, headers=headers) as response:
        data = await response.json()
        # data = json.loads(text)
        lst = [str(i_image['sizes'][int(len(i_image['sizes']) - len
        (i_image['sizes']) * (quantity / 4))]['suffix'])
               for i_image in data['hotelImages']]  # настройка качества
        result = [i_image['baseUrl'].replace('{size}', lst[i])
                  for i, i_image in enumerate(data['hotelImages'])]     # готовые ссылки
        return result


@logger.catch()
async def get_all_photos(hotels: list, quantity: int):
    timeout = aiohttp.ClientTimeout(total=22)
    conn = aiohttp.TCPConnector(limit_per_host=4)
    headers = {"X-RapidAPI-Host": "hotels4.p.rapidapi.com",
               "X-RapidAPI-Key": RAPID_API_KEY}
    async with aiohttp.ClientSession(timeout=timeout, connector=conn) as client:
        tasks = [a_search_photos(client, "https://hotels4.p.rapidapi.com/properties/get-hotel-photos",
                                 {"id": f"{i_hotel['hotel_id']}"},
                                 quantity,
                                 headers)
                 for i_hotel in hotels]
        # logger.debug(tasks)
        return await asyncio.gather(*tasks)     # список списков ссылок на фотки
