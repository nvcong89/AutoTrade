import datetime
from datetime import datetime
import json
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
from requests import post, get
from random import randint
import os, ssl

# Nếu có InvestorID và Token rồi thì có thể comment đoạn này vào
username = "nvcong89@live.com"  # custodyCode
password = "Th@nhcong89"  # Mật khẩu đăng nhập tài khoản

# Nhập thông tin vào đây (nếu có), và comment đoạn try...except bên dưới
investor_id = None
token = None


def cprint(message):
    '''
    Hàm hỗ trợ in ra console có bao gồm ngày tháng và giờ.
    '''
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] - {message}")

def authenticate(username, password):
    try:
        url = "https://api.dnse.com.vn/auth-service/login"
        _json = {
            "username": username,
            "password": password
        }
        response = post(url, json=_json)
        response.raise_for_status()

        print("Authentication successful!")
        return response.json().get("token")

    except Exception as e:
        print(f"Authentication failed: {e}")
        return None


def get_investor_info(token=None):
    try:
        url = f"https://api.dnse.com.vn/user-service/api/me"
        headers = {
            "authorization": f"Bearer {token}"
        }

        response = get(url, headers=headers)
        response.raise_for_status()
        investor_info = response.json()
        print("Get investor info successful!")
        return investor_info

    except Exception as e:
        print(f"Failed to get investor info: {e}")
        return None


try:  # Có thể comment nếu có thông tin
    token = authenticate(username, password)
    if token is not None:
        investor_info = get_investor_info(token=token)
        if investor_info is not None:
            investor_id = str(investor_info["investorId"])
        else:
            raise Exception("Failed to get investor info.")
    else:
        raise Exception("Authentication failed.")

except Exception as e:
    print(f"Error: {e}")
    exit()

print(investor_id)
print(token)

# Configuration
BROKER_HOST = "datafeed-lts-krx.dnse.com.vn"
BROKER_PORT = 443
CLIENT_ID_PREFIX = "dnse-price-json-mqtt-ws-sub-"

# Generate random client ID
client_id = f"{CLIENT_ID_PREFIX}{randint(1000, 2000)}"

# Create client
client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2,
    client_id,
    protocol=mqtt.MQTTv5,
    transport="websockets"
)

# Set credentials
client.username_pw_set(investor_id, token)

# SSL/TLS configuration (since it's wss://)
client.tls_set(cert_reqs=ssl.CERT_NONE)  # Bỏ qua kiểm tra SSL
client.tls_insecure_set(True)  # Cho phép kết nối với chứng chỉ self-signed
client.ws_set_options(path="/wss")
client.enable_logger()


# Connect callback
def on_connect(client, userdata, flags, rc, properties):
    """MQTTv5 connection callback"""
    if rc == 0 and client.is_connected():
        print("Connected to MQTT Broker!")
        # Example subscription - modify as needed

        # client.subscribe("plaintext/quotes/krx/mdds/tick/v1/roundlot/symbol/ACB", qos=1)
        # client.subscribe("plaintext/quotes/krx/mdds/topprice/v1/roundlot/symbol/ACB", qos=1)
        # client.subscribe("plaintext/quotes/krx/mdds/stockinfo/v1/roundlot/symbol/ACB", qos=1)
        # client.subscribe("plaintext/quotes/krx/mdds/v2/ohlc/stock/1H/ACB", qos=1)

        client.subscribe("plaintext/quotes/krx/mdds/tick/v1/roundlot/symbol/41I1FA000", qos=1)

        
    else:
        print(f"on_connect(): Failed to connect, return code {rc}\n")


# Message callback
def on_message(client, userdata, msg):
    payload = json.JSONDecoder().decode(msg.payload.decode())
    # print(f"[RAW] Topic: {msg.topic} | Payload: {msg.payload.decode()}")
    cprint(f"tick price : {payload['matchPrice']}")

# Assign callback
client.on_connect = on_connect
client.on_message = on_message

# Connect to broker
client.connect(BROKER_HOST, BROKER_PORT, keepalive=1200)

# Start the network loop
client.loop_start()

# To keep the connection alive (or use loop_forever() instead of loop_start())
try:
    while True:
        pass
except KeyboardInterrupt:
    print("Disconnecting...")
    client.disconnect()
    client.loop_stop()
