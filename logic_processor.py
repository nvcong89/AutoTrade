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


_createdtimeToken = None #DO NOT REMOVE
_onstart = False    #DO NOT REMOVE



def OnStart(_onstart: bool = False):

    """
    Hàm xử lý, khai báo các biến đầu tiên khi bắt đầu bật bot. Chỉ chạy lần đầu tiên, sau tickdata đầu tiên.
    """
    #=====================================================================
    #DO NOT REMOVE
    #=====================================================================
    if _onstart == True:    #kiểm tra đã chạy chưa, True là đã chạy.
        return


    global bot  #khai báo biến global khởi tạo bot.
    global logger #khai báo logger
    global _createdtimeToken

    if GLOBAL.DNSE_CLIENT:
        _createdtimeToken = GLOBAL.DNSE_CLIENT.createdtimeToken         # datetime isoformat

    logger = setup_logger("[Logic_Processor]", logging.INFO)

    #=====================================================================
    #DO NOT REMOVE
    #=====================================================================


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
    
    # logger.info(f"Bảng data nến M5")
    # print(tabulate(
    #     GLOBAL.MARKETDATA['m5'][-5:],
    #     headers=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'],
    #     tablefmt='fancy_grid'
    # ))
    
    # logger.info(f"Bảng data nến D1")
    # print(tabulate(
    #     GLOBAL.MARKETDATA['D1'][-5:],
    #     headers=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'],
    #     tablefmt='fancy_grid'
    # ))


    #===========================================================
    #BẮT ĐẦU KHAI BÁO THÔNG SỐ VÀ KHỞI TẠO BOT
    #===========================================================
    #khởi tạo bot
    bot = pyBotMACD(name="MACD_Bot",description="",
               version="1.0",
               author="Nguyen van Cong",
               timeframe="m5",
               symbol=GLOBAL.VN30F1M)
    
    # set thông số ban đầu cho bot trước khi chạy
    bot.symbol = GLOBAL.VN30F1M      # mã phái sinh
    # bot.tradingPlatform = "DNSE"     # chọn "DNSE" hoặc "ENTRADE" để đẩy lệnh lên sau này.
    bot.tradingPlatform = "ENTRADE"
    loadpackageidDNSE = 1306
    bot.loanpackageid = loadpackageidDNSE   #gói vay để giao dịch ở DNSE
    bot.investor_account_id = GLOBAL.DNSE_CLIENT.investor_account_id
    bot.is_active = True     #cho bot chạy kiểm tra logic
    bot.orderPriceType ="LO"    #đặt lệnh theo giá LO
    bot.trade_size = 1      #số lượng hợp đồng mỗi lệnh
    bot.maxOpenTrades = 1   # số lượng hợp đồng tối đa có thể mở.
    bot.stop_loss = 1000    # stop loss point
    bot.take_profit = 1000  #take profit point

    logger.info(f"Bot [{bot.name}] đã được khởi tạo.")

    #lấy data theo timeframe của bot
    GLOBAL.WORKING_TIMEFRAME = bot.timeframe
    logger.info(f"Working TimeFrame : {bot.timeframe}")

    
    bot.marketData=GLOBAL.MARKETDATA   #đẩy marketdata vào bot
    logger.info(f"Đẩy MarketData lần đầu tiên vào trong bot...")
    
    bot.run()
    logger.info(f"Bot đang chạy...")

    #in ra giá trần sàn ngày hôm nay
    logger.warning(f"Giá trần hôm nay : {bot.ceilingPrice}")
    logger.warning(f"Giá sàn hôm nay : {bot.floorPrice}")

    bot.dnseClient.CancleAllPendingOrders()
    pass

def OnTick():
    '''
    Xử lý code theo từng tick data.
    '''

    #===================================================================
    #DO NOT REMOVE
    #===================================================================
    global _onstart #biến để khởi chạy OnStart() sau tick data đầu tiên
    if not _onstart:
        OnStart(_onstart)   #gọi OnStart() sau tick đầu tiên, và chỉ gọi 1 lần duy nhất.
        _onstart = True
    #===================================================================
    #Cập nhật các thông tin thị trường vào bot:

    global bot

    if GLOBAL.BID_DEPTH and GLOBAL.ASK_DEPTH:
        bot.marketDepth = {'bid' : GLOBAL.BID_DEPTH,
                           'ask' : GLOBAL.ASK_DEPTH}
        
    #[DO NOT REMOVE] CẬP NHẬT LIÊN TỤC LAST TICK PRICE VÀ LAST TICK VOL VÀO TRONG BOT, ĐỂ LẤY DỮ LIỆU TÍNH TOÁN TRONG BOT
    bot.Update(GLOBAL.LAST_TICK_PRICE,          
               GLOBAL.LAST_TICK_VOLUME,
               GLOBAL.MARKETDATA,
               GLOBAL.TOTAL_BID,
               GLOBAL.TOTAL_OFFER,
               GLOBAL.TOTAL_FOREIGN_BUY,
               GLOBAL.TOTAL_FOREIGN_SELL
               )     


    #===================================================================
    #DO NOT REMOVE
    #===================================================================

    bot.print_dealBot()
    logger.info(f"Spread : {round(bot.spread,1) if bot.spread is not None else "N/A"}")

    pass

def OnBarClosed():
    global bot

    #kiểm tra thời hạn của token, nếu gần hết thì loggin lại để lấy token và trading token
    bot.dnseClient.is_validated_token() #kiểm tra token hiện tại đã hết hạn chưa để get lại.    #DO NOT REMOVE

    bot.marketData=GLOBAL.MARKETDATA   #đẩy mảketdata vào bot
    bot.run()

    return





