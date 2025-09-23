#%% [1] Tạo dữ liệu tổng hợp
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

np.random.seed(2025)
n_ticks = 1000

# Tạo timestamp
base_time = datetime(2025, 9, 23, 8, 45)
timestamps = [base_time + timedelta(seconds=np.random.randint(0, 900), 
                                  milliseconds=np.random.randint(0, 999)) 
            for _ in range(n_ticks)]
timestamps.sort()

# Tạo price dynamics
mid_prices = 1200 + np.cumsum(np.random.normal(0, 0.08, n_ticks))
spreads = np.random.choice([0.1, 0.2], n_ticks, p=[0.75, 0.25])
bid_prices = (mid_prices - spreads/2).round(1)
ask_prices = (mid_prices + spreads/2).round(1)

# Tạo trade data
trade_data = []
for i in range(n_ticks):
    if np.random.rand() < 0.6:
        price = ask_prices[i] if np.random.rand() < 0.55 else bid_prices[i]
    else:
        price = round(np.random.uniform(bid_prices[i], ask_prices[i]), 1)
    volume = np.random.randint(1, 20)
    trade_data.append((price, volume))

df = pd.DataFrame({
    'timestamp': timestamps,
    'bid': bid_prices,
    'bid_size': np.random.randint(10, 100, n_ticks),
    'ask': ask_prices,
    'ask_size': np.random.randint(10, 100, n_ticks),
    'last_price': [x[0] for x in trade_data],
    'last_volume': [x[1] for x in trade_data]
})

#%% [2] Tính toán features và label
# Tính toán mid price và spread
df['mid'] = (df['bid'] + df['ask'])/2
df['spread'] = (df['ask'] - df['bid']).round(1)

# Xác định hướng trade (Lee-Ready)
conditions = [
    df['last_price'] == df['ask'],
    df['last_price'] == df['bid'],
    df['last_price'] > df['mid']
]
choices = [1, -1, 1]
df['trade_sign'] = np.select(conditions, choices, default=-1)

# Tính CVD và features
df['cvd'] = (df['trade_sign'] * df['last_volume']).cumsum()
df['volatility'] = df['mid'].diff().abs().rolling(20).std().fillna(0)
df['imbalance'] = (df['bid_size'] - df['ask_size'])/(df['bid_size'] + df['ask_size'] + 1e-6)

# Tạo label 5 ticks
H = 5
df['future_mid'] = df['mid'].shift(-H)
df['label'] = np.where(
    df['future_mid'] - df['mid'] >= 0.5, 1,
    np.where(df['mid'] - df['future_mid'] >= 0.5, 0, -1)
)
df = df[~df['future_mid'].isna()]

#%% [3] Huấn luyện mô hình
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report

features = ['spread', 'imbalance', 'volatility', 'cvd']
X = df[features]
y = df['label'].replace({-1: 0})  # Chuyển neutral thành 0

model = LogisticRegression(class_weight='balanced')
model.fit(X, y)

# Dự đoán
df['pred_prob'] = model.predict_proba(X)[:, 1]
print(classification_report(y, model.predict(X)))

#%% [4] Backtest đơn giản
capital = 100_000_000  # 100 triệu VND
position = 0
trade_log = []

for idx, row in df.iterrows():
    if row['pred_prob'] > 0.65 and position < 3:
        # Market buy
        entry = row['ask']
        position += 1
        capital -= entry * 100000 + 15000  # Phí
        trade_log.append({
            'time': row['timestamp'],
            'side': 'BUY',
            'price': entry,
            'size': 1
        })
    elif row['pred_prob'] < 0.35 and position > -3:
        # Market sell
        entry = row['bid']
        position -= 1
        capital += entry * 100000 - 15000
        trade_log.append({
            'time': row['timestamp'],
            'side': 'SELL',
            'price': entry,
            'size': 1
        })
    
    # Exit sau 5 ticks
    if len(trade_log) > 0 and (idx - trade_log[-1]['time']).seconds >= 5:
        # Logic thoát lệnh
        pass  # Thêm logic thoát lệnh tương tự

# Tính PnL cuối
final_value = capital + position * df.iloc[-1]['mid'] * 100000
print(f"Lợi nhuận: {final_value - 100_000_000:,.0f} VND")
