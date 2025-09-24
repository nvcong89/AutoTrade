import GLOBAL
import datetime
from datetime import datetime
import os
import time
from time import time
import pandas as pd


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
            print(f"Entry price: {self.order_entryprice} ")
            print(f"Position: {self.position} ")
            print(f"Open Quantity: {self.orderQuantity}")
            print(f"Order Side: {self.order_side}")
            print(f"Current Price: {round(tickprice,1)}")
            print(f"Latest matched volume: {tickVol}")
            print(f"Estimated P/L: {round((tickprice-self.order_entryprice)*self.orderQuantity*contractFactor if self.position=='BUY' else (self.order_entryprice - tickprice)*self.orderQuantity*contractFactor if self.position=='SELL' else 0,0)}")
            print(80*"=")
        except:
            pass
