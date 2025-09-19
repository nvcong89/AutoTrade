import numpy as np
import pandas as pd
from Indicators.Utils import Indicator
from ta import  trend


class ADXIndicator(Indicator):
    def __init__(self,data, period : int = 8, name = "ADX"):
        super().__init__(name)
        self.data = data
        self.period = period

    def Calculate(self):
        close_prices = [x[3] for x in self.data]  # Assuming close is the 4th element
        series_data_open = pd.Series([x[0] for x in self.data], dtype=np.float32)  # Convert to Pandas Series
        series_data_high = pd.Series([x[1] for x in self.data], dtype=np.float32)  # Convert to Pandas Series
        series_data_low = pd.Series([x[2] for x in self.data], dtype=np.float32)  # Convert to Pandas Series
        series_data_close = pd.Series([x[3] for x in self.data], dtype=np.float32)  # Convert to Pandas Series
        series_data_vol = pd.Series([x[4] for x in self.data], dtype=np.float32)  # Convert to Pandas Series

        _adx = trend.adx(series_data_high,series_data_low,series_data_close, window=self.period)

        return _adx.tolist()

def adx(data, period)->list:
    return ADXIndicator(data, period).Calculate()

