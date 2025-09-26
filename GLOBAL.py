from datetime import datetime, timedelta
from dnse_client import DNSEClient
from entrade_client import EntradeClient
from json import load

def ReadConfig():
    with open("config.json", 'r') as f:
        return load(f)

# Initialized at start, shouldn't be modified in runtime
DNSE_CLIENT = DNSEClient()
ENTRADE_CLIENT = EntradeClient()



# Global data collected during runtime:

# List of 10 highest bid/lowest offer and their quantity
BID_DEPTH: list[tuple[float, int]] = []
OFFER_DEPTH: list[tuple[float, int]] = []

# Dư mua/Dư bán
TOTAL_BID: int = 0
TOTAL_OFFER: int = 0

# Tổng KLGD mua/bán của NĐT nước ngoài trong ngày
TOTAL_FOREIGN_BUY: int = 0
TOTAL_FOREIGN_SELL: int = 0

#WORKING TIMEFRAME : là timeframe để sau mỗi khi đóng nến sẽ thực thi function OnBarClosed()
WORKING_TIMEFRAME = 'm1' # m1, m3, m5, m15, m30, H1, H4, D1, W1

#Giá khớp lệnh tức thời - Tick price
TICK_PRICE: float = 0.0
TICK_VOLUME: int = 0

#Collection of historical candles for each timeframe
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
MARKETDATA = {tf: [] for tf in TIME_FRAMES} # Dictionary lưu data cho từng TF


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


VN30F1M = get_vn30f1m_krx()