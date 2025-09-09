import ssl
import json
import paho.mqtt.client as mqtt
from random import randint
import data_processor as dp

# Configuration
BROKER_HOST = "datafeed-lts-krx.dnse.com.vn"
BROKER_PORT = 443
CLIENT_ID_PREFIX = "dnse-price-json-mqtt-ws-sub-"
# Generate random client ID
client_id = f"{CLIENT_ID_PREFIX}{randint(1000, 2000)}"

# Connect callback (Subscribe to topics and initialize dp.HISTORY here)
def on_connect(client, userdata, flags, rc, properties):
    '''MQTTv5 connection callback'''
    if rc == 0 and client.is_connected():
        print("Connected to MQTT Broker!")
        # Modify topics as needed
        client.subscribe("plaintext/quotes/krx/mdds/v2/ohlc/derivative/1/VN30F1M", qos=1)
        dp.InitializeData() # DO NOT REMOVE
    else:
        print(f"on_connect(): Failed to connect, return code {rc}\n")

# Message callback (MUST call Update() inside)
# def on_message(client, userdata, msg):
#     payload = json.JSONDecoder().decode(msg.payload.decode())

#     # DO NOT REMOVE
#     Update(payload) # Send data to data_processor for each message

class MQTTClient:
    def __init__(self, investor_id, token):
        self.investor_id = investor_id
        self.token = token
        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id,
            protocol=mqtt.MQTTv5,
            transport="websockets"
        )

        self.client.username_pw_set(investor_id, token)
        # SSL/TLS configuration (since it's wss://)
        self.client.ws_set_options(path="/wss")
        self.client.tls_set(cert_reqs=ssl.CERT_NONE) # Bỏ qua kiểm tra SSL
        self.client.tls_insecure_set(True) # Cho phép kết nối với chứng chỉ self-signed
        self.client.enable_logger()

        self.client.on_connect = on_connect
        self.client.on_message = lambda c, u, m: dp.UpdateData(json.JSONDecoder().decode(m.payload.decode())) # or 'on_message'

    def Connect(self):
        self.client.connect(BROKER_HOST, BROKER_PORT, keepalive=1200)

    def Start(self):
        self.client.loop_start()