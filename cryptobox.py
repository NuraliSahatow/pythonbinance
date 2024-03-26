import hmac
import time
import hashlib
import requests
import json
from urllib.parse import urlencode

with open('config.json') as config_file:
    config = json.load(config_file)

KEY = 'ZwrV5eNRiAQZL509HyGibZaCwmyi6U16xXFhFg9tmHbJ2PaAnAlAGqkCY7Fwt4ow'
SECRET = 'GJlJc8y6fs7e14gZ4lQhc5g5PWqGOPDzssZ3RkyuVqCcUS1Q6pfJE9tWvV1Lhx8B'
BASE_URL = 'https://api.binance.com'


class BinanceConnect(object):
    @staticmethod
    def hashing(query_string):
        return hmac.new(SECRET.encode("utf-8"), query_string.encode("utf-8"), hashlib.sha256).hexdigest()

    @staticmethod
    def get_timestamp():
        response = BinanceConnect.send_public_request("/api/v3/time")
        server_time = response['serverTime']
        return server_time

    @staticmethod
    def dispatch_request(http_method):
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json;charset=utf-8", "X-MBX-APIKEY": KEY})
        return {
            "GET": session.get,
            "DELETE": session.delete,
            "PUT": session.put,
            "POST": session.post,
        }.get(http_method, "GET")

    @staticmethod
    def send_signed_request(http_method, url_path, payload={}):
        query_string = urlencode(payload)
        if query_string:
            query_string = "{}&timestamp={}".format(query_string, BinanceConnect.get_timestamp())
        else:
            query_string = "timestamp={}".format(BinanceConnect.get_timestamp())

        url = BASE_URL + url_path + "?" + query_string + "&signature=" + BinanceConnect.hashing(query_string)
        print("{} {}".format(http_method, url))
        params = {"url": url, "params": {}}
        response = BinanceConnect.dispatch_request(http_method)(**params)
        return response.json()

    @staticmethod
    def send_public_request(url_path, payload={}):
        query_string = urlencode(payload, True)
        url = BASE_URL + url_path
        if query_string:
            url = url + "?" + query_string
        print("{}".format(url))
        response = BinanceConnect.dispatch_request("GET")(url=url)
        return response.json()

    @staticmethod
    @staticmethod
    def crypto_box(code):
        payload = {
            "code": code
        }
        response = BinanceConnect.send_signed_request("POST", "/api/v3/crypto_box", payload)
        return response



# Пример использования

# Создание экземпляра класса BinanceConnect
binance = BinanceConnect()

# Ввод кода для восстановления подарочной карты Binance
code = input('Введите код для восстановления подарочной карты Binance: ')

try:
    # Вызов метода API для восстановления подарочной карты Binance
    response = binance.crypto_box(code)
    # Обработка ответа от сервера Binance
    print(response)
except Exception as e:
    # Обработка исключений и ошибок
    print(f"Ошибка: {e}")
