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

def setup_logger(
    name="AutoTrade-CONG NGUYEN",
    log_level=logging.INFO,
    output="console",  # "both" | "console" | "file"
):
    """
    Setup logger với daily rotation và multiple handlers
    output:
      - "both": ghi file + in console (mặc định)
      - "console": chỉ in console
      - "file": chỉ ghi file
    """
    # Validate output
    assert output in {"both", "console", "file"}, "output must be 'both' | 'console' | 'file'"

    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Xóa handlers cũ nếu muốn reconfigure (tránh bị kẹt config cũ)
    if logger.handlers:
        for h in list(logger.handlers):
            logger.removeHandler(h)
            h.close()

    # Base formatters
    formatter = VietnamTimeFormatter(
        '[%(asctime)s] %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

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

    # Handlers theo output
    today = get_vietnam_now().strftime("%Y-%m-%d")
    handlers = []

    if output in {"both", "console"}:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(color_formatter)
        handlers.append(console_handler)

    if output in {"both", "file"}:
        # File Handler chung
        log_file = logs_dir / f"autotrade_{today}.log"
        file_handler = logging.handlers.TimedRotatingFileHandler(
            filename=log_file, when='midnight', interval=1, backupCount=6, encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

        # Error Handler
        error_log_file = logs_dir / f"autotrade_errors_{today}.log"
        error_handler = logging.handlers.TimedRotatingFileHandler(
            filename=error_log_file, when='midnight', interval=1, backupCount=30, encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        handlers.append(error_handler)

    for h in handlers:
        logger.addHandler(h)

    # Trading logger cấu hình theo cùng output
    trading_logger_name = f"{name}.trading"
    trading_logger = logging.getLogger(trading_logger_name)
    trading_logger.setLevel(logging.INFO)

    # Clear cũ
    if trading_logger.handlers:
        for h in list(trading_logger.handlers):
            trading_logger.removeHandler(h)
            h.close()

    trading_formatter = VietnamTimeFormatter(
        '[%(asctime)s] %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    trading_handlers = []
    if output in {"both", "console"}:
        tr_console = logging.StreamHandler()
        tr_console.setLevel(logging.INFO)
        # Có thể dùng formatter thường (không màu) cho trading, hoặc tái dùng color
        tr_console.setFormatter(color_formatter)
        trading_handlers.append(tr_console)

    if output in {"both", "file"}:
        trading_log_file = logs_dir / f"trading_{today}.log"
        trading_handler = logging.handlers.TimedRotatingFileHandler(
            filename=trading_log_file, when='midnight', interval=1, backupCount=90, encoding='utf-8'
        )
        trading_handler.setLevel(logging.INFO)
        trading_handler.setFormatter(trading_formatter)
        trading_handlers.append(trading_handler)

    for h in trading_handlers:
        trading_logger.addHandler(h)
    trading_logger.propagate = False

    logger.info(f"Logger '{name}' initialized with output='{output}'")
    return logger


def get_trading_logger(name="AutoTrade-CONG NGUYEN"):
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
