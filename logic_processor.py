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
from logger_config import setup_logger
import logging
from pyBot001 import pyBotMACD



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



def OnStart():

    global bot  #khai báo biến global khởi tạo bot.
    global logger #khai báo logger

    logger = setup_logger("[Logic_Processor]", logging.INFO)


    # Truy cập dữ liệu các TF
    # cprint(f"1 phút gần nhất: {GLOBAL.MARKETDATA['m1'][-5:]}")
    # cprint(f"5 phút gần nhất: {GLOBAL.MARKETDATA['m5'][-5:]}")
    # cprint(f"15 phút gần nhất: {GLOBAL.MARKETDATA['m15'][-5:]}")

    # Visualize data
    # cprint(f"Bảng data nến M1")
    # logger.info(f"Bảng data nến M1")
    # print(tabulate(
    #     GLOBAL.MARKETDATA['m1'][-5:],
    #     headers=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'],
    #     tablefmt='fancy_grid'
    # ))
    
    # logger.info(f"Bảng data nến M3")
    # print(tabulate(
    #     GLOBAL.MARKETDATA['m3'][-5:],
    #     headers=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'],
    #     tablefmt='fancy_grid'
    # ))
    
    # logger.info(f"Bảng data nến M5")
    # print(tabulate(
    #     GLOBAL.MARKETDATA['m5'][-5:],
    #     headers=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'],
    #     tablefmt='fancy_grid'
    # ))

    # cprint(f"Thông tin tài khoản [Endtrade]: \n {GLOBAL.ENTRADE_CLIENT.GetAccountInfo()}")
    # cprint(f"Thông tin tài khoản [DNSE]: \n {GLOBAL.DNSE_CLIENT.GetAccountInfo()}")

    #===========================================================
    #===========================================================
    #khởi tạo bot
    bot = pyBotMACD(name="MACD_Bot",description="",
               version="1.0",
               author="Nguyen van Cong",
               timeframe="m5",
               symbol="VN30F1M")
    
    # set thông số ban đầu cho bot trước khi chạy
    bot.symbol = GLOBAL.VN30F1M
    bot.tradingPlatform = "DNSE"     # chọn "DNSE" hoặc "ENTRADE" để đẩy lệnh lên sau này.
    
    bot.dnseClient = GLOBAL.DNSE_CLIENT
    bot.entradeClient = GLOBAL.ENTRADE_CLIENT

    loadpackageidDNSE = 1306
    bot.loanpackageid = loadpackageidDNSE   #gói vay để giao dịch ở DNSE
    bot.accountNo = GLOBAL.DNSE_CLIENT.investor_account_id
    bot.is_active = True     #cho bot chạy kiểm tra logic
    bot.trade_size = 1      #số lượng hợp đồng mỗi lệnh
    bot.maxOpenTrades = 1   # số lượng hợp đồng tối đa có thể mở.
    bot.stop_loss = 1000    # stop loss point
    bot.take_profit = 1000  #take profit point

    cprint(80*"=")
    cprint(f"Bot {bot.name} đã được khởi tạo.")

    #lấy data theo timeframe của bot
    cprint(f"Đẩy MarketData vào trong bot...")
    bot.marketData=GLOBAL.MARKETDATA   #đẩy marketdata vào bot
    cprint(f"Bot đang chạy...")
    bot.run()


    pass

def OnTick():
    global bot

    # cprint(GLOBAL.MARKETDATA)
    bot.marketData=GLOBAL.MARKETDATA   #đẩy marketdata mới vào bot
    bot.print_dealBot()
    bot.run()


    # cprint("Dư mua:", GLOBAL.TOTAL_BID)
    # cprint("Dư bán:", GLOBAL.TOTAL_OFFER)
    # cprint("Tổng KLGD mua nước ngoài:", GLOBAL.TOTAL_FOREIGN_BUY)
    # cprint("Tổng KLGD bán nước ngoài:", GLOBAL.TOTAL_FOREIGN_SELL)

    

    return

    try:
        if GLOBAL.BID_DEPTH:
            LastBidPrice = GLOBAL.BID_DEPTH[0][0]  # Get the price from the last tuple
            # cprint(f"Last bid price: {LastBidPrice}")
        else:
            cprint("No bid data available.")

        if GLOBAL.OFFER_DEPTH:
            LastAskPrice = GLOBAL.OFFER_DEPTH[0][0]  # Get the price from the last tuple
            # cprint(f"Last ask price: {LastAskPrice}")
        else:
            cprint("No ask data available.")

        if LastBidPrice > 0 and LastAskPrice > 0:
            Spread =  round(LastAskPrice -LastBidPrice,2)
            # cprint(f"Spread: {Spread}")

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
    cprint(f"ACTIVE DEALS : {len(activedeals)}")
    for deal in activedeals:
        cprint(f"Deal ID: {deal['id']}, Side: {deal['side']}, Open Price: {deal['breakEvenPrice']}, Quantity: {deal['openQuantity']}")
        
        try:
            if deal['breakEvenPrice'] + 1.0 <= LastBidPrice and deal["side"]=="NB" and Spread <= 0.2:
                GLOBAL.ENTRADE_CLIENT.CloseDeal(deal["id"], is_demo=True)
                cprint(f"Đóng lệnh {deal['id']} chốt lời 1 point")

            if deal['breakEvenPrice'] - 1.0 >= LastAskPrice and deal["side"]=="NS" and Spread <= 0.2:
                GLOBAL.ENTRADE_CLIENT.CloseDeal(deal["id"], is_demo=True)
                cprint(f"Đóng lệnh {deal['id']} chốt lời 1 point")
        except:
            pass



    # #cprint out thông tin sau mỗi tick

    cprint(50*"-")
    cprint(f"TIME: {datetime.now().strftime("%H:%M:%S %d/%m")}")
    cprint(f"Mã phái sinh: {GLOBAL.VN30F1M}")
    cprint(f"Last Bid Price: {LastBidPrice if GLOBAL.BID_DEPTH else 0}")
    cprint(f"Last Bid Vol: {GLOBAL.BID_DEPTH[0][1] if GLOBAL.BID_DEPTH else 0}")
    cprint(f"Last Ask Price: {LastAskPrice if GLOBAL.OFFER_DEPTH else 0}")
    cprint(f"Last Ask Vol: {GLOBAL.OFFER_DEPTH[0][1] if GLOBAL.OFFER_DEPTH else 0}")
    cprint(f"Spread: {Spread if GLOBAL.BID_DEPTH and GLOBAL.OFFER_DEPTH else 0}")
    cprint(f"Tổng KLGD nước ngoài-MUA: {GLOBAL.TOTAL_FOREIGN_BUY}")
    cprint(f"Tổng KLGD nước ngoài-BÁN: {GLOBAL.TOTAL_FOREIGN_SELL}")
    cprint(f"Chênh NN MUA-BÁN : {GLOBAL.TOTAL_FOREIGN_BUY-GLOBAL.TOTAL_FOREIGN_SELL}")
    cprint(f"Dư mua: {GLOBAL.TOTAL_FOREIGN_BUY}")
    cprint(f"Dư bán: {GLOBAL.TOTAL_FOREIGN_SELL}")
    cprint(f"Chênh Dư MUA-BÁN: {GLOBAL.TOTAL_FOREIGN_BUY-GLOBAL.TOTAL_FOREIGN_SELL}")
    cprint(50 * "-")


    pass

def OnBarClosed():
    global bot

    bot.marketData=GLOBAL.MARKETDATA   #đẩy mảketdata vào bot
    bot.run()

    return



    #test khoảng thời gian thực thi sau đóng nến workingTimeFrame (xem trong GLOBAL.py)
    # n = n + 1
    # cprint(f"gọi lần {n} : [{datetime.now().strftime("%H:%M:%S %d/%m")}]")
    
    # data = GLOBAL.ENTRADE_CLIENT.GetBars(GLOBAL.VN30F1M,"5",1)

    # cprint(f"data : {len(data)} candles")
    # cprint(f" getBars: {data}")
    # cprint("5 phút gần nhất:", data[-5:])
    # cprint(tabulate(
    #     data[-5:],
    #     headers=['Open', 'High', 'Low', 'Close', 'Volume'],
    #     tablefmt='fancy_grid'
    # ))


    # Visualize data - for testing data processing
    # cprint(tabulate(
    #     HISTORY['m1'][-5:],
    #     headers=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'],
    #     tablefmt='fancy_grid'
    # ))

    # cprint(tabulate(
    #     HISTORY['m3'][-5:],
    #     headers=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'],
    #     tablefmt='fancy_grid'
    # ))

    # cprint(tabulate(
    #     HISTORY['m5'][-5:],
    #     headers=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'],
    #     tablefmt='fancy_grid'
    # ))




