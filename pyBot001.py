from time import time
import GLOBAL
# from GLOBAL import ENTRADE_CLIENT, DNSE_CLIENT
from pyBot import pyBot
import pandas as pd
import numpy as np
import ta
from Utils import*



'''
This is a sample bot file.
You can create your own bot by copying this file and modifying it.
Make sure to follow the structure and conventions used in this file.
You can create multiple bots and run them simultaneously.
Each bot should have its own logic and strategy.
Each bot should have its own entry point and be able to run independently.

'''


class pyBotMACD(pyBot):
    def __init__(self, name = "MACD_Bot", 
                 description: str = "This is a sample bot that uses MACD indicator to trade.",
                 version: str = "1.0",
                 author: str = "Nguyen van Cong",
                 timeframe: str = "m5",
                 symbol: str = "VN30F1M"):
        
        super().__init__(name)
        self.description = description
        self.version = version
        self.author = author
        self.timeframe = timeframe

        self.tradingPlatform ="DNSE"     # "DNSE" hoặc "ENTRADE"
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
            # if not self.is_trading_time():
            #     self.logger.info("Outside trading hours. Bot is inactive.")
            #     cprint("Outside trading hours. Bot is inactive.")
            #     return
            
            #kiểm tra xem số hđ đang mở đang active (mở) đã vượt quá số lượng cho phép chưa ?
            if self.getTotalOpenQuanity_DNSE() >= self.maxOpenTrades:
                self.logger.info(f"Số lượng hợp đồng đang mở đã đạt số lượng tối đa [{self.maxOpenTrades} HĐ] cho phép.")
                # cprint(f"Số lượng hợp đồng đang mở đã đạt số lượng tối đa [{self.maxOpenTrades} HĐ] cho phép.")
                return

            #cập nhật các biến động như tổng số hđ hiện tại vào trong bot, trước khi tính netprofit
            self.orderQuantity = self.getTotalOpenQuanity_DNSE()
            
            #cập nhật unrealised net profit
            self.Calculate_UnrealisedNetProfit()



            #kiểm tra tín hiệu mua/bán
            action = self.check_for_signals()
            
            action = "BUY"  #for testing only

            if action is not None:
                try:
                    self.logger.info(f"Signal detected: {action}")
                    
                    if self.tradingPlatform.upper() == "DNSE":
                        self.logger.info(f"Trading platform used : DNSE")
                        self.execute_trade_DNSE(action)
                    else:
                        self.logger(f"Trading platform used : ENDTRADE")
                        self.execute_trade_entrade(action)
                except Exception as e:
                    self.logger.error(f"Lỗi khi đặt lệnh: {e}")
                    pass
    
    def check_for_signals(self):
        '''
        Tính toán các indicators, kiểm tra các điều kiện và trả về tín hiệu mua/bán nếu có
        action = "BUY" hoặc "SELL", CLOSEBUY, CLOSESELL
        Nếu không có tín hiệu thì trả về None
        '''
        #kiểm tra chuỗi data có đủ dài để tính toán indicator không
        self.logger.info(f"Độ dài chuỗi dữ liệu nến '{self.timeframe}': {len(self.marketData[self.timeframe])}")

        if self.marketData is None or len(self.marketData[self.timeframe]) < self.macd_long_window:
            self.logger.warning("Không đủ dữ liệu nến để kiểm tra tín hiệu cho bot.")
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
                self.logger.info(f"Tín hiệu {action} |last_macd ={self.last_macd}|last_signal={self.last_signal}|last_RSI={self.last_RSI}|last_ADX={self.last_ADX}")
                
            # Điều kiện bán
            elif ((self.cross(signal,macd) and self.last_RSI <= self.upperBound)
                    or (
                        self.last_signal > self.last_macd and
                        self.cross(45, rsi)
                    )):
                action = "SELL"
                self.logger.info(f"Tín hiệu {action} |last_macd ={self.last_macd}|last_signal={self.last_signal}|last_RSI={self.last_RSI}|last_ADX={self.last_ADX}")

            # Điều kiện đóng mua
            elif (self.position == "BUY" and 
                    (self.last_macd < self.last_signal or 
                    self.last_RSI > self.upperBound)):
                action = "CLOSEBUY"
                self.logger.info(f"Tín hiệu {action} |last_macd ={self.last_macd}|last_signal={self.last_signal}|last_RSI={self.last_RSI}|last_ADX={self.last_ADX}")

            # Điều kiện đóng bán
            elif (self.position == "SELL" and 
                    (self.last_macd > self.last_signal or 
                    self.last_RSI < self.lowerBound)):
                action = "CLOSESELL"
                self.logger.info(f"Tín hiệu {action} |last_macd ={self.last_macd}|last_signal={self.last_signal}|last_RSI={self.last_RSI}|last_ADX={self.last_ADX}")
            else:
                action = None  # Không có tín hiệu
            return action
        except Exception as e:
            self.logger.error(f"Error in signal calculation: {e}")
            return None
        
    
    def execute_trade_entrade(self, action, is_demo = True):
        '''
        Thực hiện lệnh mua/bán dựa trên tín hiệu từ check_for_signals
        action = "BUY" hoặc "SELL", CLOSEBUY, CLOSESELL
        '''
        # kiểm tra số deal đang mở đã vượt quá max open trades allowed chưa?

        # lấy giá hiện tại khi có tín hiệu
        if self.orderPriceType == "MTL":
            self.orderPrice = None
        else:
            self.orderPrice = self.marketData[self.timeframe][4]  # Lấy giá đóng cửa mới nhất

        if action == "BUY":

            self.logger.info(f"[ENDTRADE] Thực hiện đặt {self.trade_size} hợp đồng LONG tại giá {self.orderPrice if self.orderPrice is not None else 'MTL'}")
            # Thực hiện lệnh mua ở đây
            result = GLOBAL.ENTRADE_CLIENT.Order(GLOBAL.VN30F1M, "NB", self.orderPrice, None, self.trade_size, self.orderPriceType, is_demo)
            
            try:
                self.position = "BUY"
                deals = GLOBAL.ENTRADE_CLIENT.GetActiveDeals()
                # self.logger.info(f"Active deals after BUY: {deals}")
                for deal in deals:
                    self.order_id = deal.get("id")
                    self.order_entryprice = deal.get("breakEvenPrice")
                    self.order_side = deal.get("side")
                    self.orderQuantity = deal.get("openQuantity")
            except:
                pass

        elif action == "SELL":
            
            self.logger(f"[ENDTRADE] Thực hiện đặt {self.trade_size} hợp đồng SHORT tại giá {self.orderPrice if self.orderPrice is not None else 'MTL'}")
            # Thực hiện lệnh bán ở đây
            result = GLOBAL.ENTRADE_CLIENT.Order(GLOBAL.VN30F1M, "NS", self.orderPrice, None, self.trade_size, self.orderPriceType, is_demo)

            try:
                self.position = "SELL"
                deals = GLOBAL.ENTRADE_CLIENT.GetActiveDeals()
                # cprint(f"Active deals after BUY: {deals}")
                for deal in deals:
                    self.order_id = deal.get("id")
                    self.order_entryprice = deal.get("breakEvenPrice")
                    self.order_side = deal.get("side")
                    self.orderQuantity = deal.get("openQuantity")
            except:
                pass

                
        elif action == "CLOSEBUY":
            if self.position == "BUY":
                self.logger.info(f"[ENDTRADE] Đóng tất cả các lệnh, lý do = {action}")
                # Thực hiện lệnh đóng mua ở đây
                result = GLOBAL.ENTRADE_CLIENT.CloseAllDeals(is_demo)
                self.position = None
                self.order_entryprice = None
                self.order_id = None
                self.order_side = None
                self.orderQuantity = None
            else:
                self.logger.error("No BUY position to close.")

        elif action == "CLOSESELL":
            if self.position == "SELL":
                self.logger.info(f"[ENDTRADE] Đóng tất cả các lệnh, lý do = {action}")
                # Thực hiện lệnh đóng mua ở đây
                result = GLOBAL.ENTRADE_CLIENT.CloseAllDeals(is_demo)
                self.position = None
                self.order_entryprice = None
                self.order_id = None
                self.order_side = None
                self.orderQuantity = None
            else:
                self.logger.info("No SELL position to close.")
        else:
            self.logger.info("No valid action to execute.")
    
    def execute_trade_DNSE(self, action):
        '''
        Thực hiện lệnh mua/bán dựa trên tín hiệu từ check_for_signals
        action = "BUY" hoặc "SELL", CLOSEBUY, CLOSESELL
        '''
        # kiểm tra số deal đang mở đã vượt quá max open trades allowed chưa?

        # lấy giá hiện tại khi có tín hiệu
        if self.orderPriceType == "MTL":
            self.orderPrice = None
        else:
            self.orderPrice = self.marketData[self.timeframe][4]  # Lấy giá đóng cửa mới nhất


        if action == "BUY":
                
            self.logger.info(f"[DNSE] Thực hiện đặt {self.trade_size} hợp đồng LONG tại giá {self.orderPrice if self.orderPrice is not None else 'MTL'}")
            # Thực hiện lệnh mua ở đây
            result = GLOBAL.DNSE_CLIENT.Order( symbol=self.symbol,
                                                account = self.accountNo,
                                                side = "NB",
                                                price = self.orderPrice,
                                                loan = self.loanpackageid,
                                                volume = self.trade_size,
                                                order_type = self.orderPriceType)
            
            try:
                self.position = "BUY"
                deals = GLOBAL.ENTRADE_CLIENT.GetActiveDeals()
                # cprint(f"Active deals after BUY: {deals}")
                for deal in deals:
                    self.order_id = deal.get("id")
                    self.order_entryprice = deal.get("breakEvenPrice")
                    self.order_side = deal.get("side")
                    self.orderQuantity = deal.get("openQuantity")
            except:
                pass

        elif action == "SELL":

            self.logger.info(f"[DNSE] Thực hiện đặt {self.trade_size} hợp đồng SHORT tại giá {self.orderPrice if self.orderPrice is not None else 'MTL'}")
            cprint(f"[DNSE] Thực hiện đặt {self.trade_size} hợp đồng SHORT tại giá {self.orderPrice}")
            # Thực hiện lệnh bán ở đây
            result = GLOBAL.DNSE_CLIENT.Order( symbol=self.symbol,
                                                account = self.accountNo,
                                                side = "NS",
                                                price = self.orderPrice,
                                                loan = self.loanpackageid,
                                                volume = self.trade_size,
                                                order_type = self.orderPriceType)

            try:
                self.position = "SELL"
                deals = GLOBAL.ENTRADE_CLIENT.GetActiveDeals()
                # cprint(f"Active deals after BUY: {deals}")
                for deal in deals:
                    self.order_id = deal.get("id")
                    self.order_entryprice = deal.get("breakEvenPrice")
                    self.order_side = deal.get("side")
                    self.orderQuantity = deal.get("openQuantity")
            except:
                pass

                
        elif action == "CLOSEBUY":
            # Thực hiện lệnh đóng mua ở đây
                self.logger.info(f"[DNSE] Đóng tất cả các lệnh, lý do = {action}")
                cprint(f"[DNSE] Đóng tất cả các lệnh, lý do = {action}")
                result = GLOBAL.DNSE_CLIENT.CloseAllDeals()
                self.position = None
                self.order_entryprice = None
                self.order_id = None
                self.order_side = None
                self.orderQuantity = None

        elif action == "CLOSESELL":
            # Thực hiện lệnh đóng mua ở đây
                self.logger.info(f"[DNSE] Đóng tất cả các lệnh, lý do = {action}")
                cprint(f"[DNSE] Đóng tất cả các lệnh, lý do = {action}")
                result = GLOBAL.DNSE_CLIENT.CloseAllDeals()
                self.position = None
                self.order_entryprice = None
                self.order_id = None
                self.order_side = None
                self.orderQuantity = None
        else:
            self.logger.info("No valid action to execute.")
    
    def getTotalOpenQuanity_DNSE(self) -> int:
        '''
        Mục đích lấy tổng số hợp động đang mở.
        '''
        if self.dnseClient is not None:
            return self.dnseClient.GetTotalOpenQuantity()
        else:
            return 0



# if __name__ == "__main__":
    # df = generate_market_data()
    # bot = pyBotMACD()
    # bot.timeframe = "m1"
    # bot.marketData = df
    # bot.trade_size =1
    # bot.run()
    # bot.cprint_dealBot()