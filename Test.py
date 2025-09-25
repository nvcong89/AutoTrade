import time
from requests import get, post
from time import localtime


base_url = "https://api.dnse.com.vn/"

def Authenticate(username, password):
        _headers = {
            "Content-Type": "application/json"
        }
        _json = {
            "username": username,
            "password": password
        }

        url = f"{base_url}auth-service/login"
        response = post(url, json=_json, headers=_headers)
        response.raise_for_status()
        print("Đăng nhập thành công! (DNSE)")
        return response.json().get("token")
        

def getAccountNo(token):
        """Lấy danh sách tài khoản"""
        _headers = {
            "Authorization": f"Bearer {token}"
        }

        url = f"{base_url}user-service/api/me"
        response = get(url, headers=_headers)
        response.raise_for_status()
        return response.json()

def Gettieukhoan(token):
        """Lấy danh sách tiểu khoản"""
        _headers = {
            "Authorization": f"Bearer {token}"
        }

        url = f"{base_url}order-service/accounts"
        response = get(url, headers=_headers)
        response.raise_for_status()
        return response.json()

def GetDeals(token, account_no=None):
        """Lấy danh sách deal nắm giữ"""
        account = account_no
        if not account:
            raise ValueError("Account number is required")
            
        _headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        params = {"accountNo": account}

        url = f"{base_url}order-service/derivative/orders"
        response = get(url, headers=_headers, params=params)
        response.raise_for_status()
        return response.json()


if __name__ == "__main__":
    from tabulate import tabulate

    usernameEntrade="nvcong89@live.com"
    passwordEntrade="Th@nhcong89"

    # token = Authenticate(usernameEntrade, passwordEntrade)
    # print(f"Token: {token}")
    token ="eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpZGVudGlmaWNhdGlvbkNvZGUiOiIwMDEwODkwMjkyNDUiLCJzdWIiOiIxMDAwOTY0NzY4IiwiYnJva2VySWQiOiIwODY5IiwiYXV0aFNvdXJjZSI6bnVsbCwicm9sZXMiOlsiaW52ZXN0b3IiLCJCUk9LRVIiXSwiaXNzIjoiRE5TRSIsImludmVzdG9ySWQiOiIxMDAwOTY0NzY4IiwiYnJva2VyVHlwZSI6IlNBQ08iLCJmdWxsTmFtZSI6Ik5ndXnhu4VuIFbEg24gQ8O0bmciLCJzZXNzaW9uSWQiOiJjOTk3NjljMi05NjI2LTRiMzItYjQ0MC0zMjZjZDI5ODliODMiLCJ1c2VySWQiOiJhODQ3OGY2ZS0yMDY4LTRjODctYjEzNi1kNmFhMzIyYzk4MTYiLCJhdWQiOlsiYXVkaWVuY2UiXSwiY3VzdG9tZXJFbWFpbCI6Im52Y29uZzg5QGxpdmUuY29tIiwiY3VzdG9keUNvZGUiOiIwNjRDNjg0NjQxIiwiY3VzdG9tZXJJZCI6IjAwMDE1MDQxNzUiLCJleHAiOjE3NTg4Mzg2NTgsImN1c3RvbWVyTW9iaWxlIjoiMDk3OTQwNDY0MSIsImlhdCI6MTc1ODgwOTg1OCwidXNlcm5hbWUiOiIwNjRDNjg0NjQxIiwic3RhdHVzIjoiQUNUSVZFIn0.fJZKPv13ziRMbq3O__OmU_kfFh4bOR8d5oBjjhjY5XVS4eZBXO2PhMENNoNoP-h9dATvoDq4N-IxAeqDRsNpmiEl02TaaCmsDbSKwg8gT0CiYdLY0M2D9E6kYqNMRiDAsadtZTi7TQ4armsf61KJ_2eiAGh6QXWqS_Iv7rHezNQ"
   
    accountNo = getAccountNo(token)
    # print(f"Account No: {accountNo}")
    tieukhoan = Gettieukhoan(token)
    # print(tieukhoan)

    print(tieukhoan['default']['id'])

           

    deals = GetDeals(token, "0001521007")
    # print(deals)


