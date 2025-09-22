import numpy as np
from typing import Dict

class LogicProcessor:
    def __init__(self, data_manager):
        self.dm = data_manager
        self.indicators = {
            tf: {
                'ma20': np.zeros(0),
                'ma50': np.zeros(0),
                'rsi': np.zeros(0)
            } for tf in self.dm.TIME_FRAMES
        }
        
    def update_indicators(self, tf):
        closes = np.array([c['close'] for c in self.dm.history[tf]], dtype=np.float32)
        if len(closes) >= 50:
            self.indicators[tf]['ma20'] = np.convolve(closes, np.ones(20)/20, mode='valid')
            self.indicators[tf]['ma50'] = np.convolve(closes, np.ones(50)/50, mode='valid')
            self.indicators[tf]['rsi'] = self.calculate_rsi(closes)
        
    def calculate_rsi(self, closes, period=14):
        deltas = np.diff(closes)
        gain = np.where(deltas > 0, deltas, 0)
        loss = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.convolve(gain, np.ones(period)/period, mode='valid')
        avg_loss = np.convolve(loss, np.ones(period)/period, mode='valid')
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def check_multiframe_signal(self):
        signals = []
        # Ví dụ: H1 uptrend + m5 pullback
        h1_condition = self.check_trend('H1')
        m5_condition = self.check_pullback('m5')
        
        if h1_condition == 'uptrend' and m5_condition == 'pullback':
            signals.append({
                'type': 'BUY',
                'strength': self.calculate_signal_strength(),
                'timeframes': ['H1', 'm5']
            })
        return signals
    
    def check_trend(self, tf):
        ma20 = self.indicators[tf]['ma20']
        ma50 = self.indicators[tf]['ma50']
        if len(ma20) < 2 or len(ma50) < 2:
            return 'neutral'
        return 'uptrend' if ma20[-1] > ma50[-1] else 'downtrend'
    
    def check_pullback(self, tf):
        # Logic phát hiện pullback
        pass
    
    def calculate_signal_strength(self):
        # Tính toán độ mạnh tín hiệu
        return 0.8
    
    def on_bar_closed(self, tf):
        self.update_indicators(tf)
        self.validate_signals(tf)
        
    def validate_signals(self, tf):
        # Kiểm tra tính hợp lệ của tín hiệu
        pass