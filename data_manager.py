import numpy as np
import pytz
from collections import deque
from datetime import datetime

class DataManager:
    def __init__(self):
        self.TIME_FRAMES = {
            'm1': 60,
            'm5': 300,
            'H1': 3600,
            'D1': 86400
        }
        self.MAX_HISTORY = {
            'm1': 10080,  # 1 tuần
            'm5': 2016,
            'H1': 168,
            'D1': 90
        }
        self.history = {tf: deque(maxlen=size) for tf, size in self.MAX_HISTORY.items()}
        self.current_bars = {tf: None for tf in self.TIME_FRAMES}
        self.tz = pytz.timezone('Asia/Ho_Chi_Minh')
        
    def convert_timestamp(self, ts):
        return datetime.fromtimestamp(ts, self.tz).strftime('%d/%m/%Y %H:%M:%S')
    
    def resample_data(self, base_data, target_tf):
        interval = self.TIME_FRAMES[target_tf]
        resampled = []
        current_group = []
        last_ts = 0
        
        for candle in base_data:
            ts = candle[0]
            if ts - last_ts > interval * 1.5:  # Phát hiện missing data
                self.log_data_gap(target_tf, last_ts, ts)
            
            if not current_group:
                current_group.append(candle)
                last_ts = ts
                continue
                
            if (ts // interval) != (current_group[0][0] // interval):
                new_candle = self.create_new_candle(current_group, target_tf)
                resampled.append(new_candle)
                current_group = [candle]
                last_ts = ts
            else:
                current_group.append(candle)
                
        return np.array(resampled, dtype=[
            ('ts', 'i8'), ('open', 'f4'), 
            ('high', 'f4'), ('low', 'f4'), 
            ('close', 'f4'), ('volume', 'i8')
        ])
    
    def create_new_candle(self, group, tf):
        open_price = group[0][1]
        high = max(c[2] for c in group)
        low = min(c[3] for c in group)
        close = group[-1][4]
        volume = sum(c[5] for c in group)
        ts = (group[0][0] // self.TIME_FRAMES[tf]) * self.TIME_FRAMES[tf]
        return (ts, open_price, high, low, close, volume)
    
    def validate_candles(self, tf):
        data = self.history[tf]
        for i in range(1, len(data)):
            prev_ts = data[i-1][0]
            curr_ts = data[i][0]
            if (curr_ts - prev_ts) != self.TIME_FRAMES[tf]:
                raise ValueError(f"Invalid candle sequence in {tf} between {self.convert_timestamp(prev_ts)} and {self.convert_timestamp(curr_ts)}")
    
    def log_data_gap(self, tf, prev_ts, curr_ts):
        gap_duration = curr_ts - prev_ts
        print(f"[{tf}] Data gap detected: {self.convert_timestamp(prev_ts)} -> {self.convert_timestamp(curr_ts)} | Duration: {gap_duration//60} minutes")