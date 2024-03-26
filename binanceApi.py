import hmac
import time
import hashlib
import threading
import requests
import json
from urllib.parse import urlencode
import telebot

bot = telebot.TeleBot('6265387611:AAEUcwtVljQnrKBaeWieu5UlLvDRSpHqRqg')


@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    bot.reply_to(message, f'Привет! ID вашего чата: {chat_id}')

def noBalance(chat_id):
    bot.send_message(chat_id, "Баланс биткойна 0 - нечего продавать")


with open('config.json') as config_file:
    config = json.load(config_file)

KEY = config['BAPI_KEY']
SECRET = config['BAPI_SECRET']
BASE_URL = config['BBASE_URL']
COIN_TYPE = config['COIN_TYPE']
symbol = config['TradeSymbol']
limit = config['Limit']

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
        params = {"url": url, "params": {}}
        response = BinanceConnect.dispatch_request(http_method)(**params)
        return response.json()

    @staticmethod
    def send_public_request(url_path, payload={}):
        query_string = urlencode(payload, True)
        url = BASE_URL + url_path
        if query_string:
            url = url + "?" + query_string
        response = BinanceConnect.dispatch_request("GET")(url=url)
        return response.json()

class Binance(object):
    @staticmethod
    def get_market_depth():
        global min_bid_quantity
        global min_ask_quantity
        global max_ask_price
        global max_bid_price
        global min_bid_price
        global max_bid_quantity
        global min_ask_price
        url_path = "/api/v3/depth"
        payload = {"symbol": symbol, "limit": limit}
        response = BinanceConnect.send_public_request(url_path, payload)
        bids = response.get("bids", [])
        asks = response.get("asks", [])

        if bids and asks:
            print("Binance")
            min_bid = min(bids, key=lambda x: x[0])
            max_bid = max(bids, key=lambda x: x[0])
            min_bid_price, min_bid_quantity = min_bid
            max_bid_price, max_bid_quantity = max_bid
            print("Minimum Bid Price: {}, Quantity: {}".format(min_bid_price, min_bid_quantity))
            print("Maximum Bid Price: {}, Quantity: {}".format(max_bid_price, max_bid_quantity))
            max_ask = max(asks, key=lambda x: x[0])
            min_ask = min(asks, key=lambda x: x[0])

            max_ask_price, max_ask_quantity = max_ask
            min_ask_price, min_ask_quantity = min_ask
            print("Minimim Ask Price: {}, Quantity: {}".format(min_ask_price, max_ask_quantity))
            print("Maximum Ask Price: {}, Quantity: {}".format(max_ask_price, max_ask_quantity))
            return min_bid_quantity, max_bid_quantity, max_ask_price, min_ask_price,min_bid_price,min_ask_quantity
        else:
            print("Failed to retrieve order book for symbol: {}".format(symbol))

    @staticmethod
    def login_to_binance():
        response = BinanceConnect.send_signed_request("GET", "/api/v3/account")
        btc_balance = None
        usdt_balance = None
        for balance in response['balances']:
            if balance['asset'] == "BTC":
                btc_balance = float(balance['free'])
            elif balance['asset'] == COIN_TYPE:
                usdt_balance = float(balance['free'])

        return btc_balance, usdt_balance

    @staticmethod
    def execute_trade_strategy(chat_id):
        btc_balance, usdt_balance = Binance.login_to_binance()
        bot.send_message(chat_id, f"Balance of BTC: {btc_balance:.8f}")
        bot.send_message(chat_id, f"Balance of USDT: {usdt_balance:.8f}")
        print(f"Balance of BTC: {btc_balance:.8f}")
        print(f"Balance of USDT: {usdt_balance:.8f}")
        try:
            # Write profit_percent to percent.txt
            with open('percent.txt', 'w') as file:
                file.write(f"Balance of BTC: {btc_balance:.8f}\n")
                file.write(f"Balance of USDT: {usdt_balance:.8f}\n")
        except Exception as e:
            print("Error writing to file: ", str(e))

        if (float(btc_balance) <1 and float(usdt_balance) > float(min_ask_price)):
            # Buy BTC using USDT
            print("BUY")
            quantities_to_buy = [1]  # Adjust this calculation based on the current price of BTC
            Binance.buy_from_seller_batch(quantities_to_buy,chat_id="5566384153")
            # ... handle the buy response ...
        elif (float(btc_balance) > float(min_ask_quantity)):
            print("SELL")
            quantities_to_sell = [float(btc_balance)]
            Binance.sell_to_buyer_batch(quantities_to_sell,chat_id="5566384153")
        else:
            print("NO TRADES")
    @staticmethod
    def place_limit_order(symbol, side, price, quantity):
        url_path = "/api/v3/order"
        payload = {
            "symbol": symbol,
            "side": side,
            "type": "LIMIT",
            "timeInForce": "GTC",
            "price": price,
            "quantity": quantity
        }
        response = BinanceConnect.send_signed_request("POST", url_path, payload)
        print("Prices {}".format(response))
        return response

    @staticmethod
    def check_seller_quantity(quantity):
        url_path = "/api/v3/depth"
        payload = {"symbol": symbol, "limit": limit}
        response = BinanceConnect.send_public_request(url_path, payload)
        asks = response.get("asks", [])
        if asks:
            for ask in asks:
                ask_price, ask_quantity = ask
                if float(ask_quantity) >= float(quantity):
                    print("Seller with sufficient quantity found")
                    return True
        else:
            print("Failed to retrieve order book for symbol: {}".format(symbol))

        print("No seller with sufficient quantity found")
        return False

    @staticmethod
    def calculate_profit(initial_balance, current_balance):
        profit_percent = ((current_balance - initial_balance) / initial_balance) * 100
        return profit_percent

    @staticmethod
    def buy_from_seller_batch(quantities_to_buy,chat_id):
        responses = []
        for quantity in quantities_to_buy:
            url_path = "/api/v3/depth"
            payload = {"symbol": symbol, "limit": limit}
            response = BinanceConnect.send_public_request(url_path, payload)
            asks = response.get("asks", [])
            askk = 0.0
            if asks:
                for ask in asks:
                    ask_price, ask_quantity = ask
                    if float(ask_quantity) >= float(quantity):
                        if float(max_ask_price) > float(ask_price):
                            bot.send_message(chat_id, f"Покупка {ask_quantity} от продавца с ценой {min_ask_price}")

                            Binance.place_limit_order(symbol, "BUY", str(min_ask_price), str(ask_quantity))
                            print("Buying {} from seller with price {}...".format(quantity, min_ask_price))
                            askk += float(ask_price) * float(quantity)
                            responses.append((True, askk))
                        break
                    else:
                        print("Buying all available assets ({}) from seller with price {}...".format(ask_quantity, ask_price))
                        # Размещаем ордер с скорректированной ценой
                        askk += float(ask_price) * float(ask_quantity)
                        rounded_price = round(float(askk), 3)
                        # Ваш код для покупки у продавца с указанной ценой и количеством
                        print(Binance.place_limit_order(symbol, "BUY", ask_price, ask_quantity))
                        quantity -= float(ask_quantity)
            else:
                print("Failed to retrieve order book for symbol: {}".format(symbol))

            if not askk:
                print("No seller with sufficient quantity found")
                responses.append((False, askk))

        return responses
    @staticmethod
    def sell_to_buyer_batch(quantities_to_sell,chat_id):
        btc_balance, usdt_balance = Binance.login_to_binance()
        responses = []
        for quantity in quantities_to_sell:
            url_path = "/api/v3/depth"
            payload = {"symbol": symbol, "limit": limit}
            response = BinanceConnect.send_public_request(url_path, payload)
            bids = response.get("asks", [])
            askk = 0.0
            if bids:
                for bid in bids:
                    bid_price, bid_quantity = bid
                    if (float(bid_quantity) >= float(quantity)):
                        if (float(max_ask_price) < float(bid_price) ):
                            print(max_ask_price, bid_price)
                            bot.send_message(chat_id, f"Продажа {bid_quantity} покупателью с ценой {bid_price}")
                            bot.send_message(chat_id, f"Баланс Биткойнов {btc_balance}, Баланс USDT{usdt_balance}")
                            bot.send_message(chat_id, f"Максимальная цена продажи {max_bid_price}, Минимальная цена покупки {min_ask_price}")
                            Binance.place_limit_order(symbol, "SELL", str(bid_price), str(bid_quantity))
                            print("Selling {} to buyer with price {}...".format(quantity, bid_price))
                        break
                    else:
                        if (float(max_ask_price) < float(bid_price) ):
                            print(max_ask_price, bid_price)
                            print("Selling all available assets ({}) to buyyer with price {}...".format(bid_quantity, bid_price))
                            bot.send_message(chat_id, f"Продажа всех доступных активов {bid_quantity} покупателью с ценой {bid_price}")
                            bot.send_message(chat_id, f"Баланс Биткойнов {btc_balance}, Баланс USDT{usdt_balance}")
                            bot.send_message(chat_id, f"Максимальная цена продажи {max_bid_price}, Минимальная цена покупки {min_ask_price}")
                            # Размещаем ордер с скорректированной ценой
                            rounded_price = round(float(askk), 3)
                            # Ваш код для покупки у продавца с указанной ценой и количеством
                            print(Binance.place_limit_order(symbol, "SELL", max_ask_price, bid_quantity))
                            quantity -= float(bid_quantity)
            else:
                print("Failed to retrieve order book for symbol: {}".format(symbol))

            if not askk:
                print("No seller with sufficient quantity found")
                responses.append((False, askk))

        return responses

    @staticmethod
    def run_trading_bot(chat_id):
        while True:
                btc_balance, usdt_balance = Binance.login_to_binance()
                Binance.get_market_depth()

                if (float(btc_balance) < 1 and float(usdt_balance) > float(min_ask_price)):
                    Binance.execute_trade_strategy(chat_id)
                elif (float(btc_balance) > float(min_ask_quantity)):
                    Binance.execute_trade_strategy(chat_id)


    @staticmethod
    def start_trading_bot(num_threads):
            chat_id = '5566384153'
            threads = []

            for _ in range(num_threads):
                trading_thread = threading.Thread(target=Binance.run_trading_bot, args=(chat_id,))
                threads.append(trading_thread)
                trading_thread.start()

            for thread in threads:
                thread.join()

    # Запустить 3 потока (вы можете выбрать свое количество)
Binance.start_trading_bot(num_threads=1)


bot.polling()
