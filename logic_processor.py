# from global_var import ENTRADE_CLIENT , LAST_BID_DEPTH, LAST_OFFER_DEPTH
from datetime import datetime
from agents.macd_agent import macd_agent
from agents.rsi_ta import rsi_agent_ta
from agent import Agent
import GLOBAL
from Indicators import MomentumIndicators, TrendIndicators

ACTIVE_BOT: list[Agent] = [
    macd_agent, rsi_agent_ta,
]

def OnTick(data: tuple):
    print("Dư mua:", GLOBAL.TOTAL_BID)
    print("Dư bán:", GLOBAL.TOTAL_OFFER)
    print("Tổng KLGD mua nước ngoài:", GLOBAL.TOTAL_FOREIGN_BUY)
    print("Tổng KLGD bán nước ngoài:", GLOBAL.TOTAL_FOREIGN_SELL)

    try:
        if GLOBAL.BID_DEPTH:
            last_bid_price = GLOBAL.BID_DEPTH[0][0]  # Get the price from the last tuple
            print(f"Last bid price: {last_bid_price}")
        else:
            print("No bid data available.")

        if GLOBAL.OFFER_DEPTH:
            last_ask_price = GLOBAL.OFFER_DEPTH[0][0]  # Get the price from the last tuple
            print(f"Last ask price: {last_ask_price}")
        else:
            print("No ask data available.")

        if last_bid_price > 0 and last_ask_price > 0:
            spread =  round(last_ask_price -last_bid_price,2)
            print(f"Spread: {spread}")


        # lấy thông tin deal đang active:
        activeDeals = GLOBAL.ENTRADE_CLIENT.GetActiveDeals()
        print(f"Numer of active deals : {len(activeDeals)}")
        # print(activeDeals[0])

        # Đặt lệnh Long
        if len(activeDeals) == 0:
            GLOBAL.ENTRADE_CLIENT.Order(GLOBAL.get_vn30f1m_krx(), "NB", None, None, 1, "MTL", True)

        #close lệnh khi có lời 1 point
        for deal in activeDeals:
            if GLOBAL.BID_DEPTH:
                last_ask_price = GLOBAL.BID_DEPTH[0][0]  # Get the price from the last tuple
                if last_ask_price >= deal["breakEvenPrice"] + 1:
                    GLOBAL.ENTRADE_CLIENT.CloseDeal(deal["id"])



    except:
        pass


    # print(GLOBAL.BID_DEPTH)
    # print(data)
    # print(np.array(data).shape)

    print(GLOBAL.get_vn30f1m_krx())



    pass

def OnBarClosed(data: list[tuple]):
    close_price = data[-1][3]
    # print("Độ sâu mua:", GLOBAL.BID_DEPTH[0]) // Market depth data
    # print("Độ sâu bán:", GLOBAL.OFFER_DEPTH[0])

    # tính indicator
    # print(data)
    # print(np.array(data).shape)

    periodRSI = 14
    rsi = MomentumIndicators.rsi(data, periodRSI)
    # print(f" RSI = {rsi}")
    print(20*"=")
    print(f" RSI = {(rsi[-1]):.1f}")
    print(20 * "=")


    for agent in ACTIVE_BOT:
        result = agent.Calculate(data)

        if result == True: # MUST CHECK FOR BOOL, SINCE AGENT MAY RETURN NONE TOO!
            #close all deal first
            #kiểm tra deal đang mở là Long thì ko cần đóng lệnh, nếu là deal đang mở là Short thì sẽ đóng lệnh trước.
            Deals = GLOBAL.ENTRADE_CLIENT.GetDeals(0,255,True)["data"]
            for deal in Deals:
                if deal["side"]=="NS":
                    GLOBAL.ENTRADE_CLIENT.CloseDeal(deal["id"], is_demo=True)


            #Đặt lệnh Long
            GLOBAL.ENTRADE_CLIENT.Order(GLOBAL.get_vn30f1m_krx(), "NB", None, None, 1, "MTL", True)
            print(f"{agent.name} đã đặt lệnh LONG tại giá {close_price:.1f} ({datetime.now().strftime("%H:%M %d/%m")})")

        elif result == False:
            # close all deal first
            # kiểm tra deal đang mở là Short thì ko cần đóng lệnh, nếu là deal đang mở là Long thì sẽ đóng lệnh trước.
            Deals = GLOBAL.ENTRADE_CLIENT.GetDeals(0, 255, True)["data"]
            for deal in Deals:
                if deal["side"] == "NB":
                    GLOBAL.ENTRADE_CLIENT.CloseDeal(deal["id"], is_demo=True)

            #đặt lệnh Short
            GLOBAL.ENTRADE_CLIENT.Order(GLOBAL.get_vn30f1m_krx(), "NS", None, None, 1, "MTL", True)
            print(f"{agent.name} đã đặt lệnh SHORT tại giá {(close_price):.1f} ({datetime.now().strftime("%H:%M %d/%m")})")


        try:
            deals = GLOBAL.ENTRADE_CLIENT.GetDeals(start=0,end=255,is_demo=True)["data"]
            for deal in deals:
                #giá khớp lệnh
                if deal["status"] == "ACTIVE":
                    print(f"Deal ID: {deal["id"]} - Side: {deal["side"]} - BreakEvenPrice: {round(deal["breakEvenPrice"],1)}")
        except:
            print("Failed to get deal data")




# def CalculateStrategy(processed_data):
#     close_price = processed_data[-1][3]
#     # print(LAST_BID_DEPTH) // Market depth data
#     # print(LAST_OFFER_DEPTH)
#     print("Close Price: ", close_price)
#
#     if LAST_BID_DEPTH:
#         last_bid_price = LAST_BID_DEPTH[0][0]  # Get the price from the last tuple
#         print(f"Last bid price: {last_bid_price}")
#     else:
#         print("No bid data available.")
#
#     if LAST_OFFER_DEPTH:
#         last_ask_price = LAST_OFFER_DEPTH[0][0]  # Get the price from the last tuple
#         print(f"Last ask price: {last_ask_price}")
#     else:
#         print("No ask data available.")
#
#     if last_bid_price > 0 and last_ask_price > 0:
#         spread =  round(last_ask_price -last_bid_price,2)
#         print(f"Spread: {spread}")
#
#
#
#     for agent in ACTIVE_BOT:
#         result = agent.Calculate(processed_data)
#
#
#
#         if result == True: # MUST CHECK FOR BOOL, SINCE AGENT MAY RETURN NONE TOO!
#             #close all deal first
#             #kiểm tra deal đang mở là Long thì ko cần đóng lệnh, nếu là deal đang mở là Short thì sẽ đóng lệnh trước.
#             Deals = ENTRADE_CLIENT.GetDeals(0,255,True)["data"]
#             for deal in Deals:
#                 if deal["side"]=="NS":
#                     ENTRADE_CLIENT.CloseDeal(deal["id"], is_demo=True)
#
#
#             #Đặt lệnh Long
#             ENTRADE_CLIENT.Order("VN30F2509", "NB", None, None, 1, "MTL", True)
#             print(f"{agent.name} đã đặt lệnh LONG tại giá {close_price:.1f} ({datetime.now().strftime("%H:%M %d/%m")})")
#
#         elif result == False:
#             # close all deal first
#             # kiểm tra deal đang mở là Short thì ko cần đóng lệnh, nếu là deal đang mở là Long thì sẽ đóng lệnh trước.
#             Deals = ENTRADE_CLIENT.GetDeals(0, 255, True)["data"]
#             for deal in Deals:
#                 if deal["side"] == "NB":
#                     ENTRADE_CLIENT.CloseDeal(deal["id"], is_demo=True)
#
#             #đặt lệnh Short
#             ENTRADE_CLIENT.Order("VN30F2509", "NS", None, None, 1, "MTL", True)
#             print(f"{agent.name} đã đặt lệnh SHORT tại giá {(close_price):.1f} ({datetime.now().strftime("%H:%M %d/%m")})")
#
#
#         try:
#             deals = ENTRADE_CLIENT.GetDeals(start=0,end=255,is_demo=True)["data"]
#             for deal in deals:
#                 #giá khớp lệnh
#                 if deal["status"] == "ACTIVE":
#                     print(f"Deal ID: {deal["id"]} - Side: {deal["side"]} - BreakEvenPrice: {round(deal["breakEvenPrice"],1)}")
#         except:
#             print("Failed to get deal data")





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