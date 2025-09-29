import GLOBAL
from tabulate import tabulate
from Utils import*
from logger_config import setup_logger
import logging



_createdtimeToken = None #DO NOT REMOVE
_onstart = False    #DO NOT REMOVE



def OnStart(_onstart: bool = False):

    """
    Hàm xử lý, khai báo các biến đầu tiên khi bắt đầu bật bot. Chỉ chạy lần đầu tiên, sau tickdata đầu tiên.
    """
    #=====================================================================
    #DO NOT REMOVE
    #=====================================================================
    if _onstart == True:    #kiểm tra đã chạy chưa, True là đã chạy.
        return

    global logger #khai báo logger
    global _createdtimeToken

    if GLOBAL.DNSE_CLIENT:
        _createdtimeToken = GLOBAL.DNSE_CLIENT.createdtimeToken         # datetime isoformat

    logger = setup_logger("[Logic_Processor]", logging.INFO)

    #=====================================================================
    #DO NOT REMOVE
    #=====================================================================

    # Truy cập dữ liệu các TF
    cprint(f"1 phút gần nhất: {GLOBAL.MARKETDATA['m1'][-5:]}")
    cprint(f"5 phút gần nhất: {GLOBAL.MARKETDATA['m5'][-5:]}")
    cprint(f"15 phút gần nhất: {GLOBAL.MARKETDATA['m15'][-5:]}")

    # Visualize data
    cprint(f"Bảng data nến M1")
    logger.info(f"Bảng data nến M1")
    print(tabulate(
        GLOBAL.MARKETDATA['m1'][-5:],
        headers=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'],
        tablefmt='fancy_grid'
    ))
    
    logger.info(f"Bảng data nến M5")
    print(tabulate(
        GLOBAL.MARKETDATA['m5'][-5:],
        headers=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'],
        tablefmt='fancy_grid'
    ))
    
    logger.info(f"Bảng data nến M15")
    print(tabulate(
        GLOBAL.MARKETDATA['M5'][-5:],
        headers=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'],
        tablefmt='fancy_grid'
    ))


    #===========================================================
    #BẮT ĐẦU KHAI BÁO THÔNG SỐ VÀ KHỞI TẠO BOT
    #===========================================================
    #khởi tạo bot
    
    #in ra giá trần sàn ngày hôm nay
    logger.warning(f"Giá trần hôm nay : {bot.ceilingPrice}")
    logger.warning(f"Giá sàn hôm nay : {bot.floorPrice}")

    #khởi tạo bot ở đây

    pass

def OnTick():
    '''
    Xử lý code theo từng tick data.
    '''

    #===================================================================
    #DO NOT REMOVE
    #===================================================================
    global _onstart #biến để khởi chạy OnStart() sau tick data đầu tiên
    if not _onstart:
        OnStart(_onstart)   #gọi OnStart() sau tick đầu tiên, và chỉ gọi 1 lần duy nhất.
        _onstart = True
    #===================================================================
    #DO NOT REMOVE
    #===================================================================


    #THÊM LOGIC XỬ LÝ THEO TICK VÀO ĐÂY:

    pass

def OnBarClosed():

    #THÊM LOGIC XỬ LÝ SAU KHI ĐÓNG NẾN WORKINGTIMEFRAM ĐÃ SET Ở GLOBAL.PY

    pass





