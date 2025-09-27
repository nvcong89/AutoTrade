import GLOBAL
import datetime
from datetime import datetime, time
import os
# import time
# from time import time
import pandas as pd
from timezone_utils import is_trading_time_vietnam
from logger_config import setup_logger
import logging



class pyBot:
    def __init__(self, name: str):
        self.name = name
        self.is_active = True
        self.position = None  # Current position: "BUY", "SELL", or None
        self.last_action_time = 0  # Last time an action was taken
        self.action_interval = 0  # Minimum interval between actions in seconds
        self.symbol = None  #tên mã chứng khoán giao dịch

        #truyền 2 objects Entrade_Client và DNSe_Client vào trong bot
        self.entradeClient = None   # ENTRADEClient instance
        self.dnseClient = None        # DNSEClient instance

        # Trading hours in Vietnam timezone
        self.starttradingtime = time(9,1)  # Start trading time, time object (tương đương 9:01 AM) defaut
        self.endtradingtime = time(14,29)    # End trading time, time object (tương đương 2:29 PM) defaut
        self.maxOpenTrades = 1  # Maximum number of open trades allowed
        self.isTradingTime = False
        self.loanpackageid = None   # load package id

        self.marketData = None # Market data passed from pBot
        self.order_id = None  # Current order ID
        self.order_entryprice = None  # Entry price of the current order
        self.order_side = None  # Side of the current order: "NB" or "NS"
        self.orderPriceType = "MTL"  # Order price type: MTL, LO
        self.orderPrice = None  # Order price, None for market orders
        self.orderQuantity = None  # Order quantity

        self.unrealisedNetProfit = None #lưu giá trị net profit tạm thời

        self.spread = None      #get spread hiện tại theo tick
        self.lastTickPrice = None   #Last tick price
        self.lastTickVolume = None  #Last tick volume

        self.trade_size = 1  # Number of contracts to trade
        self.stop_loss = 1000  # Stop loss in points
        self.take_profit = 1000  # Take profit in points
        self.order_id = None  # Current order ID

        self.debug = True  # Enable debug mode for detailed logging

        # Setup logger
        self.logger = setup_logger("SMARTBOT", logging.DEBUG)
        self.logger.info(f"Khởi tạo bot: {self.name}")


    def Update(self):
        '''
        Mục đích : Update liên tục vào trong bot các giá tick hiện thời, tick volume hiện thời và spread hiện thời
        phục vụ cho logic của bot và tính profit tức thời
        '''
        
        pass

    def Calculate_UnrealisedNetProfit(self):
        '''
        Mục đích: tính toán net profit tạm thời, và trả vào trong bot
        '''
        contractFactor = 100000.0  # Hệ số hợp đồng 100,000 VNĐ/hđ
        tickprice = GLOBAL.TICK_PRICE
        try:
            netprofit = self.UnrealisedNetProfit = round((tickprice-self.order_entryprice)*self.orderQuantity*contractFactor if self.position=='BUY' else (self.order_entryprice - tickprice)*self.orderQuantity*contractFactor if self.position=='SELL' else 0,0)
            self.unrealisedNetProfit = netprofit
            return netprofit
        except:
            self.unrealisedNetProfit = 0
            return 0

    def print_dealBot(self):
        try:
            if not self.order_id:
                print(f"Bot {self.name} has no active deals.")
                
            contractFactor = 100000.0  # Hệ số hợp đồng 100,000 VNĐ/hđ
            tickprice = GLOBAL.TICK_PRICE
            tickVol = GLOBAL.TICK_VOLUME
            print(80*"=")
            print(f"Deal info from bot {self.name}:")
            print(f"Order id: {self.order_id}")
            print(f"Entry price: {round(self.order_entryprice,1) if self.order_entryprice is not None else "N/A"}")
            print(f"Position: {self.position if self.position is not None else "N/A"}")
            print(f"Open Quantity: {self.orderQuantity if self.orderQuantity is not None else "N/A"}")
            print(f"Order Side: {self.order_side if self.order_side is not None else "N/A"}")
            print(f"Current Price: {round(tickprice,1) if tickprice is not None else "N/A"}")
            print(f"Latest matched volume: {tickVol if tickVol is not None else "N/A"}")
            print(f"Estimated P/L: {round((tickprice-self.order_entryprice)*self.orderQuantity*contractFactor if self.position=='BUY' else (self.order_entryprice - tickprice)*self.orderQuantity*contractFactor if self.position=='SELL' else 0,0):,.0f} VND")
            print(80*"=")
        except:
            pass
    
    def getBarSeries(self, timeframe: str = None, pricetype: str = "C"):
        '''
        Lấy dữ liệu nến từ marketData đã được truyền vào df
        df là dạng pandas.Series
        '''
        
        #valid marketData first
        if self.marketData is None:
            self.log("Market data is not set.")
            return None
        if timeframe in ["m1", "m3", "m5", "m15", "m30", "H1", "D1", "W1"]:
            data = self.marketData[timeframe]
            df = pd.DataFrame(data, columns=['ts', 'O', 'H', 'L', 'C', 'V'])

            if pricetype in ['O', 'H', 'L', 'C', 'V']:
                return df[pricetype.upper()]
            else:
                self.log(f"Invalid price type: {pricetype}. Must be one of ['O', 'H', 'L', 'C', 'V'].")
                return None
    
    def is_trading_time(self) -> bool:
        """Check if current Vietnam time is within trading hours"""
        return is_trading_time_vietnam(self.starttradingtime, self.endtradingtime)

    def cross(self,data1: list | float | int, data2: list | float | int) -> bool | None:
        """
        Kiểm tra xem data1 có cắt lên đường data2 hay không.
        Điều kiện: data1 trước < data2 trước và data1 hiện tại > data2 hiện tại

        Trả về:
            - True nếu có cắt lên
            - False nếu không cắt
            - None nếu không đủ dữ liệu
        """
        # Nếu là số, chuyển thành list với 2 phần tử giống nhau
        if isinstance(data1, (int, float)):
            data1 = [data1, data1]
        if isinstance(data2, (int, float)):
            data2 = [data2, data2]

        if data1 is None or data2 is None:
            return None

        if len(data1) < 2 or len(data2) < 2:
            return None  # Không đủ dữ liệu để kiểm tra

        # Lấy 2 giá trị gần nhất
        prev1, curr1 = data1[-2], data1[-1]
        prev2, curr2 = data2[-2], data2[-1]

        # Kiểm tra điều kiện cắt lên
        if prev1 < prev2 and curr1 > curr2:
            return True
        else:
            return False
        
