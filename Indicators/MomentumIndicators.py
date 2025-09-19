import numpy as np
import pandas as pd
from Indicators.Utils import Indicator
from ta import momentum  # Đảm bảo import đúng hàm RSI từ thư viện ta

class RSIIndicator(Indicator):
    """
    RSI Indicator
    input: data, period
    output: a list of values
    """
    def __init__(self, data, period: int = 8, name="RSI"):
        super().__init__(name)
        self._data = data
        self.period = period
        self.Calculate()

    def rsi(self) -> list:
        # Giả sử mỗi phần tử trong data là [open, high, low, close, volume]
        close_prices = [x[3] for x in self._data]  # Lấy giá đóng cửa
        series_data = pd.Series(close_prices, dtype=np.float32)  # Chuyển thành Pandas Series
        _rsi = momentum.rsi(series_data, window=self.period)  # Tính RSI
        return _rsi.tolist()  # Trả về dưới dạng list


def rsi(data, periodRSI) -> list:
    return RSIIndicator(data, periodRSI).rsi()

#==================================================

#==================================================


# test code
if __name__ == "__main__":
    sample_data = [
        [1846.4, 1846.5, 1846.0, 1846.1, 1090],
        [1846.2, 1846.6, 1846.1, 1826.3, 1200],
        [1846.2, 1846.6, 1846.1, 1846.3, 1200],
        [1846.2, 1846.6, 1846.1, 1886.3, 1200],
        [1846.2, 1846.6, 1846.1, 1816.3, 1200],
        [1846.2, 1846.6, 1846.1, 1826.3, 1200],
        [1846.2, 1846.6, 1846.1, 1866.3, 1200],
        [1846.2, 1846.6, 1846.1, 1896.3, 1200],
        [1846.2, 1846.6, 1846.1, 1816.3, 1200],
        [1846.2, 1846.6, 1846.1, 1836.3, 1200],
        [1846.2, 1846.6, 1846.1, 1876.3, 1200],
        [1846.2, 1846.6, 1846.1, 1866.3, 1200]
    ]

    rsi_values = rsi(sample_data, 8)
    print(rsi_values)
    print(f"Last value RSI = {rsi_values[-1]}")


