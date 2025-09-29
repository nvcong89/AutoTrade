from datetime import datetime, timedelta
import time
import os
from requests import HTTPError, get, post, delete
from time import localtime
from logger_config import setup_logger, get_trading_logger, log_trade_action, log_error_with_context
import json
from typing import Optional, Dict
from mail_reader import getOTP
from data_processor import GetOHLCVData

class DNSEClient:
    def __init__(self):
        self.emailDNSE = None
        self.passwordDNSE=None
        self.token = None
        self.trading_token = None   #Trading token sẽ được sử dụng trong các API chỉnh sửa dữ liệu: đặt lệnh, huỷ lệnh
        self.createdtimeToken = None    #lưu thời gian bắt đầu lấy token, lưu dạng năm-tháng-ngày giờ-phút-giây, isoformat
        self.investor_id = None #mã tài khoản
        self.investor_account_id = None #mã tiểu khoản
        self.OTP = None
        self.loanpackageID = None
        self.base_url = "https://api.dnse.com.vn/"

        # Setup logger
        self.logger = setup_logger("[DNSE_Client]")
        self.trading_logger = get_trading_logger()

    def Authenticate(self, username=None, password=None):
        _headers = {
            "Content-Type": "application/json"
        }
        _json = {
            "username": username or self.emailDNSE,
            "password": password or self.passwordDNSE
        }

        url = f"{self.base_url}auth-service/login"
        response = post(url, json=_json, headers=_headers)
        response.raise_for_status()
        self.token = response.json().get("token")
        self.createdtimeToken = datetime.now().isoformat()  #example : 2025-09-28T20:48:15.123456
        print("Đăng nhập thành công! (DNSE)")
        
    
    def GetSubAccounts(self):
        """Lấy danh sách tiểu khoản"""
        _headers = {
            "Authorization": f"Bearer {self.token}"
        }

        url = f"{self.base_url}order-service/accounts"
        response = get(url, headers=_headers)
        response.raise_for_status()
        self.investor_account_id = response.json()['default']['id']
        return response.json()  #trả về danh sách các tiểu khoản []

    def GetAccountInfo(self):
        try:
            _headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.token}"
            }

            url = f"{self.base_url}user-service/api/me"
            response = get(url, headers=_headers)
            response.raise_for_status()
            self.investor_id = response.json().get("investorId")
            return response.json()
        except Exception as e:
            self.logger.critical(f"Đã xảy ra lỗi khi GetAccountInfor: {e}")
            pass

    def GetOTP(self):
        _headers = {
            "Authorization": f"Bearer {self.token}"
        }

        url = f"{self.base_url}auth-service/api/email-otp"
        response = get(url, headers=_headers)
        response.raise_for_status()
        self.logger.info("Gửi email OTP thành công! (DNSE)")
    
    def readSmartOTP(self, otp: str = None):
        if otp is None:
            smartOTP = input(f"Nhập mã SmartOTP:")
            self.OTP = smartOTP
        else:
            self.OTP = otp
        
        return self.OTP


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
        self.logger.info("Lấy Trading Token thành công! (DNSE)")
    
    def GetDerivativeLoanPackages(self, account_no=None):
        """Lấy danh sách gói vay phái sinh"""
        account = account_no or self.account_no or "0001521007"
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


    def Order(self, symbol, account, side, price, loan, volume, order_type):
        '''
        Đặt lệnh lên DNSE
        detail see this link:  https://hdsd.dnse.com.vn/san-pham-dich-vu/lightspeed-api_krx/ii.-trading-api/5.-giao-dich-phai-sinh/5.3.-dat-lenh
        '''
        url = f"{self.base_url}order-service/v2/orders" # Default to normal stock :3
        loan_package_id = self.loanpackageID

        if len(symbol) > 3:
            url = f"{self.base_url}order-service/derivative/orders"
            loan_package_id = self.loanpackageID

        _headers = {
            "content-type": "application/json",
            "authorization": f"Bearer {self.token}",
            "trading-token": self.trading_token
        }
        _json = {
            "accountNo": account,   #số tiểu khoản  
            "loanPackageId": loan_package_id or loan,   #mã gói vay
            "orderType": order_type,    #Loại lệnh: LO, MTL, ATO
            "price": price,     # double, giá đặt lệnh
            "quantity": volume, # int, số hợp đồng
            "side": side,   #Lệnh mua NB, lệnh bán NS
            "symbol": symbol    #Mã ví dụ VN30F1M
        }
        response = post(url, headers=_headers, json=_json)
        response.raise_for_status()
        self.logger.info("Gửi yêu cầu đặt lệnh thành công! [DNSE]")
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
        self.logger.info("Gửi yêu cầu đặt lệnh điều kiện thành công! (DNSE)")
        return response.json()

    

    def GetBars(self, 
                symbol: str =None, 
                timeframe: str = "", 
                days_lookback: int = 30):
        
        """Lấy marketdata theo timeframe"""
        # **resolution**: 1, 3, 5, 15, 30, 1H, 1D, 1W (nến 1/3/5/... phút)

        start_time = int(time.time()) - 86400*days_lookback # 30 ngày dữ liệu
        
        try:
            raw_data = GetOHLCVData("derivative",symbol or "VN30F1M", start_time, int(time.time()), timeframe)
            
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

    def GetCashAccount(self, account_no=None):
        """Lấy thông tin tài sản tiền mặt"""
        account = account_no or self.investor_account_id
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
            
        account = account_no or self.investor_account_id
        if not account:
            raise ValueError("[SetAccountPnLConfig] : Account number is required")

        _headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
            "Trading-Token": self.trading_token
        }

        url = f"{self.base_url}derivative-deal-risk/account-pnl-configs/{account}"
        response = post(url, headers=_headers, json=config)
        response.raise_for_status()
        self.logger.info("Cài đặt chốt lời cắt lỗ theo account thành công! (DNSE)")
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
        self.logger.info("Cài đặt chốt lời cắt lỗ theo deal thành công! (DNSE)")
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
        self.logger.info("Đóng deal thành công! (DNSE)")
        return response.json()
    
    def CloseAllDeals(self):
        """Đóng tất cả deal đang mở"""

        #lấy danh dách active deal ids
        activedeacl_IDs = self.getActiveDeals_ID(self.investor_account_id)
        for id in activedeacl_IDs:
            self.CloseDeal(id)
            self.logger.warning(f"Đã đóng deal id: {id}")

    def GetTotalOpenQuantity(self, investor_account_id=None) -> int:
        #get active deals
        activeDeal = self.getActiveDeals(investor_account_id or self.investor_account_id)
        if activeDeal:
            return activeDeal['openQuantity']
        else:
            return 0
        
        

    
    def GetDeals(self, investor_account_id=None):
        """Lấy danh sách deal nắm giữ"""
        account = investor_account_id or self.investor_account_id
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
    
    def getActiveDeals(self, investor_account_id = None):    #tiểu khoản
        deals = self.GetDeals(investor_account_id)["data"]
        for deal in deals:
            if deal["status"].lower() == "open" or deal["status"].lower() == "filled" or deal["status"].lower() =="active" or deal['status'].lower()=='partiallyfilled':
                return deal
        return None  
    
    def getActiveDeals_ID(self, investor_account_id = None):
        activedealIDs=[]
        for deal in self.getActiveDeals(investor_account_id or self.investor_account_id):
            activedealIDs.append(deal['id'])
        return activedealIDs                    # a list of active deal id

    
    def CancelOrder(self, order_id, account_no=None):
        """Hủy lệnh"""
        if not self.trading_token:
            raise ValueError("Trading token not available. Please ensure tokens are loaded.")
            
        account = account_no or self.investor_account_id
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
            # log_trade_action(
            #     action="ORDER_CANCELLED",
            #     order_id=order_id,
            #     account=account
            # )
            
            # self.logger.info(f"Order cancelled successfully - ID: {order_id}")
            return result
            
        except Exception as e:
            # log_error_with_context(self.logger, e, "Failed to cancel order",
            #                      order_id=order_id, account=account)
            raise
    
    def CancleAllPendingOrders(self):
        '''
        Verified : Yes
        Purpose: Dùng đóng toàn độ các lệnh đang chờ trong sổ lệnh.
        '''
        #lấy toàn bộ pending order id vào list
        pendingOrders = self.GetPendingOrders(self.investor_account_id)    #list of pending deal objects
        for pendingOrder in pendingOrders:
            try:
                self.CancelOrder(pendingOrder['id'], self.investor_account_id)
                self.logger.info(f"Đã hủy lệnh chờ, id: {pendingOrder['id']}")
            except Exception as e:
                self.logger.error(f"Đã xảy lỗi: {e}")
    

    def GetPendingOrders(self, investor_account_id=None):
        """
        Lấy các lệnh đang chờ khớp lệnh trong sổ lệnh.
        """
        deals = self.GetOrders(investor_account_id or self.investor_account_id).get('orders')  #đọc tất cả lệnh trong sổ lệnh
        pendingOrders =[]
        for deal in deals:
            if deal['orderStatus'].lower() == 'pending' or deal['orderStatus'].lower() == 'pendingnew' or deal['orderStatus'].lower() == 'new'  :     
                pendingOrders.append(deal)

        return pendingOrders        


    def GetOrderDetail(self, order_id, account_no=None):
        """Lấy chi tiết lệnh"""
        account = account_no or self.investor_account_id
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
        account = account_no or self.investor_account_id
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

    def GetPP0(self, loan_package_id, account_no=None):
        """Lấy thông tin PP0 (cọc còn lại)"""
        account = account_no or self.account_no or "0001910385"
        if not account:
            raise ValueError("Account number is required")
            
        _headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }
        
        params = {
            "loanPackageId": loan_package_id,
            "accountNo": account
        }

        url = f"{self.base_url}derivative-core/ppse"
        response = get(url, headers=_headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def save_token_json(self):
        """
        Hàm dùng để lưu token và thời gian lấy token ra file json.
        """
        fileName ='token_dnse.json'
        # Lấy đường dẫn tuyệt đối của thư mục hiện tại
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, fileName)
        
        self.createdtimeToken = datetime.now().isoformat()  #example : 2025-09-28T20:48:15.123456


        data = {
            "token" : {"createdTime" : datetime.now().isoformat(),
                       "token" : self.token},      # thời gian, token
            "trading_token" : {"createdTime" : datetime.now().isoformat(),
                       "trading_token" : self.trading_token}   # thời gian, token
        }

        try:
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            self.logger.info(f"Đã lưu token vào {file_path}")
        except Exception as e:
            self.logger.info(f"Lỗi khi lưu token: {e}", "ERROR")
            pass

        

    def read_token_json(self):
        """
        Hàm dùng để đọc token và thời gian tạo token từ file json.
        """
        fileName ='token_dnse.json'
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, fileName)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if not all(key in data for key in ("token", "trading_token")):
                raise ValueError("Thiếu trường bắt buộc trong file JSON")
                
            self.logger.info(f"Đã đọc token từ {file_path}")
            
            self.createdtimeToken = data['token']['createdTime']  #example : 2025-09-28T20:48:15.123456

            return data
            
        except FileNotFoundError:
            self.logger.info(f"Không tìm thấy file {file_path}", "ERROR")
        except json.JSONDecodeError:
            self.logger.info(f"File {file_path} không đúng định dạng JSON", "ERROR")
        except Exception as e:
            self.logger.info(f"Lỗi khi đọc token: {str(e)}", "ERROR")
            
        return None

    def validate_token(self):
        try:
            tokens = self.read_token_json()
            token =tokens.get('token')['token']
            trading_token = tokens.get('trading_token')['trading_token']

            #kiểm tra thời gian hiệu lực của token
            # Chuyển đổi thời gian
            created_time = datetime.fromisoformat(tokens.get('token')["createdTime"])
            print(f"created time of token : {created_time}")
            current_time = datetime.now()
            time_diff = current_time - created_time

            if token and trading_token and time_diff < timedelta(hours = 7):
                self.logger.info(f"Đọc tokens từ file token_dnse.json.")
                self.token = tokens.get('token')['token']
                self.trading_token = tokens.get('trading_token')['trading_token']
                self.logger.info(f"Đọc xong tokens từ file token_dnse.json.")
                print(f"Đăng nhập thành công! [DNSE]")
            else:
                self.Authenticate(self.emailDNSE, self.passwordDNSE)
                self.GetOTP() #gửi mã OTP về email
                self.readSmartOTP(getOTP())
                self.GetTradingToken(self.OTP)
                self.logger.info(f"Đang lưu token ra file token_dnse.json...")
                self.save_token_json()
                self.logger.info(f"Đã lưu token ra file token_dnse.json.")

        except Exception as e:
            self.logger.info(f"[DNSE] Đang đăng nhập...")
            self.Authenticate(self.emailDNSE, self.passwordDNSE)
            self.GetOTP() #gửi mã OTP về email
            self.readSmartOTP(getOTP())
            self.GetTradingToken(self.OTP)
            self.logger.info(f"Đang lưu token ra file token_dnse.json...")
            self.save_token_json()
            self.logger.info(f"Đã lưu token ra file token_dnse.json.")
            pass
    
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
    
    def refresh_token(self):
        '''
        Dùng để đăng nhập lại, lấy lại token sau khi hết hạn
        '''    
        self.Authenticate(self.emailDNSE, self.passwordDNSE)
        self.GetOTP() #gửi mã OTP về email
        self.readSmartOTP(getOTP())
        self.GetTradingToken(self.OTP)
        self.logger.info(f"Đang lưu token ra file token_dnse.json...")
        self.save_token_json()
        self.logger.info(f"Đã lưu token ra file token_dnse.json.")
    
    def is_validated_token(self):
        '''
        Hàm để kiểm tra token còn giá trị hay ko, hết hạn hay chưa?
        '''
        try:
            current_time = datetime.now()
            print(self.createdtimeToken)
            created_time = datetime.fromisoformat(self.createdtimeToken)
            time_diff = current_time - created_time
            
            if time_diff > timedelta(hours= 7):
                # Add your token refresh logic here
                self.logger.warning("Token expired. Refreshing token...")
                self.refresh_token()
                self.logger.warning(f"Đã hoàn thành làm mới tokens.")
        
        except Exception as e:
            self.logger.error(f"Đã xảy ra lỗi khi refresh token : {e}")


        


