from time import time
import GLOBAL
# from GLOBAL import ENTRADE_CLIENT, DNSE_CLIENT
from pBot import pBot
import pandas as pd
import numpy as np
import ta
from Utils import *


'''
This is a sample bot file.
You can create your own bot by copying this file and modifying it.
Make sure to follow the structure and conventions used in this file.
You can create multiple bots and run them simultaneously.
Each bot should have its own logic and strategy.
Each bot should have its own entry point and be able to run independently.

'''


class pBotMACD(pBot):
    def __init__(self, name: str = "MACD_Bot", 
                 description: str = "This is a sample bot that uses MACD indicator to trade.",
                 version: str = "1.0",
                 author: str = "Nguyen van Cong",
                 timeframe: str = "m5",
                 symbol: str = "VN30F1M"):
        super().__init__(name)
        super().__init__(description)
        super().__init__(version)
        super().__init__(author)
        super().__init__(timeframe)
        super().__init__(symbol)

        #khai báo các biến riêng cho bot MACD
        self.macd_short_window = 12
        self.macd_long_window = 26
        self.macd_signal_window = 9
        self.last_macd = None
        self.last_signal = None
        self.last_hist = None

        #khai báo biến cho RSI
        self.periodRSI = 8
        self.last_RSI = None
        self.RSI = None
        self.upperBound = 10
        self.lowerBound = 45

        
    def run(self):

        #thực hiện các hành động của bot

        if self.is_active:
            # self.get_latest_data()
            action = self.check_for_signals()
            if action is not None:
                self.log(f"Signal detected: {action}")
                self.execute_trade(action)
            # time.sleep(30)  # Wait for 30 seconds before checking again
    
    def check_for_signals(self):
        '''
        Tính toán các indicators, kiểm tra các điều kiện và trả về tín hiệu mua/bán nếu có
        action = "BUY" hoặc "SELL", CLOSEBUY, CLOSESELL
        Nếu không có tín hiệu thì trả về None
        '''
        #kiểm tra chuỗi data có đủ dài để tính toán indicator không
        print(f"Data length for {self.timeframe}: {len(self.marketData[self.timeframe])}")

        if self.marketData is None or len(self.marketData[self.timeframe]) < self.macd_long_window:
            self.log("Not enough data to check for signals.")
            return None
        
        # Tính toán Indicators
        #indicator MACD
        closePrices = pd.Series(data=self.marketData[self.timeframe][4],index=False, name = "close")  # Lấy giá đóng cửa từ marketData

        print(closePrices)  
        macd = ta.trend.MACD(close=closePrices,
                      window_slow=self.macd_long_window,
                      window_fast=self.macd_short_window,
                      window_sign=self.macd_signal_window,
                      fillna=True).macd().to_list()
        signal = ta.trend.MACD(close=self.marketData[4],
                      window_slow=self.macd_long_window,
                      window_fast=self.macd_short_window,
                      window_sign=self.macd_signal_window,
                      fillna=True).macd_signal().to_list()
        
        print(f"MACD: {macd[-5:]}")
        print(f"Signal: {signal[-5:]}")

        
        # latest_row = self.marketData.iloc[-1]
        # macd = latest_row['macd']
        # signal = latest_row['signal']
        # hist = latest_row['hist']
        # action = None
        # if self.last_macd is not None and self.last_signal is not None:
        #     if macd > signal and self.last_macd <= self.last_signal:
        #         action = "BUY"
        #     elif macd < signal and self.last_macd >= self.last_signal:
        #         action = "SELL"
        # self.last_macd = macd
        # self.last_signal = signal
        # self.last_hist = hist

        action = "BUY"
        return action
    
    def execute_trade(self, action):
        '''
        Thực hiện lệnh mua/bán dựa trên tín hiệu từ check_for_signals
        '''

        # lấy giá hiện tại khi có tín hiệu
        if self.orderPriceType == "MTL":
            self.orderPrice = None
        else:
            self.orderPrice = self.marketData[-1][4]  # Lấy giá đóng cửa mới nhất


        if action == "BUY":
            if self.position != "BUY":
                self.log("Executing BUY order")
                # Thực hiện lệnh mua ở đây
                result = GLOBAL.ENTRADE_CLIENT.Order(GLOBAL.VN30F1M, "NB", self.orderPrice, None, self.trade_size, self.orderPriceType, True)
                
                try:
                    self.position = "BUY"
                    deals = GLOBAL.ENTRADE_CLIENT.GetActiveDeals()
                    print(f"Active deals after BUY: {deals}")
                    for deal in deals:
                        self.order_id = deal.get("id")
                        self.order_entryprice = deal.get("breakEvenPrice")
                        self.order_side = deal.get("side")
                        self.orderQuantity = deal.get("openQuantity")
                except:
                    pass
            else:
                self.log("Already in LONG position, no action taken.")
        elif action == "SELL":
            if self.position != "SELL":
                self.log("Executing SELL order")
                # Thực hiện lệnh bán ở đây
                result = GLOBAL.ENTRADE_CLIENT.Order(GLOBAL.VN30F1M, "NS", self.orderPrice, None, self.trade_size, self.orderPriceType, True)

                try:
                    self.position = "SELL"
                    deals = GLOBAL.ENTRADE_CLIENT.GetActiveDeals()
                    print(f"Active deals after BUY: {deals}")
                    for deal in deals:
                        self.order_id = deal.get("id")
                        self.order_entryprice = deal.get("breakEvenPrice")
                        self.order_side = deal.get("side")
                        self.orderQuantity = deal.get("openQuantity")
                except:
                    pass
            else:
                self.log("Already in SHORT position, no action taken.")
                
        elif action == "CLOSEBUY":
            if self.position == "BUY":
                self.log("Closing BUY position")
                # Thực hiện lệnh đóng mua ở đây
                result = GLOBAL.ENTRADE_CLIENT.CloseAllDeals(is_demo=True)
                self.position = None
                self.order_entryprice = None
                self.order_id = None
                self.order_side = None
                self.orderQuantity = None
            else:
                self.log("No BUY position to close.")

        elif action == "CLOSESELL":
            if self.position == "SELL":
                self.log("Closing SELL position")
                # Thực hiện lệnh đóng mua ở đây
                result = GLOBAL.ENTRADE_CLIENT.CloseAllDeals(is_demo=True)
                self.position = None
                self.order_entryprice = None
                self.order_id = None
                self.order_side = None
                self.orderQuantity = None
            else:
                self.log("No SELL position to close.")
        else:
            self.log("No valid action to execute.")
    

if __name__ == "__main__":
    df = generate_market_data()
    bot = pBotMACD()
    bot.timeframe = "m1"
    bot.marketData = df
    bot.trade_size =1
    bot.run()
    bot.print_dealBot()




