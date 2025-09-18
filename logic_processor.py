from agents.rsi_agent import rsi_agent
from global_var import ENTRADE_CLIENT #, LAST_BID_DEPTH, LAST_OFFER_DEPTH
from datetime import datetime
from agents.ma_cross_agent import ma_cross_agent
from agents.BB_agent import bb_agent
from agents.macd_agent import macd_agent
from agents.rsi_ta import rsi_agent_ta
from agent import Agent


ACTIVE_BOT: list[Agent] = [
    macd_agent, rsi_agent_ta,
]

def CalculateStrategy(processed_data):
    close_price = processed_data[-1][3]
    # print(LAST_BID_DEPTH) // Market depth data
    # print(LAST_OFFER_DEPTH)
    print("Close Price: ", close_price)


    for agent in ACTIVE_BOT:
        result = agent.Calculate(processed_data)



        if result == True: # MUST CHECK FOR BOOL, SINCE AGENT MAY RETURN NONE TOO!
            #close all deal first
            #kiểm tra deal đang mở là Long thì ko cần đóng lệnh, nếu là deal đang mở là Short thì sẽ đóng lệnh trước.
            Deals = ENTRADE_CLIENT.GetDeals(0,255,True)["data"]
            for deal in Deals:
                if deal["side"]=="NS":
                    ENTRADE_CLIENT.CloseDeal(deal["id"], is_demo=True)


            #Đặt lệnh Long
            ENTRADE_CLIENT.Order("VN30F2509", "NB", None, None, 1, "MTL", True)
            print(f"{agent.name} đã đặt lệnh LONG tại giá {close_price:.1f} ({datetime.now().strftime("%H:%M %d/%m")})")

        elif result == False:
            # close all deal first
            # kiểm tra deal đang mở là Short thì ko cần đóng lệnh, nếu là deal đang mở là Long thì sẽ đóng lệnh trước.
            Deals = ENTRADE_CLIENT.GetDeals(0, 255, True)["data"]
            for deal in Deals:
                if deal["side"] == "NB":
                    ENTRADE_CLIENT.CloseDeal(deal["id"], is_demo=True)

            #đặt lệnh Short
            ENTRADE_CLIENT.Order("VN30F2509", "NS", None, None, 1, "MTL", True)
            print(f"{agent.name} đã đặt lệnh SHORT tại giá {(close_price):.1f} ({datetime.now().strftime("%H:%M %d/%m")})")


        try:
            deals = ENTRADE_CLIENT.GetDeals(start=0,end=255,is_demo=True)["data"]
            for deal in deals:
                #giá khớp lệnh
                print("dea ID: " + deal["id"] + "[" + deal["side"] + "]" + " Giá hòa vốn: " + deal["breakEvenPrice"])
        except:
            print("Failed to get deal data")



