from __future__ import unicode_literals  # Импорт модуля для поддержки юникодных строк

import time  # Импорт модуля для работы со временем
import hashlib  # Импорт модуля для работы с хешированием
import json as complex_json  # Импорт модуля для работы с JSON
import urllib3  # Импорт модуля для выполнения HTTP-запросов
import json  # Импорт модуля для работы с JSON
from urllib3.exceptions import InsecureRequestWarning  # Импорт исключения для игнорирования предупреждений безопасности

urllib3.disable_warnings(InsecureRequestWarning)  # Отключение предупреждений безопасности
http = urllib3.PoolManager(timeout=urllib3.Timeout(connect=1, read=2))  # Создание пула HTTP-соединений
with open('config.json') as config_file:
    config = json.load(config_file)
TradeSymbol = config['TradeSymbol']
Limit = config['Limit']
Count = config['Count']
class RequestClient(object):
    __headers = {  # Заголовки по умолчанию для запросов
        'Content-Type': 'application/json; charset=utf-8',
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36'
    }

    def __init__(self, headers={}):
        self.access_id = config['CAPI_KEY']  # замените на свой идентификатор доступа
        self.secret_key = config['CAPI_SECRET'] # замените на свой секретный ключ
        self.url = config['CBASE_URL']  # URL-адрес API
        self.headers = self.__headers  # Заголовки запроса по умолчанию
        self.headers.update(headers)  # Обновление заголовков с пользовательскими значениями

    @staticmethod
    def get_sign(params, secret_key):
        sort_params = sorted(params)  # Сортировка параметров
        data = []
        for item in sort_params:
            data.append(item + '=' + str(params[item]))  # Формирование строки параметров в виде "key=value"
        str_params = "{0}&secret_key={1}".format('&'.join(data), secret_key)  # Конкатенация параметров и секретного ключа
        token = hashlib.md5(str_params.encode('utf-8')).hexdigest().upper()  # Получение хэша MD5
        return token

    def set_authorization(self, params):
        params['access_id'] = self.access_id  # Добавление идентификатора доступа к параметрам запроса
        params['tonce'] = int(time.time() * 1000)  # Добавление временной метки к параметрам запроса
        self.headers['AUTHORIZATION'] = self.get_sign(params, self.secret_key)  # Генерация подписи и добавление её к заголовкам

    def request(self, method, url, params={}, data='', json={}):
        method = method.upper()  # Преобразование метода запроса в верхний регистр
        if method in ['GET', 'DELETE']:
            self.set_authorization(params)  # Установка авторизации для GET и DELETE запросов
            result = http.request(method, url, fields=params, headers=self.headers)  # Выполнение GET или DELETE запроса
        else:
            if data:
                json.update(complex_json.loads(data))  # Обновление JSON-объекта данными из строки data
            self.set_authorization(json)  # Установка авторизации для остальных запросов
            encoded_data = complex_json.dumps(json).encode('utf-8')  # Кодирование JSON-объекта в байтовую строку
            result = http.request(method, url, body=encoded_data, headers=self.headers)  # Выполнение запроса с телом данных
        return result

class CoinEx(object):
    @staticmethod
    def get_market_depth():
        request_client = RequestClient()  # Создание клиента для выполнения запросов
        params = {'market': TradeSymbol, 'merge': Count, 'limit': Limit}  # Параметры запроса
        response = request_client.request('GET', f'{request_client.url}/v1/market/depth', params=params)  # Выполнение GET запроса на получение глубины рынка

        data = json.loads(response.data.decode('utf-8'))  # Распаковка данных ответа в формате JSON
        if response.status == 200 and data['code'] == 0:  # Проверка успешности запроса
            print(f"Symbol: {TradeSymbol}")
            print("Bids:")
            bids = data['data']['bids']  # Извлечение предложений о покупке (Bids)
            min_bid_price = min(float(bid[0]) for bid in bids)  # Нахождение минимальной цены предложения о покупке
            print(f"Minimum Bid Price: {min_bid_price}")

            print("Asks:")
            asks = data['data']['asks']  # Извлечение предложений о продаже (Asks)
            max_ask_price = max(float(ask[0]) for ask in asks)  # Нахождение максимальной цены предложения о продаже
            print(f"Maximum Ask Price: {max_ask_price}")
        else:
            print(f"Error retrieving market depth: {data['message']}")  # Вывод сообщения об ошибке при получении глубины рынка

    @staticmethod
    def place_limit_order(market, type, amount, price):
        request_client = RequestClient()
        data = {
            'access_id': request_client.access_id,
            'tonce': int(time.time() * 1000),
            'account_id': 0,
            'market': market,
            'type': type,
            'amount': amount,
            'price': price
        }
        request_client.set_authorization(data)
        response = request_client.request('POST', f'{request_client.url}/v1/order/limit', json=data)

        # Print the response data for debugging


        try:
            data = json.loads(response.data.decode('utf-8'))
            if response.status == 200 and data['code'] == 0:

                return data['data']
                print(data)
            else:
                print(data)
                return None
        except json.decoder.JSONDecodeError as e:
            print("Error decoding JSON response:", str(e))
            return None
    @staticmethod
    def get_account_info():
        request_client = RequestClient()  # Создание клиента для выполнения запросов
        response = request_client.request('GET',
                                          f'{request_client.url}/v1/balance/info')  # Выполнение GET запроса на получение информации об аккаунте

        data = json.loads(response.data.decode('utf-8'))  # Распаковка данных ответа в формате JSON
        if response.status == 200 and data['code'] == 0:  # Проверка успешности запроса
            account_info = data['data']
            print(f"Account Info: {account_info}")
        else:
            print(
                f"Error retrieving account info: {data['message']}")  # Вывод сообщения об ошибке при получении информации об аккаунте
# Пример использования
market = 'BTCUSDT'
type = 'buy'
amount = 1.0
price = 30000.0
CoinEx.place_limit_order(market, type, amount, price)
