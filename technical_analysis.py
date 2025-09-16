import numpy as np

def MA(data: np.ndarray, feature_idx: int = 3) -> np.ndarray:
    '''
    data: (m, n) np.ndarray
    '''
    _, n = data.shape

    if -n <= feature_idx < n:
        return np.mean(data[:, feature_idx]).item()

    return None

def STD(data: np.ndarray, feature_idx: int = 3) -> np.ndarray:
    '''
    data: (m, n) np.ndarray
    '''
    _, n = data.shape

    if -n <= feature_idx < n:
        return np.std(data[:, feature_idx]).item()

    return None

def rsi(data: np.ndarray, feature_idx: int = 3, period: int=14, wilder: bool=True) -> np.ndarray:
    '''
    Indicator: relative strength index
    data: (m, n) np.ndarray
    '''
    _, n = data.shape
    if -n <= feature_idx < n:
        prices = data[:, feature_idx].astype(float)
        if prices.size < period + 1:
            return None  # need at least period+1 points

        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0.0)
        losses = np.where(deltas < 0, -deltas, 0.0)

        if wilder:
            # Initial average gain/loss = simple mean of first 'period'
            avg_gain = gains[:period].mean()
            avg_loss = losses[:period].mean()
            # Wilder smoothing for the remaining points
            for g, l in zip(gains[period:], losses[period:]):
                avg_gain = (avg_gain * (period - 1) + g) / period
                avg_loss = (avg_loss * (period - 1) + l) / period
        else:
            # Simple (un-smoothed) RSI using only the last 'period' changes
            avg_gain = gains[-period:].mean()
            avg_loss = losses[-period:].mean()

        if avg_loss == 0:
            return 100.0  # All gains, no losses
        rs = avg_gain / avg_loss
        rsi_value = 100.0 - (100.0 / (1.0 + rs))
        return float(rsi_value)
