import pandas as pd
import numpy as np
from collections import deque
from sklearn.linear_model import LogisticRegression
import time

class VN30FScalper:
    def __init__(self, horizon_ticks=6, prob_min=0.58, tick_size=0.1, multiplier=100000):
        self.horizon = horizon_ticks
        self.prob_min = prob_min
        self.tick_size = tick_size
        self.multiplier = multiplier
        self.model = LogisticRegression()
        self.trained = False
        self.buffer = []          # store raw ticks
        self.feature_rows = []    # store feature snapshots for training
        self.labels = []
        self.last_mid = None
        self.trade_sign_series = deque(maxlen=5000)
        self.cvd = 0
        self.cvd_series = deque(maxlen=5000)
        self.mid_series = deque(maxlen=5000)
        self.pred_log = []

    def on_tick(self, tick):
        # tick: dict with keys:
        # timestamp, bid, bid_size, ask, ask_size, last_price, last_volume
        self.buffer.append(tick)
        mid = (tick['bid'] + tick['ask']) / 2
        if self.last_mid is None:
            self.last_mid = mid

        # Infer trade sign
        trade_sign = 0
        lp = tick['last_price']
        if lp == tick['ask']:
            trade_sign = +1
        elif lp == tick['bid']:
            trade_sign = -1
        else:
            # tick rule fallback
            trade_sign = 1 if lp > self.last_mid else -1

        self.cvd += trade_sign * tick['last_volume']
        self.trade_sign_series.append(trade_sign)
        self.cvd_series.append(self.cvd)
        self.mid_series.append(mid)
        self.last_mid = mid

        feat = self._make_feature_snapshot()
        if feat is not None:
            self.feature_rows.append(feat)

    def _make_feature_snapshot(self):
        if len(self.mid_series) < 30:
            return None
        arr_mid = np.array(self.mid_series)
        arr_cvd = np.array(self.cvd_series)
        arr_ts = np.array(self.trade_sign_series)

        ret1 = 0 if len(arr_mid) < 2 else (arr_mid[-1] - arr_mid[-2]) / arr_mid[-2]
        vol_last_10 = np.abs(arr_ts[-10:]).sum()
        up_ratio_10 = (arr_ts[-10:] == 1).sum() / 10
        cvd_delta_50 = arr_cvd[-1] - arr_cvd[max(0, len(arr_cvd)-51)]
        volatility = np.sqrt(np.sum(np.diff(arr_mid[-20:])**2))
        run_up = 0
        for s in reversed(arr_ts):
            if s == 1: run_up += 1
            else: break
        run_down = 0
        for s in reversed(arr_ts):
            if s == -1: run_down += 1
            else: break

        f = {
            "mid": arr_mid[-1],
            "ret1": ret1,
            "volatility": volatility,
            "cvd_delta_50": cvd_delta_50,
            "up_ratio_10": up_ratio_10,
            "run_up": run_up,
            "run_down": run_down,
            "vol_last_10": vol_last_10
        }
        return f

    def prepare_training_set(self):
        df = pd.DataFrame(self.feature_rows)
        # Label using horizon on mid
        mids = df.mid.values
        future = np.roll(mids, -self.horizon)
        diff = future - mids
        threshold = self.tick_size  # 1 tick
        label = np.where(diff > threshold, 1,
                 np.where(diff < -threshold, 0, -1))  # -1 = neutral
        valid_mask = label != -1
        X = df.loc[valid_mask].drop(columns=["mid"])
        y = label[valid_mask]
        return X, y

    def train(self):
        X, y = self.prepare_training_set()
        if len(np.unique(y)) < 2:
            print("Not enough classes to train.")
            return
        self.model.fit(X, y)
        self.trained = True

    def predict_live(self, latest_feature):
        if not self.trained:
            return None
        X = np.array([ [v for k,v in latest_feature.items() if k != "mid"] ])
        prob = self.model.predict_proba(X)[0,1]
        return prob

    def decide(self, latest_feature, fees_in_tick=0.3):
        prob = self.predict_live(latest_feature)
        if prob is None:
            return None
        # EV approximation (TP = +2 ticks, SL = -1 tick)
        tp = 2 - fees_in_tick
        sl = 1 + fees_in_tick
        ev = prob * tp - (1 - prob) * sl
        action = None
        if prob > self.prob_min and ev > 0:
            action = {"side": "BUY", "ev": ev, "prob": prob}
        elif (1 - prob) > self.prob_min and ev > 0:
            action = {"side": "SELL", "ev": ev, "prob": 1 - prob}
        self.pred_log.append({"prob": prob, "ev": ev, "feature_mid": latest_feature["mid"], "timestamp": time.time()})
        return action


class ExecutionEngine:
    def __init__(self, api, max_position=5):
        self.api = api
        self.position = 0
        self.max_pos = max_position
        self.open_orders = {}

    def place_limit(self, side, price, size):
        order_id = self.api.place_limit(symbol="VN30F1M", side=side, price=price, size=size)
        self.open_orders[order_id] = {"side": side, "price": price, "size": size, "time": time.time()}
        return order_id

    def cancel_order(self, order_id):
        self.api.cancel(order_id)
        self.open_orders.pop(order_id, None)

    def manage_orders(self, bid, ask):
        # Cancel stale orders > timeout
        now = time.time()
        timeout = 3  # seconds
        for oid, meta in list(self.open_orders.items()):
            if now - meta["time"] > timeout:
                self.cancel_order(oid)

    def can_open(self, side):
        if side == "BUY" and self.position >= self.max_pos:
            return False
        if side == "SELL" and self.position <= -self.max_pos:
            return False
        return True
