from binanceApi import *
from coinexApi import  *
# Вызов функции login_to_binance() для входа в аккаунт на Binance

marketc = CoinEx.get_market_depth()
#marketb = Binance.get_market_depth()
print(marketc)
# Вывод результата