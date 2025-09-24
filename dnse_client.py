import time
from requests import get, post
from time import localtime

class DNSEClient:
    def __init__(self):
        self.token = None
        self.trading_token = None
        self.investor_id = None
        self.base_url = "https://api.dnse.com.vn/"

    def Authenticate(self, username, password):
        _headers = {
            "Content-Type": "application/json"
        }
        _json = {
            "username": username,
            "password": password
        }

        url = f"{self.base_url}auth-service/login"
        response = post(url, json=_json, headers=_headers)
        response.raise_for_status()
        self.token = response.json().get("token")
        print("Đăng nhập thành công! (DNSE)")

    def GetAccountInfo(self):
        _headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }

        url = f"{self.base_url}user-service/api/me"
        response = get(url, headers=_headers)
        response.raise_for_status()
        self.investor_id = response.json().get("investorId")
        return response.json()

    def GetOTP(self):
        _headers = {
            "Authorization": f"Bearer {self.token}"
        }

        url = f"{self.base_url}auth-service/api/email-otp"
        response = get(url, headers=_headers)
        response.raise_for_status()
        print("Gửi OTP thành công! (DNSE)")

    def GetTradingToken(self, otp):
        url = f"{self.base_url}/order-service/trading-token"
        _headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "otp": otp
        }
        response = post(url, headers=_headers)
        response.raise_for_status()
        self.trading_token = response.json().get("tradingToken")
        print("Lấy Trading Token thành công! (DNSE)")

    def Order(self, symbol, account, side, price, loan, volume, order_type):
        url = f"{self.base_url}order-service/v2/orders" # Default to normal stock :3
        loan_package_id = 1372

        if len(symbol) > 3:
            url = f"{self.base_url}order-service/derivative/orders"
            loan_package_id = 2278

        _headers = {
            "content-type": "application/json",
            "authorization": f"Bearer {self.token}",
            "trading-token": self.trading_token
        }
        _json = {
            "accountNo": account,
            "loanPackageId": loan or loan_package_id,
            "orderType": order_type,
            "price": price,
            "quantity": volume,
            "side": side,
            "symbol": symbol
        }
        response = post(url, headers=_headers, json=_json)
        response.raise_for_status()
        print("Gửi yêu cầu đặt lệnh thành công! (DNSE)")
        return response.json()

    def ConditionalOrder(self, symbol, account : int, side, price : float, loan, volume, order_type, condition):
        url = f"{self.base_url}conditional-order-api/v1/orders"

        # Default to derivative
        loan_package_id = 2278
        market_id = "DERIVATIVES"

        if len(symbol) < 4: # It's normal stock :3
            loan_package_id = 1372
            market_id = "UNDERLYING"

        _headers = {
            "content-type": "application/json",
            "authorization": f"Bearer {self.token}",
            "trading-token": self.trading_token
        }

        current_time = localtime()
        _json = {
            "condition": condition,
            "targetOrder": {"quantity": volume, "side": side, "price": price, "loanPackageId": loan or loan_package_id, "orderType": order_type},
            "symbol": symbol,
            "props": {"stopPrice": int(condition[9:]), "marketId": market_id},
            "accountNo": account,
            "category": "STOP",
            "timeInForce": {"expireTime": f"{current_time.tm_year}-{current_time.tm_mon:02d}-{current_time.tm_mday:02d}T07:30:00.000Z", "kind": "GTD"}
        }
        response = post(url, headers=_headers, json=_json)
        response.raise_for_status()
        print("Gửi yêu cầu đặt lệnh điều kiện thành công! (DNSE)")
        return response.json()

    

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
            print("Lỗi khi get marketdata", e)

    def GetCashAccount(self, account_no=None):
        """Lấy thông tin tài sản tiền mặt"""
        account = account_no or self.account_no or "0001910385"
        if not account:
            raise ValueError("Account number is required")
            
        _headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }
        
        params = {"accountNo": account}

        url = f"{self.base_url}derivative-core/cash-accounts"
        response = get(url, headers=_headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def SetAccountPnLConfig(self, config, account_no=None):
        """Cài đặt chốt lời cắt lỗ theo account"""
        if not self.trading_token:
            raise ValueError("Trading token not available. Please ensure tokens are loaded from MongoDB.")
            
        account = account_no or self.account_no or "0001910385"
        if not account:
            raise ValueError("Account number is required")

        _headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
            "Trading-Token": self.trading_token
        }

        url = f"{self.base_url}derivative-deal-risk/account-pnl-configs/{account}"
        response = post(url, headers=_headers, json=config)
        response.raise_for_status()
        print("Cài đặt chốt lời cắt lỗ theo account thành công! (DNSE)")
        return response.json()
    
    def SetDealPnLConfig(self, deal_id, config):
        """Cài đặt chốt lời cắt lỗ theo deal"""
        if not self.trading_token:
            raise ValueError("Trading token not available. Please ensure tokens are loaded from MongoDB.")

        _headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
            "Trading-Token": self.trading_token
        }

        url = f"{self.base_url}derivative-deal-risk/pnl-configs/{deal_id}"
        response = post(url, headers=_headers, json=config)
        response.raise_for_status()
        print("Cài đặt chốt lời cắt lỗ theo deal thành công! (DNSE)")
        return response.json()
    
    def CloseDeal(self, deal_id):
        """Đóng deal"""
        if not self.trading_token:
            raise ValueError("Trading token not available. Please ensure tokens are loaded from MongoDB.")

        _headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
            "Trading-Token": self.trading_token
        }

        url = f"{self.base_url}derivative-core/deals/{deal_id}/close"
        response = post(url, headers=_headers)
        response.raise_for_status()
        print("Đóng deal thành công! (DNSE)")
        return response.json()
    
    def GetDeals(self, account_no=None):
        """Lấy danh sách deal nắm giữ"""
        account = account_no or self.account_no or "0001910385"
        if not account:
            raise ValueError("Account number is required")
            
        _headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }
        
        params = {"accountNo": account}

        url = f"{self.base_url}derivative-core/deals"
        response = get(url, headers=_headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def CancelOrder(self, order_id, account_no=None):
        """Hủy lệnh"""
        if not self.trading_token:
            raise ValueError("Trading token not available. Please ensure tokens are loaded from MongoDB.")
            
        account = account_no or self.account_no or "0001910385"
        if not account:
            raise ValueError("Account number is required")

        _headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
            "Trading-Token": self.trading_token
        }
        
        params = {"accountNo": account}

        try:
            url = f"{self.base_url}order-service/derivative/orders/{order_id}"
            self.logger.info(f"Cancelling order: {order_id}")
            
            response = delete(url, headers=_headers, params=params)
            response.raise_for_status()
            result = response.json()
            
            # Log trading action
            log_trade_action(
                action="ORDER_CANCELLED",
                order_id=order_id,
                account=account
            )
            
            self.logger.info(f"Order cancelled successfully - ID: {order_id}")
            return result
            
        except Exception as e:
            log_error_with_context(self.logger, e, "Failed to cancel order",
                                 order_id=order_id, account=account)
            raise

    def GetOrderDetail(self, order_id, account_no=None):
        """Lấy chi tiết lệnh"""
        account = account_no or self.account_no or "0001910385"
        if not account:
            raise ValueError("Account number is required")
            
        _headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }
        
        params = {"accountNo": account}

        url = f"{self.base_url}order-service/derivative/orders/{order_id}"
        response = get(url, headers=_headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def GetOrders(self, account_no=None):
        """Lấy danh sách lệnh"""
        account = account_no or self.account_no or "0001910385"
        if not account:
            raise ValueError("Account number is required")
            
        _headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }
        
        params = {"accountNo": account}

        url = f"{self.base_url}order-service/derivative/orders"
        response = get(url, headers=_headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def GetPPSE(self, symbol, price, loan_package_id, account_no=None):
        """Lấy thông tin sức mua sức bán"""
        account = account_no or self.account_no or "0001910385"
        if not account:
            raise ValueError("Account number is required")
            
        _headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }
        
        params = {
            "symbol": symbol,
            "price": price,
            "loanPackageId": loan_package_id
        }

        url = f"{self.base_url}order-service/accounts/{account}/derivative-ppse"
        response = get(url, headers=_headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def GetDerivativeLoanPackages(self, account_no=None):
        """Lấy danh sách gói vay phái sinh"""
        account = account_no or self.account_no or "0001910385"
        if not account:
            raise ValueError("Account number is required")
            
        _headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }

        url = f"{self.base_url}order-service/accounts/{account}/derivative-loan-packages"
        response = get(url, headers=_headers)
        response.raise_for_status()
        return response.json()