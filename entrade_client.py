from datetime import datetime, time
from requests import HTTPError, get, post, delete
from time import localtime
from data_processor import GetOHLCVData
from logger_config import get_trading_logger, setup_logger
import logging

class EntradeClient:
    def __init__(self):
        self.usernameEntrade = None 
        self.passwordEntrade=None
        self.token = None
        self.createdtimeToken = None    #lưu thời gian bắt đầu lấy token, lưu dạng năm-tháng-ngày giờ-phút-giây
        self.investor_id = None or '1000053980'
        self.investor_account_id = None or '1000053980'
        # https://services-staging.entrade.com.vn/papertrade-entrade-api/derivative/orders
        self.base_url = f"https://services.entrade.com.vn/"
    
        # Setup logger
        self.logger = setup_logger("[ENTRADE_Client]", logging.INFO)
        self.trading_logger = get_trading_logger()


    def Authenticate(self, username = None, password = None):
        _json = {
            "username": username or self.usernameEntrade,
            "password": password or self.passwordEntrade
        }

        url = f"{self.base_url}entrade-api/v2/auth"
        response = post(url, json=_json)
        response.raise_for_status()
        self.token = response.json().get("token")
        print("Đăng nhập thành công! (Entrade)")

    def Order(self, symbol, side, price, loan, volume, order_type, is_demo: bool):
        
        """Đặt lệnh với kiểm tra đầu vào và xử lý lỗi nâng cao"""
        
        #Kiểm tra lệnh được đặt trong thời gian cho phép hay không? 8h05 -> 15h
        
        # Chuyển đổi thời gian bắt đầu và kết thúc sang đối tượng datetime.time
        thoi_gian_bat_dau = datetime.strptime("08:05", "%H:%M").time()
        thoi_gian_ket_thuc = datetime.strptime("15:00", "%H:%M").time()        
        thoi_gian_hien_tai = datetime.now().time()  # Lấy thời gian hiện tại
        
       
        # Kiểm tra xem thời gian hiện tại có nằm trong khoảng cho phép hay không
        if not (thoi_gian_bat_dau <= thoi_gian_hien_tai <= thoi_gian_ket_thuc):
            self.logger.warning("Chỉ được đặt lệnh từ 08:05 đến 15:00.")
            return



        _headers = {
            "Authorization": f"Bearer {self.token}"
        }
        _json = {
            "symbol": symbol.upper(),
            "side": side.upper(),
            "orderType": order_type.upper(),
            "price": price,
            "quantity": volume,
            "bankMarginPortfolioId": loan or (32 if is_demo else 37),
            "investorId": self.investor_id
        }

        url = f"{self.base_url}{"papertrade-" if is_demo else ""}entrade-api/derivative/orders"

        try:
            response = post(url, headers=_headers, json=_json)
            response.raise_for_status()
            order_data = response.json()
            self.logger.info(f"Đặt lệnh {order_type} thành công [Entrade]: {order_data['id']}")
            return order_data
        except HTTPError as e:
            self.logger.error("Order() failed! (Entrade):", exc_info=True)
            return None
    
    def _validate_order_params(self, symbol: str, side: str, price: float, volume: int):
       """Kiểm tra tính hợp lệ của tham số lệnh"""
       if price <= 0:
           raise ValueError("Giá phải lớn hơn 0")
       if volume % 1 != 0:
           raise ValueError("Khối lượng phải là bội số của 1")
       if side.upper() not in ["NB", "NS"]:
           raise ValueError("Loại lệnh không hợp lệ")
       if not self._is_valid_symbol(symbol):
           raise ValueError(f"Mã chứng khoán {symbol} không hợp lệ")
    
    def CancelOrder(self, order_id, is_demo: bool):
        _headers = {
            "Authorization": f"Bearer {self.token}"
        }

        url = f"{self.base_url}{"papertrade-" if is_demo else ""}entrade-api/derivative/orders/{order_id}"

        try:
            response = delete(url, headers=_headers)
            response.raise_for_status()
            self.logger.info("Hủy lệnh thành công! (Entrade)")
            return response.json()
        except HTTPError as e:
            self.logger.info("CancelOrder() failed! (Entrade):", e)

    def CancelAllOrders(self, is_demo: bool):
        _headers = {
            "Authorization": f"Bearer {self.token}"
        }
        _params = {
            "investorId": self.investor_id,
            "investorAccountId": self.investor_account_id
        }

        url = f"{self.base_url}{"papertrade-" if is_demo else ""}entrade-api/derivative/orders"

        try:
            response = delete(url, headers=_headers, params=_params)
            response.raise_for_status()
            self.logger.info("Hủy tất cả lệnh thành công! (Entrade)")
            return response.json()
        except HTTPError as e:
            self.logger.info("CancelAllOrders() failed! (Entrade):", e)

    def ConditionalOrder(self, symbol, side, price, loan, volume, condition, is_demo: bool):
        _headers = {
            "Authorization": f"Bearer {self.token}"
        }

        current_time = localtime()
        _json = {
            "bankMarginPortfolioId": loan or (32 if is_demo else 37),
            "condition": condition,
            "expiredTime": f"{current_time.tm_year}-{current_time.tm_mon:02d}-{current_time.tm_mday:02d}T07:30:00.000Z",
            "investorAccountId": self.investor_account_id,
            "investorId": self.investor_id,
            "symbol": symbol,
            "targetPrice": price,
            "targetQuantity": volume,
            "targetSide": side,
            "type": "STOP"
        }

        url = f"{self.base_url}{"papertrade-" if is_demo else ""}smart-order/orders"

        try:
            response = post(url, headers=_headers, json=_json)
            response.raise_for_status()
            self.logger.info("Gửi yêu cầu đặt lệnh điều kiện thành công! (Entrade)")
            return response.json()
        except HTTPError as e:
            self.logger.info("ConditionalOrder() failed! (Entrade):", e)

    def CancelConditionalOrder(self, order_id, is_demo: bool):
        _headers = {
            "Authorization": f"Bearer {self.token}"
        }

        url = f"{self.base_url}{"papertrade-" if is_demo else ""}smart-order/orders/{order_id}"

        try:
            response = delete(url, headers=_headers)
            response.raise_for_status()
            self.logger.info("Hủy lệnh thành công! (Entrade)")
            return response.json()
        except HTTPError as e:
            self.logger.info("CancelConditionalOrder() failed! (Entrade):", e)

    def CancelAllConditionalOrder(self, is_demo: bool):
        _headers = {
            "Authorization": f"Bearer {self.token}"
        }
        _params = {
            "investorId": self.investor_id,
            "investorAccountId": self.investor_account_id
        }

        url = f"{self.base_url}{"papertrade-" if is_demo else ""}smart-order/orders"

        try:
            response = delete(url, headers=_headers, params=_params)
            response.raise_for_status()
            self.logger.info("Hủy tất cả lệnh thành công! (Entrade)")
            return response.json()
        except HTTPError as e:
            self.logger.info("CancelAllConditionalOrder() failed! (Entrade):", e)

    def CloseDeal(self, deal_id, is_demo: bool):
        _headers = {
            "Authorization": f"Bearer {self.token}"
        }
        _json = {
            "orderType":"LO",
            "triggeredBy":"close-deal"
        }

        url = f"{self.base_url}{"papertrade-" if is_demo else ""}entrade-api/derivative/deals/{deal_id}/_close_deal"

        try:
            response = post(url, headers=_headers, json=_json)
            response.raise_for_status()
            self.logger.info("Hủy lệnh thành công! (Entrade)")
            return response.json()
        except HTTPError as e:
            self.logger.info("CloseDeal() failed! (Entrade):", e)

    def GetAccountInfo(self):
        _headers = {
            "Authorization": f"Bearer {self.token}"
        }
        url = f"{self.base_url}entrade-api/investors/_me"

        response = get(url, headers=_headers)
        response.raise_for_status()
        json_data = response.json()
        self.investor_id = json_data.get("investorId")
        return json_data

    def GetAccountBalance(self):
        _headers = {
            "Authorization": f"Bearer {self.token}"
        }
        url = f"{self.base_url}entrade-api/account_balances/{self.investor_id}"

        response = get(url, headers=_headers)
        response.raise_for_status()
        json_data = response.json()
        self.investor_account_id = json_data.get("investorAccountId")
        return json_data

    def GetDeals(self, start: int = 0, end: int = 100, is_demo: bool = True):
        _headers = {
            "Authorization": f"Bearer {self.token}"
        }
        _params = {
            "investorId": self.investor_id,
            "_start": start,
            "_end": end
        }

        url = f"{self.base_url}{"papertrade-" if is_demo else ""}entrade-api/derivative/deals"

        response = get(url, headers=_headers, params=_params)
        response.raise_for_status()
        return response.json()

    def GetActiveDeals(self,investorAccountId: str = None):
        deals = self.GetDeals()["data"]
        for deal in deals:
            if deal["status"] == "ACTIVE" and deal['investorAccountId'] == investorAccountId or self.investor_account_id:
                return deal
        return 0

    def CloseAllDeals(self, is_demo: bool):
        try:
            deals = self.GetDeals(0, 255, is_demo)["data"]
            for deal in deals:
                if deal["status"] == "ACTIVE":
                    self.CloseDeal(deal["id"], is_demo)

            self.logger.info("Đóng tất cả lệnh thành công! (Entrade)")
        except HTTPError as e:
            self.logger.info("CloseAllDeals() failed! (Entrade):", e)
            
            
    def GetBars(self, 
                             symbol: str, 
                             timeframe: str = "", 
                             days_lookback: int = 30):
        
        """Lấy marketdata theo timeframe"""

        start_time = int(time.time()) - 86400*days_lookback # 30 ngày dữ liệu
        
        try:
            raw_data = GetOHLCVData("derivative", "VN30F1M", start_time, int(time.time()), timeframe)
            
            # Tạo dữ liệu base với timestamp
            base_data = list(zip(
                raw_data['t'],
                raw_data['o'],
                raw_data['h'],
                raw_data['l'],
                raw_data['c'],
                raw_data['v']
            ))
            
            return base_data
        
        except HTTPError as e:
            self.logger.info("Lỗi khi get marketdata", e)
            
    def GetTotalOpenQuantity(self, investor_account_id = None):
        #get active deals
        activeDeal = self.GetActiveDeals(investor_account_id or self.investor_account_id)
        totalVol = activeDeal['openQuantity']
        return totalVol
    
    def validate_token(self, usernameEntrade = None, passwordEntrade = None):
        '''
        Loggin, và lấy token cho tài khoản Entrade
        '''
        try:
            self.Authenticate(usernameEntrade or self.usernameEntrade, passwordEntrade or self.passwordEntrade)
            self.GetAccountInfo() # Get investor_id
            self.GetAccountBalance() # Get investor_account_id
            self.usernameEntrade = usernameEntrade if self.usernameEntrade == None else self.usernameEntrade
            self.passwordEntrade = passwordEntrade if self.passwordEntrade == None else self.passwordEntrade

        except Exception as e:
            self.logger.error("Đã xảy ra lỗi : {e}")
    
    def GetCeilingAndFloorPrices_VN30F1M(self):
        '''
        Tính toán giá trần sàn của phiên hiện tại
        Trả về 1 dict ceilingandFloorPrice{}
        '''
        #lấy data 1D
        days_lookback = 30
        start_time = int(time.time()) - 86400*days_lookback # 30 ngày dữ liệu
        data = GetOHLCVData("derivative","VN30F1M", start_time, int(time.time()),"1D")  #trả về nến 1D 
        # cấu trúc data =  {'t':[], 'o':[],'h':[],'l':[],'c':[]}
        i = 1

        # Lấy ngày hiện tại
        today = datetime.today().date()

        ceilingandFloorPrice ={
            'ceilingprice' : None,
            'floorprice' : None
        }
        for i in range(1,29,1):
            timestamp = data['t'][len(data['t'])-i]
            date_from_timestamp = datetime.fromtimestamp(timestamp).date()
            if date_from_timestamp < today:
                closePrice = data['c'][len(data['t'])-i]
                ceilingandFloorPrice['ceilingprice'] = round(closePrice*1.069,0)    #+6.9%
                ceilingandFloorPrice['floorprice'] = round(closePrice*0.931,0)      #-6.9%
                return ceilingandFloorPrice
            

    def GetPendingOrders(self, is_demo = True):
        """
        Lấy các lệnh đang chờ khớp lệnh trong sổ lệnh.
        """
        deals = self.GetDeals(start=0, end=100, is_demo=is_demo)["data"]  #đọc tất cả lệnh trong sổ lệnh
        pendingOrders =[]
        for deal in deals:
            if deal['status'].lower() == 'pending' or deal['status'].lower() == 'pendingnew' or deal['status'].lower() == 'new'  :     
                pendingOrders.append(deal)

        return pendingOrders 

    