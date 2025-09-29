import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
from timezone_utils import get_vietnam_now
from colorlog import ColoredFormatter


class VietnamTimeFormatter(logging.Formatter):
    """Custom formatter that uses Vietnam timezone for timestamps"""
    
    def formatTime(self, record, datefmt=None):
        """Override formatTime to use Vietnam timezone"""
        ct = get_vietnam_now()
        if datefmt:
            s = ct.strftime(datefmt)
        else:
            s = ct.strftime('%Y-%m-%d %H:%M:%S')
        return s

def setup_logger(name="AutoTrade-CONG NGUYEN", log_level=logging.INFO):
    """
    Setup logger với daily rotation và multiple handlers
    
    Args:
        name: Tên logger
        log_level: Mức độ logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        logger: Configured logger instance
    """
    
    # Tạo logs directory nếu chưa có
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Tạo logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Tránh duplicate handlers
    if logger.handlers:
        return logger
    
    # Format cho log messages (sử dụng Vietnam timezone)
    formatter = VietnamTimeFormatter(
        '[%(asctime)s] %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 🎨 Formatter có màu cho console
    color_formatter = ColoredFormatter(
        fmt='%(log_color)s[%(asctime)s] %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red',
        }
    )

    # Console Handler với màu sắc
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(color_formatter)
    logger.addHandler(console_handler)


    # Console Handler
    # console_handler = logging.StreamHandler()
    # console_handler.setLevel(logging.INFO)
    # console_handler.setFormatter(formatter)
    # logger.addHandler(console_handler)
    
    # File Handler với daily rotation (sử dụng Vietnam timezone)
    today = get_vietnam_now().strftime("%Y-%m-%d")
    log_file = logs_dir / f"autotrade_{today}.log"
    
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=log_file,
        when='midnight',
        interval=1,
        backupCount=6,  # Giữ lại 6 ngày
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Error Handler riêng cho errors
    error_log_file = logs_dir / f"autotrade_errors_{today}.log"
    error_handler = logging.handlers.TimedRotatingFileHandler(
        filename=error_log_file,
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    # Trading Handler riêng cho trading activities
    trading_log_file = logs_dir / f"trading_{today}.log"
    trading_handler = logging.handlers.TimedRotatingFileHandler(
        filename=trading_log_file,
        when='midnight',
        interval=1,
        backupCount=90,  # Giữ lại 90 ngày cho trading logs
        encoding='utf-8'
    )
    trading_handler.setLevel(logging.INFO)
    trading_formatter = VietnamTimeFormatter(
        '[%(asctime)s] %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    trading_handler.setFormatter(trading_formatter)
    
    # Tạo trading logger riêng
    trading_logger = logging.getLogger(f"{name}.trading")
    trading_logger.setLevel(logging.INFO)
    if not trading_logger.handlers:
        trading_logger.addHandler(trading_handler)
        # Tránh log duplicate lên parent logger
        trading_logger.propagate = False
    
    logger.info(f"Logger '{name}' initialized with daily rotation")
    
    return logger

def get_trading_logger(name="AutoTrade"):
    """Lấy trading logger để log các hoạt động giao dịch"""
    return logging.getLogger(f"{name}.trading")

def log_trade_action(action, symbol, side=None, price=None, quantity=None, **kwargs):
    """
    Log trading action với format chuẩn
    
    Args:
        action: Loại hành động (ORDER_PLACED, ORDER_CANCELLED, DEAL_CLOSED, etc.)
        symbol: Mã chứng khoán
        side: Mua/Bán (NB/NS)
        price: Giá
        quantity: Khối lượng
        **kwargs: Các thông tin bổ sung
    """
    trading_logger = get_trading_logger()
    
    log_parts = [f"ACTION={action}", f"SYMBOL={symbol}"]
    
    if side:
        log_parts.append(f"SIDE={side}")
    if price:
        log_parts.append(f"PRICE={price}")
    if quantity:
        log_parts.append(f"QUANTITY={quantity}")
    
    # Thêm các thông tin bổ sung
    for key, value in kwargs.items():
        if value is not None:
            log_parts.append(f"{key.upper()}={value}")
    
    message = " | ".join(log_parts)
    trading_logger.info(message)

def log_agent_signal(agent_name, signal, symbol, price, reason=""):
    """
    Log trading signal từ agents
    
    Args:
        agent_name: Tên agent
        signal: True (BUY), False (SELL), None (HOLD)
        symbol: Mã chứng khoán
        price: Giá hiện tại
        reason: Lý do đưa ra signal
    """
    trading_logger = get_trading_logger()
    
    signal_str = "BUY" if signal is True else "SELL" if signal is False else "HOLD"
    message = f"AGENT_SIGNAL | AGENT={agent_name} | SIGNAL={signal_str} | SYMBOL={symbol} | PRICE={price}"
    
    if reason:
        message += f" | REASON={reason}"
    
    trading_logger.info(message)

def log_market_data(symbol, ohlcv_data):
    """
    Log market data updates
    
    Args:
        symbol: Mã chứng khoán
        ohlcv_data: Dictionary chứa OHLCV data
    """
    logger = logging.getLogger("AutoTrade")
    
    if isinstance(ohlcv_data, (list, tuple)) and len(ohlcv_data) >= 5:
        o, h, l, c, v = ohlcv_data[:5]
        logger.debug(f"MARKET_DATA | SYMBOL={symbol} | O={o} | H={h} | L={l} | C={c} | V={v}")
    elif isinstance(ohlcv_data, dict):
        logger.debug(f"MARKET_DATA | SYMBOL={symbol} | DATA={ohlcv_data}")

def log_error_with_context(logger, error, context="", **kwargs):
    """
    Log error với context information
    
    Args:
        logger: Logger instance
        error: Exception object hoặc error message
        context: Mô tả context khi lỗi xảy ra
        **kwargs: Thông tin bổ sung
    """
    error_parts = []
    
    if context:
        error_parts.append(f"CONTEXT={context}")
    
    if isinstance(error, Exception):
        error_parts.append(f"ERROR={type(error).__name__}: {str(error)}")
    else:
        error_parts.append(f"ERROR={error}")
    
    for key, value in kwargs.items():
        if value is not None:
            error_parts.append(f"{key.upper()}={value}")
    
    message = " | ".join(error_parts)
    logger.error(message, exc_info=isinstance(error, Exception))

# Tạo default logger
default_logger = setup_logger()
