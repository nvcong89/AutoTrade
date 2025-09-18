import numpy as np
import pandas as pd
from ta import add_all_ta_features
from ta.utils import dropna
from ta.momentum import rsi
from datetime import datetime
from agent import Agent


class rsi_ta(Agent):
    def __init__(self, period : int = 8, name = "RSI"):
        super().__init__(name)
        self.period = period

    def Calculate(self, data) -> bool | None:
        close_prices = [x[3] for x in data]  # Assuming close is the 4th element
        series_data = pd.Series(close_prices, dtype=np.float32)  # Convert to Pandas Series

        _rsi = rsi(series_data, window=self.period)  # Use the correct RSI function with window

        rsi_lastvalue = _rsi.iloc[-1]  # Use iloc for the last value

        print(f"{self.name} rsi =  {rsi_lastvalue:.1f} ({datetime.now().strftime('%H:%M %d/%m')})")

        if (rsi_lastvalue <= 100 and rsi_lastvalue > 70): #and self.deal_pos < 1:
            self.deal_pos = 1
            return True
        elif (rsi_lastvalue >= 0 and rsi_lastvalue < 30): # and self.deal_pos > -1:
            self.deal_pos = -1
            return False
        else:
            return None


rsi_agent_ta = rsi_ta(period = 14, name="BOT")