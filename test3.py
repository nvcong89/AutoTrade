import time
from requests import get
from tabulate import tabulate


# def GetOHLCVData(type: str, symbol: str, from_time: int, to_time: int, resolution: str = '15') -> dict[str, list[float]]:
#     '''
#     **type**: "derivative", "stock" hoặc "index"\n
#     **symbol**: mã cổ phiếu/phái sinh/thị trường tương ứng với 'type'\n
#     **from_time/to_time**: thời điểm bắt đầu/kết thúc lấy dữ liệu (Unix epoch time)\n
#     **resolution**: 1, 3, 5, 15, 30, 1H, 1D, 1W (nến 1/3/5/... phút)
#     '''

#     url = f"https://api.dnse.com.vn/chart-api/v2/ohlcs/{type}?from={from_time}&to={to_time}&symbol={symbol}&resolution={resolution}"

#     response = get(url)
#     response.raise_for_status()
#     return response.json()



if __name__ == "__main__":

    # days_lookback = 3
    # start_time = int(time.time()) - 86400*days_lookback # 30 ngày dữ liệu

    # data = GetOHLCVData("derivative","VN30F1M", start_time, int(time.time()),"1")
    # print(data['c'][-5:])
    # print(data['t'][-5:])

    # Visualize data
    # print(f"Bảng data nến M1")
    # # logger.info(f"Bảng data nến M1")
    # print(tabulate(
    #     data[-5:],
    #     headers=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'],
    #     tablefmt='fancy_grid'
    # ))
    from datetime import datetime

    # Timestamp cần so sánh (ví dụ: 1695897600)
    timestamp = 1695897600
    date_from_timestamp = datetime.fromtimestamp(timestamp).date()

    # Lấy ngày hiện tại
    today = datetime.today().date()

    # So sánh
    if date_from_timestamp < today:
        print("Ngày trong timestamp là quá khứ.")
    elif date_from_timestamp > today:
        print("Ngày trong timestamp là tương lai.")
    else:
        print("Ngày trong timestamp là hôm nay.")


    pass