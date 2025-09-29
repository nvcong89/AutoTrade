import logging
from logger_config import setup_logger
import logic_processor as lp
import GLOBAL
from requests import get
from time import time
from Utils import*
from tabulate import tabulate



def GetOHLCVData(type: str, symbol: str, from_time: int, to_time: int, resolution: str = '15') -> dict[str, list[float]]:
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


last_ts: int = 0

# ========== CẤU TRÚC DỮ LIỆU NÂNG CẤP ==========
TIME_FRAMES = {
    'm1': 60,
    'm3': 180,
    'm5': 300,
    'm15': 900,
    'm30': 1800,
    'H1': 3600,
    'D1': 86400,
    'W1': 604800
}

HISTORY = {tf: [] for tf in TIME_FRAMES} # Dictionary lưu data cho từng TF

current_bars = {tf: None for tf in TIME_FRAMES} # Bar đang hình thành của các TF

# ======== CẢI TIẾN HÀM INITIALIZE ========
def InitializeData():
    global HISTORY, current_bars, last_ts, logger
    logger = setup_logger("[Data Processor]", logging.INFO)

    # logger.info(f"Working TimeFrame: {GLOBAL.WORKING_TIMEFRAME}")

    base_tf = 'm1'
    last_ts = int(time())
    start_time = int(time()) - 86400*100  # 100 ngày dữ liệu
    
    # Lấy dữ liệu gốc 1 phút
    raw_data = GetOHLCVData("derivative", "VN30F1M", start_time, int(last_ts), '1')

    # Tạo dữ liệu base với timestamp
    base_data = list(zip(
        raw_data['t'],
        raw_data['o'], 
        raw_data['h'],
        raw_data['l'],
        raw_data['c'],
        raw_data['v']
    ))


    # Lưu dữ liệu và resample
    HISTORY[base_tf] = base_data
    for tf in [k for k in TIME_FRAMES if k != base_tf]:
        HISTORY[tf] = resample_data(base_data, tf)
    
    # Khởi tạo current bars
    for tf in TIME_FRAMES:
        if HISTORY[tf]:
            last_candle = HISTORY[tf][-1]
            current_bars[tf] = {
                'ts': last_candle[0] + TIME_FRAMES[tf],
                'O': last_candle[4],  # Close của candle trước
                'H': last_candle[4],
                'L': last_candle[4],
                'C': last_candle[4],
                'V': 0
            }
    
    GLOBAL.MARKETDATA = HISTORY
    logger.info("Successfully initialized multi-timeframe data:")
    for tf in TIME_FRAMES:
        logger.info(f"{tf}: {len(HISTORY[tf])} candles")
    print("-"*150)
    
    # lp.OnStart() # DO NOT REMOVE





# ========== HÀM UPDATE THEO THỜI GIAN THỰC ==========
def UpdateOHLCVData(new_data):
    global HISTORY, current_bars, last_ts

    # print(f"Current_bars: {current_bars}")
    # print(f"New tick data: {new_data}")
    new_ts = int(new_data['time'])
    price = float(new_data['close'])
    volume = int(new_data['volume'])
    last_ts = int(new_data['lastUpdated'])  # Cập nhật last_ts mới nhất

    GLOBAL.LAST_TICK_PRICE = price
    GLOBAL.LAST_TICK_VOLUME = volume

    # print_color(f"[Data_processor] Last_tick_Price : {price}","yellow")

    # Gọi logic xử lý cho OnTick()
    lp.OnTick()

    # Cập nhật dữ liệu cho các timeframe
    # print(f"New tick ts: {new_ts}, current m1 bar ts: {current_bars['m1']['ts']}")
    if new_ts >= current_bars['m1']['ts']:
        for tf in TIME_FRAMES:
            tf_interval = TIME_FRAMES[tf]
            current_bar = current_bars[tf]

            # Kiểm tra sang candle mới
            if new_ts >= current_bar['ts']:
                # Lưu candle cũ
                HISTORY[tf].append((
                    current_bar['ts'] - tf_interval,
                    current_bar['O'],
                    current_bar['H'],
                    current_bar['L'],
                    current_bar['C'],
                    current_bar['V']
                ))

                # Tạo candle mới
                current_bars[tf] = {
                    'ts': current_bar['ts'] + tf_interval,
                    'O': price,
                    'H': price,
                    'L': price,
                    'C': price,
                    'V': volume
                }
            else:
                # Update candle hiện tại
                current_bars[tf]['H'] = max(current_bars[tf]['H'], price)
                current_bars[tf]['L'] = min(current_bars[tf]['L'], price)
                current_bars[tf]['C'] = price
                current_bars[tf]['V'] += volume
    

        #thực thi code nằm trong OnBarClosed()
        #print(f"working timeframe: {GLOBAL.WORKING_TIMEFRAME}")
        #print(f"current bar ts: {current_bars[GLOBAL.WORKING_TIMEFRAME]['ts']}, new tick ts: {new_ts}")
        
        # Lấy dữ liệu mới nhất cho GLOBAL.MARKETDATA
        GLOBAL.MARKETDATA = HISTORY

        if GLOBAL.WORKING_TIMEFRAME =='m1':
            lp.OnBarClosed()
        else:
            if new_ts >= current_bars[GLOBAL.WORKING_TIMEFRAME]['ts']:
                # cprint(f"new_ts >= current_bars[GLOBAL.WORKING_TIMEFRAME]['ts'], Running OnBarClosed()")
                lp.OnBarClosed()
    
    


def UpdateMarketData(new_market_data):
    try:
        if new_market_data:
            GLOBAL.TOTAL_BID = int(new_market_data["totalBidQtty"])
            GLOBAL.TOTAL_OFFER = int(new_market_data["totalOfferQtty"])
            

        GLOBAL.BID_DEPTH.clear()
        for dict in new_market_data["bid"]:
            GLOBAL.BID_DEPTH.append(tuple(dict.values()))
        
        # print_color(f"[Data_processor] Las_bid_Price : {GLOBAL.BID_DEPTH[0][0]}","yellow")

        GLOBAL.ASK_DEPTH.clear()
        for dict in new_market_data["offer"]:
            GLOBAL.ASK_DEPTH.append(tuple(dict.values()))

        # print_color(f"[Data_processor] Last_ask_Price : {GLOBAL.ASK_DEPTH[0][0]}","yellow")
        # print_color(f"[Data_processor] Spread : {GLOBAL.ASK_DEPTH[0][0]-GLOBAL.BID_DEPTH[0][0]}")

    except Exception as e:
        logger.error(f"[Data_processor] UpdateMarketData Đã xảy ra lỗi: {e}")
        pass

def UpdateForeignData(new_foreign_data):
    GLOBAL.TOTAL_FOREIGN_BUY = int(new_foreign_data["buyForeignQuantity"])
    GLOBAL.TOTAL_FOREIGN_SELL = int(new_foreign_data["sellForeignQuantity"])


# ========== HÀM RESAMPLE THÔNG MINH ==========
def resample_data(data, target_tf):
    interval = TIME_FRAMES[target_tf]
    resampled = []
    current_group = []
    
    for candle in data:
        ts = candle[0]
        if not current_group:
            current_group.append(candle)
            continue
            
        if ts < (current_group[0][0] // interval) * interval + interval:
            current_group.append(candle)
        else:
            new_candle = (
                (current_group[0][0] // interval) * interval,
                current_group[0][1],
                max(c[2] for c in current_group),
                min(c[3] for c in current_group),
                current_group[-1][4],
                sum(c[5] for c in current_group)
            )
            resampled.append(new_candle)
            current_group = [candle]
    
    return resampled


def get_interval_seconds(tf):
    return {
        'm1': 60,
        'm3': 180,
        'm5': 300,
        'm15': 900,
        'm30': 1800,
        'H1': 3600,
        'D1': 86400,
        'W1': 604800
    }[tf]