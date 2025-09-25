import GLOBAL
import datetime
from datetime import datetime, time
import os
# import time
# from time import time
import pandas as pd
from timezone_utils import is_trading_time_vietnam



class pBot:
    def __init__(self, name: str = "BotName", 
                 description: str = "This is a sample bot that uses MACD indicator to trade.", 
                 version: str = "1.0", 
                 author: str = "Your Name",
                 timeframe: str = "m5",
                 symbol: str = "VN30F1M"):
        self.name = name
        self.description = description
        self.version = version
        self.author = author
        self.is_active = True
        self.timeframe = timeframe  # Timeframe to use for this bot
        self.symbol = "VN30F1M"  # Symbol to trade
        self.position = None  # Current position: "BUY", "SELL", or None
        self.last_action_time = 0  # Last time an action was taken
        self.action_interval = 0  # Minimum interval between actions in seconds

        # Trading hours in Vietnam timezone
        self.starttradingtime = time(9,1)  # Start trading time, time object (tương đương 9:01 AM) defaut
        self.endtradingtime = time(14,29)    # End trading time, time object (tương đương 2:29 PM) defaut
        self.maxOpenTrades = 1  # Maximum number of open trades allowed

        self.marketData = None # Market data passed from pBot
        self.order_id = None  # Current order ID
        self.order_entryprice = None  # Entry price of the current order
        self.order_side = None  # Side of the current order: "NB" or "NS"
        self.orderPriceType = "MTL"  # Order price type: MTL, LO
        self.orderPrice = None  # Order price, None for market orders
        self.orderQuantity = None  # Order quantity
        self.trade_size = 1  # Number of contracts to trade
        self.stop_loss = 1000  # Stop loss in points
        self.take_profit = 1000  # Take profit in points
        self.order_id = None  # Current order ID
        self.debug = True  # Enable debug mode for detailed logging
        self.log_file = f"{self.name}_log.txt"
        self.init_log()
        self.log(f"Bot {self.name} initialized.")
        self.log(f"Bot {self.name} started.")
    
    def init_log(self):

        with open(self.log_file, 'w') as f:
            f.write(f"Log for {self.name}\n")
            f.write("="*50 + "\n")
    def log(self, message):
        if self.debug:
            # print(message)
            pass
        with open(self.log_file, 'a') as f:
            f.write(f"{datetime.now().strftime("%H:%M:%S %d/%m")} - {message}\n")
    
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
            print(f"Entry price: {round(self.order_entryprice,1)} ")
            print(f"Position: {self.position} ")
            print(f"Open Quantity: {self.orderQuantity}")
            print(f"Order Side: {self.order_side}")
            print(f"Current Price: {round(tickprice,1)}")
            print(f"Latest matched volume: {tickVol}")
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
        
