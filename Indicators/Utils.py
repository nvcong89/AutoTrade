class Indicator:
    def __init__(self, name: str) -> None:
        self.name = name

    def Calculate(self) -> list:
        return None



def cross(data1: list, data2: list) -> bool | None:
    """
    Kiểm tra xem data1 có cắt lên đường data2 hay không.
    Điều kiện: data1 trước < data2 trước và data1 hiện tại > data2 hiện tại

    Trả về:
        - True nếu có cắt lên
        - False nếu không cắt
        - None nếu không đủ dữ liệu
    """
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
