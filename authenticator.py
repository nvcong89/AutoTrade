import GLOBAL
from mqtt_client import MQTTClient
from dotenv import load_dotenv
from os import getenv


load_dotenv()
gmailEntrade = getenv("usernameEntrade") # Email/SĐT tài khoản Entrade
passwordEntrade = getenv("passwordEntrade") # Mật khẩu tài khoản Entrade

gmailDNSE = getenv("gmailDNSE") # Email đăng kí DNSE
passwordDNSE = getenv("passwordDNSE") # Mật khẩu tài khoản DNSE
appPasswordDNSE = getenv("appPasswordDNSE") # App Password cho email đăng kí DNSE




if __name__ == "__main__":
    
    # dùng test code khỏi cần lấy lại token
    # token ="eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpZGVudGlmaWNhdGlvbkNvZGUiOiIwMDEwODkwMjkyNDUiLCJzdWIiOiIxMDAwOTY0NzY4IiwiYnJva2VySWQiOiIwODY5IiwiYXV0aFNvdXJjZSI6bnVsbCwicm9sZXMiOlsiaW52ZXN0b3IiLCJCUk9LRVIiXSwiaXNzIjoiRE5TRSIsImludmVzdG9ySWQiOiIxMDAwOTY0NzY4IiwiYnJva2VyVHlwZSI6IlNBQ08iLCJmdWxsTmFtZSI6Ik5ndXnhu4VuIFbEg24gQ8O0bmciLCJzZXNzaW9uSWQiOiJjOTk3NjljMi05NjI2LTRiMzItYjQ0MC0zMjZjZDI5ODliODMiLCJ1c2VySWQiOiJhODQ3OGY2ZS0yMDY4LTRjODctYjEzNi1kNmFhMzIyYzk4MTYiLCJhdWQiOlsiYXVkaWVuY2UiXSwiY3VzdG9tZXJFbWFpbCI6Im52Y29uZzg5QGxpdmUuY29tIiwiY3VzdG9keUNvZGUiOiIwNjRDNjg0NjQxIiwiY3VzdG9tZXJJZCI6IjAwMDE1MDQxNzUiLCJleHAiOjE3NTg4Mzg2NTgsImN1c3RvbWVyTW9iaWxlIjoiMDk3OTQwNDY0MSIsImlhdCI6MTc1ODgwOTg1OCwidXNlcm5hbWUiOiIwNjRDNjg0NjQxIiwic3RhdHVzIjoiQUNUSVZFIn0.fJZKPv13ziRMbq3O__OmU_kfFh4bOR8d5oBjjhjY5XVS4eZBXO2PhMENNoNoP-h9dATvoDq4N-IxAeqDRsNpmiEl02TaaCmsDbSKwg8gT0CiYdLY0M2D9E6kYqNMRiDAsadtZTi7TQ4armsf61KJ_2eiAGh6QXWqS_Iv7rHezNQ"
   
    # Connect to Entrade (Only needed if used to auto trade)
    GLOBAL.ENTRADE_CLIENT.Authenticate(gmailEntrade, passwordEntrade)
    GLOBAL.ENTRADE_CLIENT.GetAccountInfo() # Get investor_id
    GLOBAL.ENTRADE_CLIENT.GetAccountBalance() # Get investor_account_id

    # Connect to DNSE
    GLOBAL.DNSE_CLIENT.Authenticate(gmailDNSE, passwordDNSE)

    if GLOBAL.DNSE_CLIENT.token is None:
        raise SystemError("Login to DNSE failed!")

    #đẩy traking token vào luôn để test code trong 8 tiếng


    if GLOBAL.tradingtoken_dnse is None:
        GLOBAL.DNSE_CLIENT.GetOTP() #gửi mã OTP về email
        GLOBAL.DNSE_CLIENT.readSmartOTP()
        GLOBAL.DNSE_CLIENT.GetTradingToken(GLOBAL.DNSE_CLIENT.OTP)

    else:
        GLOBAL.DNSE_CLIENT.trading_token = GLOBAL.tradingtoken_dnse

    print(f"Trading-Token [DNSE]: {GLOBAL.DNSE_CLIENT.trading_token}")

    investor_id = GLOBAL.DNSE_CLIENT.GetAccountInfo().get("investorId")
    token = GLOBAL.DNSE_CLIENT.token
    GLOBAL.DNSE_CLIENT.GetSubAccounts()
    # GLOBAL.DNSE_CLIENT.getLoanPackages()
    # print(GLOBAL.DNSE_CLIENT.loanpackages)

    print(f"\ninvestor_id [Etrade] : {GLOBAL.ENTRADE_CLIENT.investor_id}")
    print(f"investor_account_id [Etrade] : {GLOBAL.ENTRADE_CLIENT.investor_account_id} \n")
    
    print(f"investor_id [DNSE] : {investor_id}")
    print(f"investor_account_id [DNSE] : {GLOBAL.DNSE_CLIENT.investor_account_id}\n")
    # print(f"token : {token}")

    # Connect to MQTT server
    MQTT_CLIENT = MQTTClient(investor_id, token)
    MQTT_CLIENT.Connect()
    MQTT_CLIENT.Start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Disconnecting...")
        MQTT_CLIENT.client.disconnect()
        MQTT_CLIENT.client.loop_stop()
