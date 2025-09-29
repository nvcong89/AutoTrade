from datetime import datetime, timedelta

import numpy as np
import pandas as pd



def print_color(text, color="default"):
    '''
    Dùng để in text ra console với màu sắc, ko dùng thư viện bên ngoài
    
    Example:
    print_color("Thông báo thành công!", "green")
    print_color("Cảnh báo!", "yellow")
    print_color("Lỗi nghiêm trọng!", "red")
    print_color("Thông tin hệ thống", "blue")

    '''
    colors = {
        "default": "\033[0m",
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "gray": "\033[90m",
    }
    
    color_code = colors.get(color.lower(), colors["default"])
    reset_code = colors["default"]
    print(f"{color_code}{text}{reset_code}")



def cprint(message):
    '''
    Hàm hỗ trợ in ra console có bao gồm ngày tháng và giờ.
    '''
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] - {message}")


#tên mã phái sinh KRX tháng hiện tại
def get_vn30f1m_krx() -> str:
    """
    Tạo mã hợp đồng VN30F1M theo chuẩn KRX mới
    Format: 41I1[Y][M]000
    - 4: loại chứng khoán phái sinh
    - 1: nhóm chứng khoán (Future)
    - I1: mã tài sản cơ sở VN30
    - Y: năm đáo hạn (0-9, A-W trừ I,O,U)
    - M: tháng đáo hạn (1-9,A,B,C)
    - 000: mã định danh hợp đồng tương lai
    """
    # Mapping năm đáo hạn theo bảng KRX
    year_mapping = {
        2010: '0', 2011: '1', 2012: '2', 2013: '3', 2014: '4', 2015: '5', 2016: '6', 2017: '7', 2018: '8', 2019: '9',
        2020: 'A', 2021: 'B', 2022: 'C', 2023: 'D', 2024: 'E', 2025: 'F', 2026: 'G', 2027: 'H', 2028: 'J', 2029: 'K',
        2030: 'L', 2031: 'M', 2032: 'N', 2033: 'P', 2034: 'Q', 2035: 'R', 2036: 'S', 2037: 'T', 2038: 'V', 2039: 'W'
    }

    # Mapping tháng đáo hạn theo bảng KRX
    month_mapping = {
        1: '1', 2: '2', 3: '3', 4: '4', 5: '5', 6: '6',
        7: '7', 8: '8', 9: '9', 10: 'A', 11: 'B', 12: 'C'
    }

    #Xác định current year, current month and current day, format : int
    year = datetime.now().year
    month = datetime.now().month
    day = datetime.now().day

    # Tìm ngày thứ 5 thứ 3 của tháng (ngày đáo hạn)
    first_day = datetime(year, month, 1)
    third_thursday = first_day + timedelta((3 - first_day.weekday() + 7) % 7) + timedelta(14)

    # Xác định tháng và năm đáo hạn
    if month == 12 and day > third_thursday.day:
        # Nếu quá ngày đáo hạn tháng 12, chuyển sang tháng 1 năm sau
        expiry_year = year + 1
        expiry_month = 1
    elif day <= third_thursday.day:
        # Nếu chưa qua ngày đáo hạn, dùng tháng hiện tại
        expiry_year = year
        expiry_month = month
    else:
        # Nếu đã qua ngày đáo hạn, chuyển sang tháng tiếp theo
        if month == 12:
            expiry_year = year + 1
            expiry_month = 1
        else:
            expiry_year = year
            expiry_month = month + 1

    # Lấy mã năm và tháng theo mapping KRX
    year_code = year_mapping.get(expiry_year, 'F')  # Default F cho 2025
    month_code = month_mapping.get(expiry_month, '1')  # Default 1 cho tháng 1

    # Tạo mã hợp đồng KRX: 41I1[Y][M]000
    krx_code = f"41I1{year_code}{month_code}000"

    return krx_code


def print_dict_table(data):
    '''
    In dictionary hoặc list of dictionaries dưới dạng bảng
    '''
    # Xác định headers
    headers = data[0].keys() if isinstance(data, list) else data.keys()
    
    # Tính độ rộng cột
    col_width = {key: max(len(str(key)), *[len(str(v)) for v in (data.values() if isinstance(data, dict) else [d[key] for d in data])]) for key in headers}
    
    # Tạo hàng ngăn cách
    separator = '+' + '+'.join(['-'*(width+2) for width in col_width.values()]) + '+'
    
    # In header
    print(separator)
    print('| ' + ' | '.join([str(key).ljust(col_width[key]) for key in headers]) + ' |')
    print(separator)
    
    # In dữ liệu
    if isinstance(data, dict):
        print('| ' + ' | '.join([str(data[key]).ljust(col_width[key]) for key in headers]) + ' |')
    else:
        for row in data:
            print('| ' + ' | '.join([str(row[key]).ljust(col_width[key]) for key in headers]) + ' |')
    print(separator)



def cross(data1: list | float | int, data2: list | float | int) -> bool | None:
    """
    Kiểm tra xem data1 có cắt lên đường data2 hay không.
    Điều kiện: data1 trước < data2 trước và data1 hiện tại > data2 hiện tại

    Trả về:
        - True nếu có cắt lên
        - False nếu không cắt
        - None nếu không đủ dữ liệu
    """
    # Nếu là số, chuyển thành list với 2 phần tử giống nhau
    if isinstance(data1, (int, float)):
        data1 = [data1, data1]
    if isinstance(data2, (int, float)):
        data2 = [data2, data2]

    if data1 is None or data2 is None:
        return None

    if len(data1) < 2 or len(data2) < 2:
        return None  # Không đủ dữ liệu để kiểm tra

    # Lấy 2 giá trị gần nhất
    prev1, curr1 = data1[-2], data1[-1]
    prev2, curr2 = data2[-2], data2[-1]

    # Kiểm tra điều kiện cắt lên
    if prev1 < prev2 and curr1 > curr2:
        return True
    else:
        return False

def value_when(condition, series, occurrence=0):
    return series.shift(occurrence+1).where(condition).ffill()


def exrem(series1, series2):
    clean = pd.Series(np.nan, index=series1.index)
    buy_flag = False
    sell_flag = False
    
    for i in range(len(series1)):
        if series1.iloc[i] and not sell_flag:
            clean.iloc[i] = True
            buy_flag = True
            sell_flag = False
        elif series2.iloc[i] and not buy_flag:
            clean.iloc[i] = True
            sell_flag = True
            buy_flag = False
        else:
            clean.iloc[i] = False
    return clean


def demoMarketData():
    """
    Tạo dữ liệu thị trường mô phỏng cho hợp đồng tương lai VN30
    Cải tiến chính:
    - Xử lý timeline chính xác trong giờ giao dịch
    - Mô phỏng giá thực tế hơn với cơ chế trôi dạt có điều kiện
    - Thêm biến động giá trong phiên
    - Điều chỉnh khối lượng theo phiên giao dịch
    - Thêm cột ngày và thời gian riêng biệt
    """
    # Cấu hình dữ liệu
    symbol = "VN30F1M"
    num_rows = 500
    initial_price = 1200.0
    trading_hours = ('09:15', '14:45')

    # Tạo timeline chính xác -------------------------------------------------
    days_needed = (num_rows // 330) + 2  # 330 phút/ngày giao dịch
    end_time = datetime(2025, 9, 24, 14, 45)
    start_time = end_time - timedelta(days=days_needed)
    
    # Tạo toàn bộ timeline rồi lọc giờ giao dịch
    timestamps = pd.date_range(start=start_time, end=end_time, freq='1T')
    df = pd.DataFrame(index=timestamps)
    df = df.between_time(*trading_hours).iloc[-num_rows:]  # Lấy 500 phiên gần nhất

    # Tạo dữ liệu giá --------------------------------------------------------
    np.random.seed(42)
    
    # 1. Tạo biến động giá cơ bản
    price_changes = np.random.normal(0, 0.0005, len(df))
    
    # 2. Thêm cơ chế trôi dạt có điều kiện
    drift = np.where(df.index.hour < 11, 0.0002, -0.0001)  # Trôi dạt buổi sáng/chiều
    price_changes += drift
    
    # 3. Tạo các mức giá
    close_prices = pd.Series(initial_price * (1 + np.cumsum(price_changes)), index=df.index)
    open_prices = close_prices.shift(1).fillna(initial_price)
    
    # 4. Thêm biến động trong phiên
    intraday_volatility = np.abs(np.random.normal(0, 0.001, (len(df), 2)))
    high_prices = close_prices + (close_prices * intraday_volatility[:, 0])
    low_prices = close_prices - (close_prices * intraday_volatility[:, 1])

    # Đảm bảo logic high/low
    df['open'] = np.round(open_prices, 1)
    df['high'] = np.round(np.maximum(high_prices, np.maximum(open_prices, close_prices)), 1)
    df['low'] = np.round(np.minimum(low_prices, np.minimum(open_prices, close_prices)), 1)
    df['close'] = np.round(close_prices, 1)

    # Tạo khối lượng thực tế -------------------------------------------------
    # 1. Khối lượng cơ bản
    base_volume = np.random.randint(500, 2000, len(df))
    
    # 2. Biến động theo thời gian trong phiên
    time_factor = np.sin(np.linspace(-np.pi/2, np.pi/2, len(df)))
    
    # 3. Tăng khối lượng khi có biến động giá
    volatility_effect = np.clip(intraday_volatility.mean(axis=1) * 1000, 0.5, 2.0)
    
    df['volume'] = np.round(base_volume * (1 + time_factor**2) * volatility_effect).astype(int)

    # Định dạng dữ liệu cuối cùng --------------------------------------------
    df = df.reset_index(names='time')
    # df['date'] = df['time'].dt.date.astype(str)
    df['time'] = df['time'].dt.strftime('%H:%M:%S')
    df = df[['time', 'open', 'high', 'low', 'close', 'volume']]
    # df = df[['date', 'time', 'open', 'high', 'low', 'close', 'volume']]

    print(f"\nDữ liệu mẫu {symbol} (5 dòng đầu):")
    print(df.head().to_string(index=False))
    print(f"\nThống kê mô tả:\n{df.describe().round(1)}")
    
    return df


def generate_market_data(base_price: float = 1200.0, 
                         num_candles: int = 1000,
                         volatility: float = 0.005,
                         seed: int = 42) -> dict:
    """
    Tạo dữ liệu giá ngẫu nhiên cho VN30F1M theo các khung thời gian
    Áp dụng nguyên tắc fractal và mô hình random walk có điều chỉnh
    
    Parameters:
        base_price (float): Giá khởi điểm (mặc định: 1200.0)
        num_candles (int): Số nến cơ sở (khung thời gian nhỏ nhất)
        volatility (float): Độ biến động (0.1 = 10%)
        seed (int): Seed cho random number generator
    
    Returns:
        dict: Dictionary chứa dữ liệu theo từng khung thời gian
    """

    TIME_FRAMES = {
    'm1': 60,
    'm3': 180,
    'm5': 300,
    'm15': 900,
    'm30': 1800,
    'H1': 3600,
    'D1': 86400,
    'W1': 604800
    }
    
    np.random.seed(seed)
    market_data = {tf: [] for tf in TIME_FRAMES}
    
    # Tạo dữ liệu gốc từ khung thời gian nhỏ nhất (m1)
    base_time = datetime(2025, 9, 24, 9, 15)
    price_series = base_price * (1 + np.cumsum(np.random.normal(
        scale=volatility/np.sqrt(252*390),  # Điều chỉnh theo số phiên/năm
        size=num_candles
    )))
    
    # Tạo timestamp cho từng nến m1
    timestamps = [base_time + timedelta(minutes=i) for i in range(num_candles)]
    
    # Điền dữ liệu cho tất cả khung thời gian
    for tf, seconds in TIME_FRAMES.items():
        tf_interval = seconds // 60  # Chuyển sang đơn vị phút
        grouped = []
        
        for i in range(0, num_candles, tf_interval):
            group = price_series[i:i+tf_interval]
            if len(group) == 0:
                continue
                
            open_price = group[0]
            close_price = group[-1]
            high = np.max(group)
            low = np.min(group)
            volume = int(np.random.uniform(500, 2000) * tf_interval**0.5)  # Điều chỉnh volume theo TF
            
            candle = {
                'time': timestamps[i].strftime('%Y-%m-%d %H:%M:%S'),
                'open': round(open_price, 1),
                'high': round(high, 1),
                'low': round(low, 1),
                'close': round(close_price, 1),
                'volume': volume
            }
            grouped.append(candle)
        
        market_data[tf] = grouped
    
    # Thêm tính năng fractal cho các khung lớn
    for tf in ['H1', 'D1', 'W1']:
        for candle in market_data[tf]:
            # Thêm bóng nến dài hơn cho các khung lớn
            candle['high'] += np.random.uniform(0, volatility*2)
            candle['low'] -= np.random.uniform(0, volatility*2)
            candle['volume'] = int(candle['volume'] * np.random.uniform(1.2, 2.5))
    
    return market_data


if __name__ == "__main__":

    # cprint(f"Mã hợp đồng VN30F1M KRX tháng hiện tại: {get_vn30f1m_krx()}")
    # # demoMarketData()

    # MARKETDATA = generate_market_data()
    # cprint(MARKETDATA['m1'][:10])
    # data = MARKETDATA['m1'][:10]
    # # Trích xuất close prices và timestamps
    # close_prices = [candle['close'] for candle in data]
    # timestamps = [candle['time'] for candle in data]

    # # Tạo pandas Series với index thời gian
    # close_series = pd.Series(
    #     data=close_prices,
    #     index=pd.to_datetime(timestamps),
    #     name='Close Price',
    #     dtype='float64'
    # )
    # cprint(close_series)
    # print(f"\nDữ liệu mẫu VN30F1M (m1) - 5 nến đầu:")
    # for row in MARKETDATA['m1'][:10]:
    #     print(row)

    
    print_color("Thông báo thành công!", "green")
    print_color("Cảnh báo!", "yellow")
    print_color("Lỗi nghiêm trọng!", "red")
    print_color("Thông tin hệ thống", "blue")
