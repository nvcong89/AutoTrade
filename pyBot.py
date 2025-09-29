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
        self.position_side = None  # Current position: "LONG", "SHORT", or None 
        self.last_action_time = 0  # Last time an action was taken
        self.action_interval = 0  # Minimum interval between actions in seconds
        self.symbol = None         #tên mã chứng khoán giao dịch

        #truyền 2 objects Entrade_Client và DNSe_Client vào trong bot
        self.entradeClient = GLOBAL.ENTRADE_CLIENT   # ENTRADEClient instance
        self.dnseClient = GLOBAL.DNSE_CLIENT       # DNSEClient instance

        self.tradingPlatform ="DNSE"     # set trading platform cho bot: "DNSE" hoặc "ENTRADE"
        self.is_demo = True              # set trade voi tk demo

        self.investor_account_id = None   # Mã tiểu khoản dùng để trade bằng bot

        # Trading hours in Vietnam timezone
        self.starttradingtime = time(9,1)  # Start trading time, time object (tương đương 9:01 AM) defaut
        self.endtradingtime = time(14,29)    # End trading time, time object (tương đương 2:29 PM) defaut
        self.maxOpenTrades = 1  # Maximum number of open trades allowed

        self.isTradingTime = False  #có bật chế độ khống chế khoảng thời gian trade ko ?

        self.loanpackageid = None   # load package id

        self.marketData = None # Market data passed from pBot

        self.order_id = None  # Current order ID
        self.order_entryprice = None  # Entry price of the current order, giá mở lệnh, hoặc khớp lệnh
        self.order_side = None  # Side of the current order: "NB" or "NS"
        self.trade_size = 1  # Number of contracts to trade
        self.orderPriceType = "LO"  # Order price type: MTL, LO
        self.orderPrice = None  # Order price, None for market orders
        self.breakevenPrice = None  #giá hòa vốn của deal
        
        self.orderStatus = None     #string, trạng thái lệnh thuộc các giá trị sau: pending, pendingNew, new, partiallyFilled, filled, rejected, expired, doneForDay
        self.orderQuantity = None  # Order quantity, tổng số hợp đồng đang mở

        #Lưu các lệnh đang chờ
        self.pendingOrders = []     #danh sách các lệnh đang chờ

        #object deal đang mở:
        self.dealOpening = None     #trả về deal đang mở.

        self.unrealisedNetProfit = None #lưu giá trị net profit tạm thời

        self.spread = None      #get spread hiện tại theo tick
        self.lastTickPrice = None   #Last tick price
        self.lastTickVolume = None  #Last tick volume
        self.last_bid_price = None  #giá mua bid
        self.last_ask_price = None  #giá bán ask

        self.marketDepth = None # {'bid':[[giá],[khối lượng]], 'ask':[[giá],[khối lượng]]} 10 giá chờ bán + vol, 10 giá chờ mua + vol

        #khối lượng dư mua, bán real time
        self.totalBidQuantity = None #tổng khối lượng dư mua
        self.totalAskQuantity = None #tổng khối lượng dư bán

        #khối lượng mua, bán của nước ngoài
        self.totalBuy_foreign = 0 #tổng khối lượng mua của nước ngoài trong ngày
        self.totalSell_foreign = 0 # tổng khối lượng bán của nước ngoài trong ngày

        #stop loss and take profit
        self.stop_loss = 1000  # Stop loss in points
        self.take_profit = 1000  # Take profit in points
        self.stoplossPrice = None   # Giá đóng lệnh cắt lỗ
        self.takeprofitPrice = None # giá đóng lệnh chốt lời

        #trailing stop
        self.isTrailingStop = False #bật trailing stop hay không
        self.triggerDistance_trailingstop = None    #khoảng cách giá bắt dầu kích hoạt trailing stop
        self.trailingDistance_trailingstop = None   # khoảng cách bắt đầu chạy trailing stop

        #giá trần, sàn
        self.ceilingPrice = None #Giá trần trong ngày giao dịch
        self.floorPrice = None  #Giá sàn trong ngày giao dịch

        #Chế độ DCA
        self.isDCA = False #Bật hoặc tắt chế độ DCA, true, false
        self.dca_distance = None    #float, khoảng cách mở lệnh DCA
        self.dca_volumeType = 1     #int, 1 = khối lượng đi bằng lệnh đầu, 2 = khối lượng tăng thêm 1hđ ở lệnh sau, 3 = gấp thếp hợp đồng ở lệnh sau

        self.firstDeal = None   # format: deal, thông tin của lệnh mở đầu tiên sẽ được lưu lại.
        self.lastDeal = None    # format: deal, thông tin của lệnh mở cuối cùng sẽ được lưu lại

    
        self.debug = True  # Enable debug mode for detailed logging

        self.Initialise()


    def Initialise(self):

        # Setup logger
        self.logger = setup_logger("[SMARTBOT]", logging.DEBUG)
        self.logger.info(f"Khởi tạo bot: {self.name}")

        self.Update(GLOBAL.LAST_TICK_PRICE,GLOBAL.LAST_TICK_VOLUME,None,None)

        #lấy giá trần sàn
        if self.dnseClient:
            self.ceilingPrice = self.dnseClient.GetCeilingAndFloorPrices_VN30F1M()['ceilingprice']
            self.floorPrice = self.dnseClient.GetCeilingAndFloorPrices_VN30F1M()['floorprice'] 
        elif self.entradeClient:
            self.ceilingPrice = self.entradeClient.GetCeilingAndFloorPrices_VN30F1M()['ceilingprice']
            self.floorPrice = self.entradeClient.GetCeilingAndFloorPrices_VN30F1M()['floorprice']
        



    def Update(self, lastTickPrice = None, 
               lastTickVol= None, 
               MARKETDATA= None,
               TOTAL_BID= None,
               TOTAL_OFFER= None,
               TOTAL_FOREIGN_BUY= None,
               TOTAL_FOREIGN_SELL= None 
               ):
        '''
        Mục đích : Update liên tục vào trong bot các giá tick hiện thời, tick volume hiện thời và spread hiện thời
        phục vụ cho logic của bot và tính profit tức thời
        '''

        try:

            #update tickdata vào trong bot
            self.lastTickPrice = lastTickPrice
            self.lastTickVolume = lastTickVol
            
            # cập nhật marketdata
            if MARKETDATA:
                self.marketData = MARKETDATA

            if TOTAL_BID:
                self.totalBidQuantity = TOTAL_BID

            if TOTAL_OFFER:
                self.totalAskQuantity = TOTAL_OFFER
            
            if TOTAL_FOREIGN_BUY:
                self.totalBuy_foreign = TOTAL_FOREIGN_BUY
            
            if TOTAL_FOREIGN_SELL:
                self.totalSell_foreign = TOTAL_FOREIGN_SELL
            
            #update market depth vào trong bot
            if self.marketDepth:
                self.last_bid_price = self.marketDepth['bid'][0][0]
                self.last_ask_price = self.marketDepth['ask'][0][0]
                self.spread = self.last_ask_price - self.last_bid_price
            
        
            #lấy thông tin sổ lệnh vào self.dealOpening
            if self.tradingPlatform.upper() =="DNSE":
                #lấy danh sách lệnh đang chờ
                self.pendingOrders = self.dnseClient.GetPendingOrders(self.investor_account_id)

                #lấy thông tin deal đang mở
                self.dealOpening = self.dnseClient.getActiveDeals(self.investor_account_id)

                if self.dealOpening is not None:
                    self.order_id = self.dealOpening['id']
                    self.order_entryprice = self.dealOpening['breakEvenPrice']
                    self.order_side = self.dealOpening['side']
                    self.orderQuantity = self.dealOpening['fillQuantity']
                    self.orderStatus = self.dealOpening['orderStatus']
                    self.breakevenPrice = self.dealOpening['breakEvenPrice']

                    if self.dealOpening['side']=='NB':
                        self.position_side = "LONG"
                    elif self.dealOpening['side']=='NS':
                        self.position_side = "SHORT"
                    else:
                        self.position_side = None

            else:
                self.dealOpening = self.entradeClient.GetActiveDeals(self.investor_account_id)

                if self.dealOpening is not None:
                    self.order_id = self.dealOpening['id']
                    self.order_entryprice = self.dealOpening['breakEvenPrice']
                    self.order_side = self.dealOpening['side']
                    self.orderQuantity = self.dealOpening['openQuantity']
                    self.orderStatus = self.dealOpening['status']
                    self.breakevenPrice = self.dealOpening['breakEvenPrice']

                    if self.dealOpening['side']=='NB':
                        self.position_side = "LONG"
                    elif self.dealOpening['side']=='NS':
                        self.position_side = "SHORT"
                    else:
                        self.position_side = None


        except Exception as e:
            self.logger.error(f"Đã gặp lỗi Bot.Update() : {e}")
            pass

        

    def Calculate_UnrealisedNetProfit(self):
        '''
        Mục đích: tính toán net profit tạm thời, và trả vào trong bot
        '''
        contractFactor = 100000.0  # Hệ số hợp đồng 100,000 VNĐ/hđ
        tickprice = GLOBAL.LAST_TICK_PRICE
        try:
            netprofit = round((tickprice-self.order_entryprice)*self.orderQuantity*contractFactor if self.position_side=='LONG' else (self.order_entryprice - tickprice)*self.orderQuantity*contractFactor if self.position_side=='SHORT' else 0,0)
            self.unrealisedNetProfit = netprofit
            return netprofit
        except:
            self.unrealisedNetProfit = 0
            return 0

    def print_dealBot(self):
        try:
            if self.dealOpening is None:
                self.logger.warning(f"Bot [{self.name}] has no active deals.")

            contractFactor = 100000.0  # Hệ số hợp đồng 100,000 VNĐ/hđ
            tickprice = GLOBAL.LAST_TICK_PRICE
            tickVol = GLOBAL.LAST_TICK_VOLUME

            totalOpeningDeal = 0
            if self.tradingPlatform.upper() =="DNSE":
                totalOpeningDeal = self.dnseClient.GetTotalOpenQuantity()
            else:
                totalOpeningDeal = self.entradeClient.GetTotalOpenQuantity()

            print(150*"-")
            (f"DEAL INFORMATION [{self.name}]")
            self.cprint(f"Số HĐ đang mở: {totalOpeningDeal}")
            self.cprint(f"Order id: {self.order_id}")
            self.cprint(f"Order Status: {self.orderStatus}")
            self.cprint(f"Break even price: {round(self.breakevenPrice,1) if self.breakevenPrice is not None else "N/A"}")
            self.cprint(f"Position Side: {self.position_side if self.position_side is not None else "N/A"}")
            self.cprint(f"Open Quantity: {self.orderQuantity if self.orderQuantity is not None else "N/A"}")
            self.cprint(f"Order Side: {self.order_side if self.order_side is not None else "N/A"}")
            self.cprint(f"Current Price: {round(tickprice,1) if tickprice is not None else "N/A"}")
            self.cprint(f"Latest matched volume: {tickVol if tickVol is not None else "N/A"}")
            self.cprint(f"Estimated P/L: {self.Calculate_UnrealisedNetProfit():,.0f} VND")
            print(150*"-")
        except Exception as e:
            self.logger.error(f"Đã xảy ra lỗi : {e}")
    
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
    
    def closeAllDeals(self):
        if self.tradingPlatform.upper() == "DNSE":
            self.dnseClient.CloseAllDeals()
            self.logger.warning(f"Đã đóng tất cả các lệnh! [DNSE]")
        else:
            self.entradeClient.CloseAllDeals(self.is_demo)
            self.logger.warning(f"Đã đóng tất cả các lệnh! [ENTRADE]")
        
        #reset các biến
        self.order_id = None
        self.orderStatus = None
        self.breakevenPrice=None
        self.position_side = None
        self.orderQuantity=0
        self.order_side=None
        self.unrealisedNetProfit = 0

    def execute_trade_entrade(self, action, is_demo = True):
        '''
        Thực hiện lệnh mua/bán dựa trên tín hiệu từ check_for_signals
        action = "LONG" hoặc "SHORT", CLOSELONG, CLOSESHORT
        '''
        # kiểm tra số deal đang mở đã vượt quá max open trades allowed chưa?

        # lấy giá hiện tại khi có tín hiệu
        if self.orderPriceType == "MTL":
            self.orderPrice = None
        else:
            if self.spread is not None: 
                self.orderPrice = self.lastTickPrice + (self.spread if action.uppper()=="LONG" else -1*self.spread)  # Lấy giá đóng cửa mới nhất
            else:
                self.orderPrice = self.lastTickPrice + 2

        if action.upper() == "LONG":

            try:
                self.logger.info(f"[ENTRADE] Thực hiện đặt {self.trade_size} hợp đồng LONG tại giá {self.orderPrice if self.orderPrice is not None else 'MTL'}")
                # Thực hiện lệnh mua ở đây
                result = self.entradeClient.Order(self.symbol, "NB", self.orderPrice, None, self.trade_size, self.orderPriceType, is_demo)

                self.position_side = "LONG"
                # deals = self.entradeClient.GetActiveDeals()
                # for deal in deals:
                #     self.order_id = deal.get("id")
                #     self.order_entryprice = deal.get("breakEvenPrice")
                #     self.order_side = deal.get("side")
                #     self.orderQuantity = deal.get("openQuantity")
            except Exception as e:
                self.logger.error(f"Đã xảy ra lỗi: {e}")

        elif action.upper() == "SHORT":
            
            try:
                self.logger.info(f"[ENTRADE] Thực hiện đặt {self.trade_size} hợp đồng SHORT tại giá {self.orderPrice if self.orderPrice is not None else 'MTL'}")
                # Thực hiện lệnh bán ở đây
                # result = self.entradeClient.Order(self.symbol, "NS", self.orderPrice, None, self.trade_size, self.orderPriceType, self.is_demo)

                result = self.entradeClient.Order(symbol=self.symbol, 
                                                  side="NS", 
                                                  price=self.orderPrice, 
                                                  loan = None, 
                                                  volume=self.trade_size, 
                                                  order_type=self.orderPriceType, 
                                                  is_demo= self.is_demo)
                
                self.position_side = "SHORT"
                # deals = self.entradeClient.GetActiveDeals()
                # for deal in deals:
                #     self.order_id = deal.get("id")
                #     self.order_entryprice = deal.get("breakEvenPrice")
                #     self.order_side = deal.get("side")
                #     self.orderQuantity = deal.get("openQuantity")
            except Exception as e:
                self.logger.error(f"Đã xảy ra lỗi: {e}")

                
        elif action.upper() == "CLOSELONG":
            if self.position_side == "BUY":
                self.logger.info(f"[ENTRADE] Đóng tất cả các lệnh, lý do = {action}")
                # Thực hiện lệnh đóng mua ở đây
                result = self.entradeClient.CloseAllDeals(is_demo)
                self.position_side = None
                self.order_entryprice = None
                self.order_id = None
                self.order_side = None
                self.orderQuantity = None
            else:
                self.logger.error("No BUY position to close.")

        elif action.upper() == "CLOSESHORT":
            if self.position_side == "SELL":
                self.logger.info(f"[ENTRADE] Đóng tất cả các lệnh, lý do = {action}")
                # Thực hiện lệnh đóng mua ở đây
                result = self.entradeClient.CloseAllDeals(is_demo)
                self.position_side = None
                self.order_entryprice = None
                self.order_id = None
                self.order_side = None
                self.orderQuantity = None
            else:
                self.logger.info("No SELL position to close.")
        else:
            self.logger.info("No valid action to execute.")
    
    def execute_trade_DNSE(self, action):
        '''
        Thực hiện lệnh mua/bán dựa trên tín hiệu từ check_for_signals
        action = "BUY" hoặc "SELL", CLOSEBUY, CLOSESELL
        '''
        # kiểm tra số deal đang mở đã vượt quá max open trades allowed chưa?

        # lấy giá hiện tại khi có tín hiệu
        if self.orderPriceType == "MTL":
            self.orderPrice = self.lastTickPrice + 5*self.spread
        else:
            # self.orderPrice = self.marketData[self.timeframe][4]  # Lấy giá đóng cửa mới nhất
            self.orderPrice = (self.lastTickPrice + self.spread) if action.upper() == "LONG" else (self.lastTickPrice - self.spread)


        if action.upper() == "LONG":

            try:
                self.logger.info(f"[DNSE] Thực hiện đặt {self.trade_size} hợp đồng LONG tại giá {self.orderPrice}")
                # Thực hiện lệnh mua ở đây
                result = self.dnseClient.Order( symbol=self.symbol,
                                                    account = self.investor_account_id,
                                                    side = "NB",
                                                    price = self.orderPrice,
                                                    loan = self.loanpackageid,
                                                    volume = self.trade_size,
                                                    order_type = self.orderPriceType)
                

                self.position_side = "LONG"
                
                # deal = self.dnseClient.GetOrderDetail(result['id'],self.investor_account_id)
                # self.order_id = deal.get("id")
                # self.orderStatus=deal.get('orderStatus')
                # self.order_entryprice = deal.get("breakEvenPrice")
                # self.order_side = deal.get("side")
                # self.orderQuantity = deal.get("openQuantity")

                #lưu lệnh mở đầu tiên
                if self.firstDeal is None:
                    self.firstDeal=deal
                self.lastDeal = deal

            except Exception as e:
                self.logger.error(f'Xảy ra lỗi: {e}')

        elif action.upper() == "SHORT":

            try:
                self.logger.info(f"[DNSE] Thực hiện đặt {self.trade_size} hợp đồng SHORT tại giá {self.orderPrice}")
                # Thực hiện lệnh bán ở đây
                result = self.dnseClient.Order( symbol=self.symbol,
                                                account = self.investor_account_id,
                                                side = "NS",
                                                price = self.orderPrice,
                                                loan = self.loanpackageid,
                                                volume = self.trade_size,
                                                order_type = self.orderPriceType)
                self.position_side = "SHORT"
                deal = self.dnseClient.GetOrderDetail(result['id'],self.investor_account_id)
                # self.order_id = deal.get("id")
                # self.orderStatus=deal.get('orderStatus')
                # self.order_entryprice = deal.get("breakEvenPrice")
                # self.order_side = deal.get("side")
                # self.orderQuantity = deal.get("openQuantity")

                #lưu lệnh mở đầu tiên
                if self.firstDeal is None:
                    self.firstDeal=deal
                self.lastDeal = deal

            except:
                self.logger.error(f'Xảy ra lỗi: {e}')

                
        elif action.upper() == "CLOSELONG":
            # Thực hiện lệnh đóng mua ở đây
                self.logger.info(f"[DNSE] Đóng tất cả các lệnh, lý do = {action}")
                result = self.dnseClient.CloseAllDeals()
                self.position_side = None
                self.order_entryprice = None
                self.order_id = None
                self.order_side = None
                self.orderQuantity = None

        elif action.upper() == "CLOSESHORT":
            # Thực hiện lệnh đóng mua ở đây
                self.logger.info(f"[DNSE] Đóng tất cả các lệnh, lý do = {action}")
                result = self.dnseClient.CloseAllDeals()
                self.position_side = None
                self.order_entryprice = None
                self.order_id = None
                self.order_side = None
                self.orderQuantity = None
        else:
            self.logger.info("No valid action to execute.")
    
    def getTotalOpenQuanity_DNSE(self) -> int:

        '''
        Mục đích lấy tổng số hợp động đang mở DNSE.
        '''
        if self.dnseClient is not None:
            return self.dnseClient.GetTotalOpenQuantity()
        else:
            return 0 
    
    def getTotalOpenQuanity_Entrade(self) -> int:

        '''
        Mục đích lấy tổng số hợp động đang mở ở Entrade.
        '''
        if self.dnseClient is not None:
            return self.entradeClient.GetTotalOpenQuantity()
        else:
            return 0 
    
    def cprint(self, message):
        '''
        Hàm hỗ trợ in ra console có bao gồm ngày tháng và giờ.
        '''
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{ts}] - {message}")
