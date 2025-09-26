from requests import get, post, delete
from time import localtime
from pymongo import MongoClient
from datetime import datetime, timezone
import os
from logger_config import setup_logger, get_trading_logger, log_trade_action, log_error_with_context

class DNSEClient:
    def __init__(self, mongo_uri=None, db_name="algo"):
        self.token = None
        self.trading_token = None
        self.account_no = None
        self.investor_id = None
        self.base_url = "https://api.dnse.com.vn/"
        
        # Setup logger
        self.logger = setup_logger("DNSE_Client")
        self.trading_logger = get_trading_logger()
        
        # MongoDB connection
        self.mongo_uri = mongo_uri or os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self.db_name = db_name
        
        try:
            self.client = MongoClient(self.mongo_uri)
            self.db = self.client[self.db_name]
            self.tokens_collection = self.db["dnse_tokens"]
            self.logger.info(f"Connected to MongoDB: {self.mongo_uri}/{self.db_name}")
        except Exception as e:
            log_error_with_context(self.logger, e, "MongoDB connection failed", 
                                 mongo_uri=self.mongo_uri, db_name=self.db_name)
            raise
        
        # Load tokens from MongoDB on initialization
        self._load_tokens_from_db()

    def _load_tokens_from_db(self):
        """Load tokens from MongoDB collection"""
        try:
            # Get the latest token document
            token_doc = self.tokens_collection.find_one(sort=[("expiry", -1)])
            
            if token_doc:
                # Check if token is still valid
                if self._is_token_valid(token_doc):
                    self.token = token_doc.get("jwt_token")
                    self.trading_token = token_doc.get("trading_token")
                    expiry = token_doc.get("expiry")
                    self.logger.info(f"Loaded valid tokens from MongoDB - Expiry: {expiry}")
                    
                    # Load account info using the token
                    self._load_account_info()
                else:
                    expiry = token_doc.get("expiry")
                    self.logger.warning(f"Token in MongoDB has expired - Expiry: {expiry}")
            else:
                self.logger.warning("No token found in MongoDB collection 'dnse_tokens'")
                
        except Exception as e:
            log_error_with_context(self.logger, e, "Failed to load tokens from MongoDB")

    def _is_token_valid(self, token_doc):
        """Check if token is still valid"""
        expiry = token_doc.get("expiry")
        if expiry:
            # Convert to datetime if it's a string or ensure it's timezone aware
            if isinstance(expiry, str):
                expiry = datetime.fromisoformat(expiry.replace('Z', '+00:00'))
            elif expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)
            
            now = datetime.now(timezone.utc)
            return expiry > now
        return False

    def _load_account_info(self):
        """Load account info using current token"""
        if not self.token:
            self.logger.warning("No JWT token available to load account info")
            return
            
        try:
            _headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.token}"
            }

            url = f"{self.base_url}user-service/api/me"
            response = get(url, headers=_headers)
            response.raise_for_status()
            account_info = response.json()
            
            # Store account info for later use
            self.investor_id = account_info.get("investorId")
            # Get first account if multiple accounts exist
            accounts = account_info.get("accounts", [])
            if accounts:
                self.account_no = accounts[0].get("accountNo")
                
            self.logger.info(f"Loaded account info - Investor ID: {self.investor_id}, Account: {self.account_no}")
            
        except Exception as e:
            log_error_with_context(self.logger, e, "Failed to load account info")

    def refresh_tokens(self):
        """Manually refresh tokens from MongoDB"""
        self._load_tokens_from_db()

    def get_token_status(self):
        """Get current token status"""
        return {
            "has_jwt_token": bool(self.token),
            "has_trading_token": bool(self.trading_token),
            "investor_id": self.investor_id,
            "account_no": self.account_no
        }

    def GetAccountInfo(self):
        """Lấy thông tin tài khoản (backward compatibility)"""
        if not self.token:
            raise ValueError("JWT token not available. Please ensure tokens are loaded from MongoDB.")
            
        _headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }

        url = f"{self.base_url}user-service/api/me"
        response = get(url, headers=_headers)
        response.raise_for_status()
        account_info = response.json()
        
        # Store account info for later use
        self.investor_id = account_info.get("investorId")
        # Get first account if multiple accounts exist
        accounts = account_info.get("accounts", [])
        if accounts:
            self.account_no = accounts[0].get("accountNo")
        
        return account_info

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

    def Order(self, symbol, side, price, quantity, loan_package_id, order_type="LO", account_no=None):
        """Đặt lệnh phái sinh"""
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
        
        _json = {
            "symbol": symbol,
            "side": side,
            "orderType": order_type,
            "price": price,
            "quantity": quantity,
            "loanPackageId": loan_package_id,
            "accountNo": account
        }

        try:
            url = f"{self.base_url}order-service/derivative/orders"
            self.logger.info(f"Placing order: {symbol} {side} {quantity}@{price} ({order_type})")
            
            response = post(url, headers=_headers, json=_json)
            response.raise_for_status()
            result = response.json()
            
            order_id = result.get("id")
            
            # Log trading action
            log_trade_action(
                action="ORDER_PLACED",
                symbol=symbol,
                side=side,
                price=price,
                quantity=quantity,
                order_type=order_type,
                order_id=order_id,
                account=account,
                loan_package_id=loan_package_id
            )
            
            self.logger.info(f"Order placed successfully - ID: {order_id}")
            return result
            
        except Exception as e:
            log_error_with_context(self.logger, e, "Failed to place order",
                                 symbol=symbol, side=side, price=price, quantity=quantity)
            raise

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

    # Conditional Order methods (for advanced trading)
    def CreateConditionalOrder(self, symbol, account, side, price, loan, volume, order_type, condition):
        """Đặt lệnh điều kiện"""
        if not self.trading_token:
            raise ValueError("Trading token not available. Please ensure tokens are loaded from MongoDB.")
            
        url = f"{self.base_url}conditional-order-api/v1/orders"

        # Default to derivative
        loan_package_id = loan or 2278
        market_id = "DERIVATIVES"

        if len(symbol) < 4:  # It's normal stock
            loan_package_id = loan or 1372
            market_id = "UNDERLYING"

        _headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
            "Trading-Token": self.trading_token
        }

        current_time = localtime()
        _json = {
            "condition": condition,
            "targetOrder": {
                "quantity": volume, 
                "side": side, 
                "price": price, 
                "loanPackageId": loan_package_id, 
                "orderType": order_type
            },
            "symbol": symbol,
            "props": {"stopPrice": int(condition[9:]), "marketId": market_id},
            "accountNo": account,
            "category": "STOP",
            "timeInForce": {
                "expireTime": f"{current_time.tm_year}-{current_time.tm_mon:02d}-{current_time.tm_mday:02d}T07:30:00.000Z", 
                "kind": "GTD"
            }
        }
        response = post(url, headers=_headers, json=_json)
        response.raise_for_status()
        print("Gửi yêu cầu đặt lệnh điều kiện thành công! (DNSE)")
        return response.json()

    def close_connection(self):
        """Close MongoDB connection"""
        if hasattr(self, 'client'):
            self.client.close()
            print("Đã đóng kết nối MongoDB!")

    def __del__(self):
        """Destructor to close MongoDB connection"""
        try:
            self.close_connection()
        except:
            pass
