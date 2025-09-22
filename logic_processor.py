from datetime import datetime
from agents.macd_agent import macd_agent
from agents.rsi_ta import rsi_agent_ta
from agent import Agent
from Indicators import MomentumIndicators, TrendIndicators
import GLOBAL
from tabulate import tabulate
import numpy as np

ACTIVE_BOT: list[Agent] = [
    macd_agent, rsi_agent_ta,
]


LastBidPrice = 0
LastAskPrice = 0
Spread = None
activedeals = []
trend = 0  #1=up, 0=sideway, -1=down
pendingDeals=[]

n: int = 0

def OnStart(HISTORY: {}):
    # Truy cập dữ liệu các TF
    print("1 phút gần nhất:", HISTORY['m1'][-5:])
    print("5 phút gần nhất:", HISTORY['m5'][-5:])
    print("15 phút gần nhất:", HISTORY['m15'][-5:])

    # Visualize data
    print(tabulate(
        HISTORY['m1'][-5:],
        headers=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'],
        tablefmt='fancy_grid'
    ))
    
    print(tabulate(
        HISTORY['m3'][-5:],
        headers=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'],
        tablefmt='fancy_grid'
    ))
    
    print(tabulate(
        HISTORY['m5'][-5:],
        headers=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'],
        tablefmt='fancy_grid'
    ))

    pass

def OnTick(data: tuple):
    # print("Dư mua:", TOTAL_BID)
    # print("Dư bán:", TOTAL_OFFER)
    # print("Tổng KLGD mua nước ngoài:", TOTAL_FOREIGN_BUY)
    # print("Tổng KLGD bán nước ngoài:", TOTAL_FOREIGN_SELL)

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
        if trend > 0 and Spread == 0.1:
            # mở lệnh Long
            resultNB = GLOBAL.ENTRADE_CLIENT.Order(GLOBAL.VN30F1M, "NB", None, None, 1, "MTL", True)



        elif trend < 0 and Spread == 0.1:
            resultNS = GLOBAL.ENTRADE_CLIENT.Order(GLOBAL.VN30F1M, "NS", None, None, 1, "MTL", True)




    except:
        pass

    # lấy thông tin deal đang active:
    activedeals = GLOBAL.ENTRADE_CLIENT.GetActiveDeals()
    print(f"ACTIVE DEALS : {len(activedeals)}")
    for deal in activedeals:
        print(deal)



    # print(GLOBAL.BID_DEPTH)
    # print(data)
    # print(np.array(data).shape)

    #print out thông tin sau mỗi tick
    print(50*"-")
    print(f"TIME: {datetime.now().strftime("%H:%M:%S %d/%m")}")
    print(f"Mã phái sinh: {GLOBAL.VN30F1M}")
    print(f"Last Bid Price: {LastBidPrice if GLOBAL.BID_DEPTH else 0}")
    print(f"Last Ask Price: {LastAskPrice if GLOBAL.OFFER_DEPTH else 0}")
    print(f"Spread: {Spread if GLOBAL.BID_DEPTH and GLOBAL.OFFER_DEPTH else 0}")
    print(f"Tổng KLGD nước ngoài-MUA: {GLOBAL.TOTAL_FOREIGN_BUY}")
    print(f"Tổng KLGD nước ngoài-BÁN: {GLOBAL.TOTAL_FOREIGN_SELL}")
    print(f"Chênh NN MUA-BÁN : {GLOBAL.TOTAL_FOREIGN_BUY-GLOBAL.TOTAL_FOREIGN_SELL}")
    print(f"Dư mua: {GLOBAL.TOTAL_FOREIGN_BUY}")
    print(f"Dư bán: {GLOBAL.TOTAL_FOREIGN_SELL}")
    print(f"Chênh Dư MUA-BÁN: {GLOBAL.TOTAL_FOREIGN_BUY-GLOBAL.TOTAL_FOREIGN_SELL}")

    print(50 * "-")



    pass

def OnBarClosed(HISTORY: {}):
    global n
    data = HISTORY['m1']
    close_price = HISTORY['m1'][4]
    
    #test khoảng thời gian thực thi sau đóng nến workingTimeFrame (xem trong GLOBAL.py)
    n = n + 1
    print(f"gọi lần {n} : [{datetime.now().strftime("%H:%M:%S %d/%m")}]")
    
    data = GLOBAL.ENTRADE_CLIENT.GetBars(GLOBAL.VN30F1M,"m5",3)
    print(data)
    
    # print("Độ sâu mua:", GLOBAL.BID_DEPTH[0]) // Market depth data
    # print("Độ sâu bán:", GLOBAL.OFFER_DEPTH[0])

    # tính indicator
    # print(data)
    # print(np.array(data).shape)

    # periodRSI = 9
    # rsiShort = MomentumIndicators.rsi(data, periodRSI)
    # periodRSI = 45
    # rsiLong = MomentumIndicators.rsi(data, periodRSI)

    # if rsiShort[-1] > rsiLong[1]:
    #     trend = 1
    # else:
    #     trend = -1


    # # print(f" RSI = {rsi}")
    # print(20*"=")
    # print(f" rsiShort = {(rsiShort[-1]):.1f}")
    # print(f" rsiLong = {(rsiLong[-1]):.1f}")
    # print(20 * "=")


    # for agent in ACTIVE_BOT:
    #     result = agent.Calculate(data)
    #
    #     if result == True: # MUST CHECK FOR BOOL, SINCE AGENT MAY RETURN NONE TOO!
    #         #close all deal first
    #         #kiểm tra deal đang mở là Long thì ko cần đóng lệnh, nếu là deal đang mở là Short thì sẽ đóng lệnh trước.
    #         Deals = GLOBAL.ENTRADE_CLIENT.GetDeals(0,255,True)["data"]
    #         for deal in Deals:
    #             if deal["side"]=="NS":
    #                 GLOBAL.ENTRADE_CLIENT.CloseDeal(deal["id"], is_demo=True)
    #
    #
    #         #Đặt lệnh Long
    #         GLOBAL.ENTRADE_CLIENT.Order(VN30F1M, "NB", None, None, 1, "MTL", True)
    #         print(f"{agent.name} đã đặt lệnh LONG tại giá {close_price:.1f} ({datetime.now().strftime("%H:%M %d/%m")})")
    #
    #     elif result == False:
    #         # close all deal first
    #         # kiểm tra deal đang mở là Short thì ko cần đóng lệnh, nếu là deal đang mở là Long thì sẽ đóng lệnh trước.
    #         Deals = GLOBAL.ENTRADE_CLIENT.GetDeals(0, 255, True)["data"]
    #         for deal in Deals:
    #             if deal["side"] == "NB":
    #                 GLOBAL.ENTRADE_CLIENT.CloseDeal(deal["id"], is_demo=True)
    #
    #         #đặt lệnh Short
    #         GLOBAL.ENTRADE_CLIENT.Order(VN30F1M, "NS", None, None, 1, "MTL", True)
    #         print(f"{agent.name} đã đặt lệnh SHORT tại giá {(close_price):.1f} ({datetime.now().strftime("%H:%M %d/%m")})")
    #
    #
    #     try:
    #         deals = GLOBAL.ENTRADE_CLIENT.GetDeals(start=0,end=255,is_demo=True)["data"]
    #         for deal in deals:
    #             #giá khớp lệnh
    #             if deal["status"] == "ACTIVE":
    #                 print(f"Deal ID: {deal["id"]} - Side: {deal["side"]} - BreakEvenPrice: {round(deal["breakEvenPrice"],1)}")
    #     except:
    #         print("Failed to get deal data")









# def OnStart():
#
#     timeframeM1 = "M5"
#     timeframeM15 = "M15"
#
#     # datasource : có thể là chuỗi data theo các khung timeframe khác nhau
#     datasourceM5 = MarketData.GetBars(timeframeM1)
#     datasourceM15 = MarketData.GetBars(timeframeM15)
#
#     _rsi = Indicators.rsi(datasourceM5, period)
#     _emaA = Indicators.EMA(datasourceM5, periodA)  # return a list
#     _emaB = Indicators.EMA(datasourceM15, periodB)  # return a list
#
#
# def OnTick(data: tuple):
#     print("Dư mua:", GLOBAL.TOTAL_BID)
#     print("Dư bán:", GLOBAL.TOTAL_OFFER)
#     print("Tổng KLGD mua nước ngoài:", GLOBAL.TOTAL_FOREIGN_BUY)
#     print("Tổng KLGD bán nước ngoài:", GLOBAL.TOTAL_FOREIGN_SELL)
#
#     pass
#
# def OnBarClosed():
#     #close_price = data[-1][3]
#     # print("Độ sâu mua:", GLOBAL.BID_DEPTH[0]) // Market depth data
#     # print("Độ sâu bán:", GLOBAL.OFFER_DEPTH[0])
#
#
#     if CloseBuyCondition:
#     # kiểm tra deal đang mở là Long thì ko cần đóng lệnh, nếu là deal đang mở là Short thì sẽ đóng lệnh trước.
#         Deals = ENTRADE_CLIENT.GetDeals(0,255,True)["data"]
#         for deal in Deals:
#             if deal["side"]=="NB":
#                 ENTRADE_CLIENT.CloseDeal(deal["id"], is_demo=True)
#
#
#     if CloseShortCondition:
#     # kiểm tra deal đang mở là Short thì ko cần đóng lệnh, nếu là deal đang mở là Short thì sẽ đóng lệnh trước.
#         Deals = ENTRADE_CLIENT.GetDeals(0,255,True)["data"]
#         for deal in Deals:
#             if deal["side"]=="NS":
#                 ENTRADE_CLIENT.CloseDeal(deal["id"], is_demo=True)
#
#     if BuyCondition:
#         GLOBAL.ENTRADE_CLIENT.Order("41I1FA000", "NB", None, None, 1, "MTL", True)
#
#     if ShortCondition:
#         GLOBAL.ENTRADE_CLIENT.Order("41I1FA000", "NS", None, None, 1, "MTL", True)
#
#
# def BuyCondition:
#     # Ví dụ tính ema cross
#     result = Utils.Cross(_emaA, _emaB)  # return a bool, True or False
#     return result
#
#
# def CloseBuyCondition:
#     # Ví dụ tính ema cross
#     result = Utils.Cross(_emaA, _emaB)  # return a bool, True or False
#     return result
#
#
# def ShortCondition:
#     # Ví dụ tính ema cross
#     result = Utils.Cross(_emaA, _emaB)  # return a bool, True or False
#     return result
#
#
# def CloseShortCondition:
#     # Ví dụ tính ema cross
#     result = Utils.Cross(_emaA, _emaB)  # return a bool, True or False
#     return result