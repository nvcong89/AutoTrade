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

#Khai báo các biến toàn cục cho Indicators

global resitancePrice
global supportPrice

resitancePrice = 1825
supportPrice = 1820

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

def OnTick(data):
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

    # print(GLOBAL.BID_DEPTH)
    # print(data)
    # print(np.array(data).shape)

    #print out thông tin sau mỗi tick

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


def OnBarClosed(HISTORY: {}):
    global n
    data = HISTORY['m1']
    close_price = HISTORY['m1'][4]
    
    #test khoảng thời gian thực thi sau đóng nến workingTimeFrame (xem trong GLOBAL.py)
    n = n + 1
    print(f"gọi lần {n} : [{datetime.now().strftime("%H:%M:%S %d/%m")}]")
    
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




    if CloseBuyCondition():
    # kiểm tra deal đang mở là Long thì ko cần đóng lệnh, nếu là deal đang mở là Short thì sẽ đóng lệnh trước.
        Deals = GLOBAL.ENTRADE_CLIENT.GetActiveDeals()
        for deal in Deals:
            if deal["side"]=="NB":
                GLOBAL.ENTRADE_CLIENT.CloseDeal(deal["id"], is_demo=True)


    if CloseShortCondition():
    # kiểm tra deal đang mở là Short thì ko cần đóng lệnh, nếu là deal đang mở là Short thì sẽ đóng lệnh trước.
        Deals = GLOBAL.ENTRADE_CLIENT.GetActiveDeals()
        for deal in Deals:
            if deal["side"]=="NS":
                GLOBAL.ENTRADE_CLIENT.CloseDeal(deal["id"], is_demo=True)

    if BuyCondition():
        GLOBAL.ENTRADE_CLIENT.Order("41I1FA000", "NB", None, None, 1, "MTL", True)
        # print(f"{agent.name} đã đặt lệnh LONG tại giá {close_price:.1f} ({datetime.now().strftime("%H:%M %d/%m")})")

    if ShortCondition():
        GLOBAL.ENTRADE_CLIENT.Order("41I1FA000", "NS", None, None, 1, "MTL", True)



def BuyCondition():
    # Ví dụ tính ema cross
    result = False  # return a bool, True or False
    return result


def CloseBuyCondition():
    # Ví dụ tính ema cross
    result = False  # return a bool, True or False
    return result


def ShortCondition():
    # Ví dụ tính ema cross
    result = False  # return a bool, True or False
    return result


def CloseShortCondition():
    # Ví dụ tính ema cross
    result = False  # return a bool, True or False
    return result