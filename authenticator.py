import GLOBAL
from logger_config import setup_logger
import logging
from mqtt_client import MQTTClient
from dotenv import load_dotenv
from os import getenv
from mail_reader import getOTP
from Utils import*


load_dotenv()
gmailEntrade = getenv("usernameEntrade") # Email/SĐT tài khoản Entrade
passwordEntrade = getenv("passwordEntrade") # Mật khẩu tài khoản Entrade

gmailDNSE = getenv("gmailDNSE") # Email đăng kí DNSE
passwordDNSE = getenv("passwordDNSE") # Mật khẩu tài khoản DNSE
appPasswordDNSE = getenv("appPasswordDNSE") # App Password cho email đăng kí DNSE



if __name__ == "__main__":
    
    global logger
    logger = setup_logger("[Authenticaotor]", logging.INFO)    # khởi tạo logger để in ra file log, console

    # Connect to Entrade (Only needed if used to auto trade)
    GLOBAL.ENTRADE_CLIENT.Authenticate(gmailEntrade, passwordEntrade)
    GLOBAL.ENTRADE_CLIENT.GetAccountInfo() # Get investor_id
    GLOBAL.ENTRADE_CLIENT.GetAccountBalance() # Get investor_account_id

    # Connect to DNSE
    GLOBAL.DNSE_CLIENT.gmailDNSE = gmailDNSE
    GLOBAL.DNSE_CLIENT.passwordDNSE = passwordDNSE
    GLOBAL.DNSE_CLIENT.validate_token()


    if GLOBAL.DNSE_CLIENT.token is None:
        raise SystemError("Login to DNSE failed!")

    token = GLOBAL.DNSE_CLIENT.token

    logger.info(f"token [DNSE] : {token}")
    logger.info(f"Trading-Token [DNSE]: {GLOBAL.DNSE_CLIENT.trading_token}")

    investor_id = GLOBAL.DNSE_CLIENT.GetAccountInfo().get("investorId")

    # print(GLOBAL.DNSE_CLIENT.GetAccountInfo())

    GLOBAL.DNSE_CLIENT.GetSubAccounts()
    investor_account_id = GLOBAL.DNSE_CLIENT.investor_account_id
    # đẩy loadpackageID vào trong DNSE_Client
    GLOBAL.DNSE_CLIENT.loanpackageID = GLOBAL.DNSE_CLIENT.GetDerivativeLoanPackages(GLOBAL.DNSE_CLIENT.investor_account_id).get('loanPackages')[0]['id']


    logger.info(f"investor_id [Etrade] : {GLOBAL.ENTRADE_CLIENT.investor_id}")
    logger.info(f"investor_account_id [Etrade] : {GLOBAL.ENTRADE_CLIENT.investor_account_id} \n")
    
    logger.info(f"investor_id [DNSE] : {investor_id}")
    logger.info(f"investor_account_id [DNSE] : {GLOBAL.DNSE_CLIENT.investor_account_id}\n")
    

    logger.info(f"loan package id: {GLOBAL.DNSE_CLIENT.loanpackageID}")

    logger.info(f"Tổng số lượng lệnh trong sổ: {len(GLOBAL.DNSE_CLIENT.GetOrders(investor_account_id).get('orders'))}")

    # print(f"sổ lệnh: {GLOBAL.DNSE_CLIENT.GetOrders(investor_account_id)}")

    totaVol = GLOBAL.DNSE_CLIENT.GetTotalOpenQuantity()
    logger.info(f"Tổng số hợp đồng đang mở: {totaVol} HĐ")

    # print(f"active deals: {GLOBAL.DNSE_CLIENT.getActiveDeals(GLOBAL.DNSE_CLIENT.investor_account_id)}")


    # Connect to MQTT server
    MQTT_CLIENT = MQTTClient(investor_id, token)
    MQTT_CLIENT.Connect()
    MQTT_CLIENT.Start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        logger.info("Disconnecting...")
        MQTT_CLIENT.client.disconnect()
        MQTT_CLIENT.client.loop_stop()
