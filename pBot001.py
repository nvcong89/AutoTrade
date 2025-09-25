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

        self.accountNo = None   # Mã tiểu khoản dùng để trade bằng bot
        self.maxOpenTrades = 1  # set max open trades allowed


        #khai báo các biến riêng cho bot MACD
        self.macd_short_window = 23
        self.macd_long_window = 26
        self.macd_signal_window = 24
        self.last_macd = None
        self.last_signal = None
        self.last_hist = None

        #khai báo biến cho RSI
        self.periodRSI = 8
        self.last_RSI = None
        self.upperBound = 45
        self.lowerBound = 40

        #khai báo biến cho ADX
        self.periodADX = 8
        self.last_ADX = None
        self.levelADXBuy = 22
        self.levelADXSell = 25


        
    def run(self):

        #thực hiện các hành động của bot
        if self.is_active:
            # kiểm tra bot có đang trong giờ giao dịch không
            if not self.is_trading_time():
                self.log("Outside trading hours. Bot is inactive.")
                return
            
            #kiểm tra tín hiệu mua/bán
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
        highPrices = self.getBarSeries("m5","H")
        closePrices = self.getBarSeries("m5","C")
        openPrices = self.getBarSeries("m5","O")
        lowPrices = self.getBarSeries("m5","L")
        
        macd = ta.trend.MACD(close=closePrices,
                      window_slow=self.macd_long_window,
                      window_fast=self.macd_short_window,
                      window_sign=self.macd_signal_window,
                      fillna=True).macd().to_list()
        signal = ta.trend.MACD(close=closePrices,
                      window_slow=self.macd_long_window,
                      window_fast=self.macd_short_window,
                      window_sign=self.macd_signal_window,
                      fillna=True).macd_signal().to_list()
        
        self.last_macd = macd[-1]
        self.last_signal = signal[-1]

        #indicator RSI
        rsi = ta.momentum.RSIIndicator(close=closePrices,   
                                       window=self.periodRSI, 
                                       fillna=True).rsi().to_list()
        self.last_RSI = rsi[-1]
        
        # Indicator ADX
        adx = ta.trend.ADXIndicator(high=highPrices,
                                    low=lowPrices,
                                    close=closePrices,
                                    window=self.periodADX,
                                    fillna=True).adx().to_list()

        self.last_ADX = adx[-1]

        #=======================================================================
        # Kiểm tra các điều kiện để đưa ra tín hiệu mua/bán/đóng mua/đóng bán
        action = None        
        try:
            # Điều kiện mua
            if (self.last_macd > self.last_signal and 
                self.last_RSI >= self.lowerBound and 
                self.last_ADX > self.levelADXBuy):
                action = "BUY"
                
            # Điều kiện bán
            elif ((self.cross(signal,macd) and self.last_RSI <= self.upperBound)
                    or (
                        self.last_signal > self.last_macd and
                        self.cross(45, rsi)
                    )):
                action = "SELL"

            # Điều kiện đóng mua
            elif (self.position == "BUY" and 
                    (self.last_macd < self.last_signal or 
                    self.last_RSI > self.upperBound)):
                action = "CLOSEBUY"

            # Điều kiện đóng bán
            elif (self.position == "SELL" and 
                    (self.last_macd > self.last_signal or 
                    self.last_RSI < self.lowerBound)):
                action = "CLOSESELL"
            else:
                action = None  # Không có tín hiệu
            return action
        except Exception as e:
            self.log(f"Error in signal calculation: {e}")
            return None
        
    
    def execute_trade(self, action):
        '''
        Thực hiện lệnh mua/bán dựa trên tín hiệu từ check_for_signals
        action = "BUY" hoặc "SELL", CLOSEBUY, CLOSESELL
        '''
        # kiểm tra số deal đang mở đã vượt quá max open trades allowed chưa?

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
    
    # def getActiveDeals_Entrade(self, EntradeClient=None):
    #     if EntradeClient is not None:
    #         activeDeals = EntradeClient.GetActiveDeals()
    #         return activeDeals
    #     else:
    #         return None
    
    # def getActiveDeals_DNSE(self, DNSEClient=None):

    #     if DNSEClient is not None and self.accountNo is not None:
    #         activeDeals = DNSEClient.GetActiveDeals(self.accountNo)
    #         return activeDeals
    #     else:
    #         return None




if __name__ == "__main__":
    df = generate_market_data()
    bot = pBotMACD()
    bot.timeframe = "m1"
    bot.marketData = df
    bot.trade_size =1
    bot.run()
    bot.print_dealBot()




