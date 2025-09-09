import logic_processor as lp
from requests import get
from time import time

HISTORY = []
last_O = None
last_H = None
last_L = None
last_C = None
last_V = None
last_T = None

def GetOHLCVData(type : str, symbol : str, from_time : int, to_time : int, resolution : str = '15') -> dict[str, list[float]]:
    '''
    **type**: "derivative", "stock" hoặc "index"\n
    **symbol**: mã cổ phiếu/phái sinh/thị trường tương ứng với 'type'\n
    **from_time/to_time**: thời điểm bắt đầu/kết thúc lấy dữ liệu (Unix epoch time)\n
    **resolution**: 1, 3, 5, 15, 30, 1H, 1D, 1W (nến 1/3/5/... phút)
    '''

    url = f"https://api.dnse.com.vn/chart-api/v2/ohlcs/{type}?from={from_time}&to={to_time}&symbol={symbol}&resolution={resolution}"

    response = get(url)
    response.raise_for_status()
    return response.json()

def InitializeData():
    global HISTORY

    now = int(time())
    past = now - 72_000 # 20 hours prior to now, ensure that we definitely get at least 89 candles (1 minute resolution!) :3

    json_data = GetOHLCVData("derivative", "VN30F1M", past, now, '1')
    HISTORY = list(zip(
        json_data['o'],
        json_data['h'],
        json_data['l'],
        json_data['c'],
        json_data['v']
    ))

    print("Successfully initialized data:\n...")
    print(HISTORY[-10:])
    print("==================================================")

def UpdateData(new_data):
    global HISTORY, last_O, last_H, last_L, last_C, last_V, last_T

    O = new_data.get("open")
    H = new_data.get("high")
    L = new_data.get("low")
    C = new_data.get("close")
    V = int(new_data.get("volume"))
    T = int(new_data.get("time"))

    if last_T is None or last_T == T:
        last_O = O
        last_H = H
        last_L = L
        last_C = C
        last_V = V
        last_T = T

    elif last_T < T: # The candle have just finished, use last data of it as the final result
        last_T = T
        HISTORY.append([last_O, last_H, last_L, last_C, last_V])
        lp.CalculateStrategy(HISTORY)
