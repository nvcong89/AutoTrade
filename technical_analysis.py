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

def rsi(data: np.ndarray, feature_idx: int = 3, period: int = 14, wilder: bool = True) -> np.ndarray:
    '''
    Indicator: relative strength index
    data: (m, n) np.ndarray
    Returns: np.ndarray of RSI values (length: m - period)
    '''
    if data.ndim != 2:
        raise ValueError("Input data must be 2D array (m, n)")
    m, n = data.shape
    if not (-n <= feature_idx < n):
        raise IndexError("feature_idx out of range")
    prices = data[:, feature_idx].astype(float)
    if prices.size < period + 1:
        return np.array([])  # Not enough data

    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)

    rsi_values = np.full(prices.size, np.nan)

    if wilder:
        # First RSI value (at index period)
        avg_gain = gains[:period].mean()
        avg_loss = losses[:period].mean()
        if avg_loss == 0:
            rsi_values[period] = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi_values[period] = 100.0 - (100.0 / (1.0 + rs))
        # Wilder smoothing for the rest
        for i in range(period + 1, prices.size):
            gain = gains[i - 1]
            loss = losses[i - 1]
            avg_gain = (avg_gain * (period - 1) + gain) / period
            avg_loss = (avg_loss * (period - 1) + loss) / period
            if avg_loss == 0:
                rsi_values[i] = 100.0
            else:
                rs = avg_gain / avg_loss
                rsi_values[i] = 100.0 - (100.0 / (1.0 + rs))
    else:
        # Simple RSI (rolling window)
        for i in range(period, prices.size):
            avg_gain = gains[i - period:i].mean()
            avg_loss = losses[i - period:i].mean()
            if avg_loss == 0:
                rsi_values[i] = 100.0
            else:
                rs = avg_gain / avg_loss
                rsi_values[i] = 100.0 - (100.0 / (1.0 + rs))

    # Return only valid RSI values (from index period onwards)
    return rsi_values[period:]
