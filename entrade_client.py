from requests import HTTPError, get, post, delete
from time import localtime
from data_processor import GetOHLCVData
import time

class EntradeClient:
    def __init__(self):
        self.token = None
        self.investor_id = None
        self.investor_account_id = None
        # https://services-staging.entrade.com.vn/papertrade-entrade-api/derivative/orders
        self.base_url = f"https://services.entrade.com.vn/"


    def Authenticate(self, username, password):
        _json = {
            "username": username,
            "password": password
        }

        url = f"{self.base_url}entrade-api/v2/auth"
        response = post(url, json=_json)
        response.raise_for_status()
        self.token = response.json().get("token")
        print("Đăng nhập thành công! (Entrade)")

    def Order(self, symbol, side, price, loan, volume, order_type, is_demo: bool):
        
        """Đặt lệnh với kiểm tra đầu vào và xử lý lỗi nâng cao"""
        
        self._validate_order_params(symbol, side, price, volume)
        
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
            print(f"Đặt lệnh {order_type} thành công: {order_data['id']}")
            return order_data
        except HTTPError as e:
            print("Order() failed! (Entrade):", e)
    
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
            print("Hủy lệnh thành công! (Entrade)")
            return response.json()
        except HTTPError as e:
            print("CancelOrder() failed! (Entrade):", e)

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
            print("Hủy tất cả lệnh thành công! (Entrade)")
            return response.json()
        except HTTPError as e:
            print("CancelAllOrders() failed! (Entrade):", e)

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
            print("Gửi yêu cầu đặt lệnh điều kiện thành công! (Entrade)")
            return response.json()
        except HTTPError as e:
            print("ConditionalOrder() failed! (Entrade):", e)

    def CancelConditionalOrder(self, order_id, is_demo: bool):
        _headers = {
            "Authorization": f"Bearer {self.token}"
        }

        url = f"{self.base_url}{"papertrade-" if is_demo else ""}smart-order/orders/{order_id}"

        try:
            response = delete(url, headers=_headers)
            response.raise_for_status()
            print("Hủy lệnh thành công! (Entrade)")
            return response.json()
        except HTTPError as e:
            print("CancelConditionalOrder() failed! (Entrade):", e)

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
            print("Hủy tất cả lệnh thành công! (Entrade)")
            return response.json()
        except HTTPError as e:
            print("CancelAllConditionalOrder() failed! (Entrade):", e)

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
            print("Hủy lệnh thành công! (Entrade)")
            return response.json()
        except HTTPError as e:
            print("CloseDeal() failed! (Entrade):", e)

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
        activeDeals = []
        for deal in deals:
            if deal["status"] == "ACTIVE":
                activeDeals.append(deal)
        return activeDeals

    def CloseAllDeals(self, is_demo: bool):
        try:
            deals = self.GetDeals(0, 255, is_demo)["data"]
            for deal in deals:
                if deal["status"] == "ACTIVE":
                    self.CloseDeal(deal["id"], is_demo)

            print("Đóng tất cả lệnh thành công! (Entrade)")
        except HTTPError as e:
            print("CloseAllDeals() failed! (Entrade):", e)
            
            
    def GetBars(self, 
                             symbol: str, 
                             timeframe: str = "", 
                             days_lookback: int = 30):
        
        """Lấy marketdata theo timeframe"""

        start_time = int(time.time()) - 86400*days_lookback # 30 ngày dữ liệu
        
        try:
            raw_data = GetOHLCVData("derivative", "VN30F1M", start_time, int(time()), timeframe)
            
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
            print("Lỗi khi get marketdata", e)
            

    