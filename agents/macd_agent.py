import numpy as np
from datetime import datetime
from agent import Agent

class MACDIndicator(Agent):
    def __init__(self,
                 fast_period: int = 12,
                 slow_period: int = 26,
                 signal_period: int = 9,
                 feature_idx: int = 3,
                 name: str = "BotMACD"):
        super().__init__(name)
        if fast_period >= slow_period:
            raise ValueError("fast_period must be < slow_period")
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.feature_idx = feature_idx
        # self.deal_pos = 0  # Initialize position

    def _ema(self, data, period):
        alpha = 2 / (period + 1)
        ema = np.empty_like(data)
        ema[:] = np.nan
        if len(data) < period:
            return ema
        ema[period-1] = np.mean(data[:period])
        for i in range(period, len(data)):
            ema[i] = alpha * data[i] + (1 - alpha) * ema[i-1]
        return ema

    def compute(self, data):
        # Extract price series
        if data.ndim == 2:
            prices = data[:, self.feature_idx]
        else:
            prices = data

        ema_fast = self._ema(prices, self.fast_period)
        ema_slow = self._ema(prices, self.slow_period)
        macd = ema_fast - ema_slow
        signal = self._ema(macd, self.signal_period)
        return {"macd": macd, "signal": signal}

    def Calculate(self, data):
        np_data = np.asarray(data, dtype=np.float32)

        # Prepare price series
        if np_data.ndim == 2:
            if not (-np_data.shape[1] <= self.feature_idx < np_data.shape[1]):
                return None
            prices = np_data[:, self.feature_idx]
        elif np_data.ndim == 1:
            prices = np_data
        else:
            return None

        min_needed = self.slow_period + self.signal_period  # heuristic
        if prices.size < min_needed:
            return None

        result = self.compute(np_data)
        macd = result["macd"]
        signal = result["signal"]

        # Find last two indices where both macd and signal are valid
        valid_idx = np.where(~np.isnan(macd) & ~np.isnan(signal))[0]
        if valid_idx.size < 2:
            return None

        i_prev, i_last = valid_idx[-2], valid_idx[-1]
        macd_prev, sig_prev = macd[i_prev], signal[i_prev]
        macd_last, sig_last = macd[i_last], signal[i_last]

        print(f"{self.name} macd_prev =  {macd_prev:.1f} ({datetime.now().strftime("%H:%M %d/%m")})")
        print(f"{self.name} macd_last =  {macd_last:.1f} ({datetime.now().strftime("%H:%M %d/%m")})")
        print(f"{self.name} sig_prev =  {sig_prev:.1f} ({datetime.now().strftime("%H:%M %d/%m")})")
        print(f"{self.name} sig_last =  {sig_last:.1f} ({datetime.now().strftime("%H:%M %d/%m")})")

        # Bullish crossover
        if macd_prev <= sig_prev and macd_last > sig_last and self.deal_pos < 1:
            self.deal_pos = 1
            return True

        # Bearish crossover
        if macd_prev >= sig_prev and macd_last < sig_last and self.deal_pos > -1:
            self.deal_pos = -1
            return False

        return None

macd_agent = MACDIndicator(fast_period= 12, slow_period=26, signal_period=9)
