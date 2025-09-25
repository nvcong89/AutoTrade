from datetime import datetime
import json

import pandas as pd
from agents.macd_agent import macd_agent
from agents.rsi_ta import rsi_agent_ta
from agent import Agent
from Indicators import MomentumIndicators, TrendIndicators
import GLOBAL
from tabulate import tabulate
import numpy as np
from Utils import*
from pBot001 import pBotMACD


LastBidPrice = 0
LastAskPrice = 0
Spread = None
activedeals = []
trend = 0  #1=up, 0=sideway, -1=down
pendingDeals=[]

n: int = 0

#Khai báo các biến toàn cục cho Indicators

global resitancePrice
global supportPrice

resitancePrice = 1825
supportPrice = 1820

marketData={}



def OnStart():

    global marketData, bot  #khai báo biến global khởi tạo bot.

    

    # Truy cập dữ liệu các TF
    # print("1 phút gần nhất:", HISTORY['m1'][-5:])
    # print("5 phút gần nhất:", HISTORY['m5'][-5:])
    # print("15 phút gần nhất:", HISTORY['m15'][-5:])

    # Visualize data
    # print(tabulate(
    #     HISTORY['m1'][-5:],
    #     headers=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'],
    #     tablefmt='fancy_grid'
    # ))
    
    # print(tabulate(
    #     HISTORY['m3'][-5:],
    #     headers=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'],
    #     tablefmt='fancy_grid'
    # ))
    
    # print(tabulate(
    #     HISTORY['m5'][-5:],
    #     headers=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'],
    #     tablefmt='fancy_grid'
    # ))

    # print(f"Thông tin tài khoản [Endtrade]: \n {GLOBAL.ENTRADE_CLIENT.GetAccountInfo()}")
    # print(f"Thông tin tài khoản [DNSE]: \n {GLOBAL.DNSE_CLIENT.GetAccountInfo()}")

    #===========================================================
    #===========================================================
    #khởi tạo bot
    bot = pBotMACD(name="MACD_Bot",description="",
               version="1.0",
               author="Nguyen van Cong",
               timeframe="m5",
               symbol="VN30F1M")
    
    # set thông số ban đầu cho bot trước khi chạy
    bot.symbol = GLOBAL.VN30F1M
    bot.traingPlatform = "DNSE"     # chọn "DNSE" hoặc "ENTRADE" để đẩy lệnh lên sau này.
    bot.is_active =True     #cho bot chạy kiểm tra logic
    bot.trade_size = 1      #số lượng hợp đồng mỗi lệnh
    bot.maxOpenTrades = 5   # số lượng hợp đồng tối đa có thể mở.
    bot.stop_loss = 1000    # stop loss point
    bot.take_profit = 1000  #take profit point

    print(80*"=")
    print(f"Bot {bot.name} đã được khởi tạo.")

    #lấy data theo timeframe của bot
    bot.marketData=GLOBAL.MARKETDATA   #đẩy marketdata vào bot

    print(f"Bot đang chạy...")
    bot.run()
    pass

def OnTick():
    global bot

    # print(GLOBAL.MARKETDATA)
    bot.marketData=GLOBAL.MARKETDATA   #đẩy marketdata mới vào bot
    bot.print_dealBot()
    bot.run()

    # print("Dư mua:", TOTAL_BID)
    # print("Dư bán:", TOTAL_OFFER)
    # print("Tổng KLGD mua nước ngoài:", TOTAL_FOREIGN_BUY)
    # print("Tổng KLGD bán nước ngoài:", TOTAL_FOREIGN_SELL)

    

    return

    try:
        if GLOBAL.BID_DEPTH:
            LastBidPrice = GLOBAL.BID_DEPTH[0][0]  # Get the price from the last tuple
            # print(f"Last bid price: {LastBidPrice}")
        else:
            print("No bid data available.")

        if GLOBAL.OFFER_DEPTH:
            LastAskPrice = GLOBAL.OFFER_DEPTH[0][0]  # Get the price from the last tuple
            # print(f"Last ask price: {LastAskPrice}")
        else:
            print("No ask data available.")

        if LastBidPrice > 0 and LastAskPrice > 0:
            Spread =  round(LastAskPrice -LastBidPrice,2)
            # print(f"Spread: {Spread}")

        # Mở và đóng lệnh scalp 1 point
        if Spread == 0.1 and LastBidPrice < supportPrice and len(GLOBAL.ENTRADE_CLIENT.GetActiveDeals())==0:
            # mở lệnh Long
            resultNB = GLOBAL.ENTRADE_CLIENT.Order(GLOBAL.VN30F1M, "NB", None, None, 1, "MTL", True)

        elif Spread == 0.1 and LastAskPrice > resitancePrice and len(GLOBAL.ENTRADE_CLIENT.GetActiveDeals())==0:
            resultNS = GLOBAL.ENTRADE_CLIENT.Order(GLOBAL.VN30F1M, "NS", None, None, 1, "MTL", True)




    except:
        pass

    # lấy thông tin deal đang active:
    activedeals = GLOBAL.ENTRADE_CLIENT.GetActiveDeals()
    print(f"ACTIVE DEALS : {len(activedeals)}")
    for deal in activedeals:
        print(f"Deal ID: {deal['id']}, Side: {deal['side']}, Open Price: {deal['breakEvenPrice']}, Quantity: {deal['openQuantity']}")
        
        try:
            if deal['breakEvenPrice'] + 1.0 <= LastBidPrice and deal["side"]=="NB" and Spread <= 0.2:
                GLOBAL.ENTRADE_CLIENT.CloseDeal(deal["id"], is_demo=True)
                print(f"Đóng lệnh {deal['id']} chốt lời 1 point")

            if deal['breakEvenPrice'] - 1.0 >= LastAskPrice and deal["side"]=="NS" and Spread <= 0.2:
                GLOBAL.ENTRADE_CLIENT.CloseDeal(deal["id"], is_demo=True)
                print(f"Đóng lệnh {deal['id']} chốt lời 1 point")
        except:
            pass



    # #print out thông tin sau mỗi tick

    print(50*"-")
    print(f"TIME: {datetime.now().strftime("%H:%M:%S %d/%m")}")
    print(f"Mã phái sinh: {GLOBAL.VN30F1M}")
    print(f"Last Bid Price: {LastBidPrice if GLOBAL.BID_DEPTH else 0}")
    print(f"Last Bid Vol: {GLOBAL.BID_DEPTH[0][1] if GLOBAL.BID_DEPTH else 0}")
    print(f"Last Ask Price: {LastAskPrice if GLOBAL.OFFER_DEPTH else 0}")
    print(f"Last Ask Vol: {GLOBAL.OFFER_DEPTH[0][1] if GLOBAL.OFFER_DEPTH else 0}")
    print(f"Spread: {Spread if GLOBAL.BID_DEPTH and GLOBAL.OFFER_DEPTH else 0}")
    print(f"Tổng KLGD nước ngoài-MUA: {GLOBAL.TOTAL_FOREIGN_BUY}")
    print(f"Tổng KLGD nước ngoài-BÁN: {GLOBAL.TOTAL_FOREIGN_SELL}")
    print(f"Chênh NN MUA-BÁN : {GLOBAL.TOTAL_FOREIGN_BUY-GLOBAL.TOTAL_FOREIGN_SELL}")
    print(f"Dư mua: {GLOBAL.TOTAL_FOREIGN_BUY}")
    print(f"Dư bán: {GLOBAL.TOTAL_FOREIGN_SELL}")
    print(f"Chênh Dư MUA-BÁN: {GLOBAL.TOTAL_FOREIGN_BUY-GLOBAL.TOTAL_FOREIGN_SELL}")
    print(50 * "-")


    pass


def OnBarClosed():
    global bot

    
    bot.marketData=GLOBAL.MARKETDATA   #đẩy mảketdata vào bot
    bot.run()
    bot.print_dealBot()

    return



    #test khoảng thời gian thực thi sau đóng nến workingTimeFrame (xem trong GLOBAL.py)
    # n = n + 1
    # print(f"gọi lần {n} : [{datetime.now().strftime("%H:%M:%S %d/%m")}]")
    
    # data = GLOBAL.ENTRADE_CLIENT.GetBars(GLOBAL.VN30F1M,"5",1)

    # print(f"data : {len(data)} candles")
    # print(f" getBars: {data}")
    # print("5 phút gần nhất:", data[-5:])
    # print(tabulate(
    #     data[-5:],
    #     headers=['Open', 'High', 'Low', 'Close', 'Volume'],
    #     tablefmt='fancy_grid'
    # ))


    # Visualize data - for testing data processing
    # print(tabulate(
    #     HISTORY['m1'][-5:],
    #     headers=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'],
    #     tablefmt='fancy_grid'
    # ))

    # print(tabulate(
    #     HISTORY['m3'][-5:],
    #     headers=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'],
    #     tablefmt='fancy_grid'
    # ))

    # print(tabulate(
    #     HISTORY['m5'][-5:],
    #     headers=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'],
    #     tablefmt='fancy_grid'
    # ))




