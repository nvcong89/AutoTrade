"""
Timezone utilities for AutoTrade system
Ensures all datetime operations use GMT+7 (Vietnam timezone)
"""

from datetime import datetime, time, timezone, timedelta
import pytz

# Vietnam timezone (GMT+7)
VIETNAM_TZ = pytz.timezone('Asia/Ho_Chi_Minh')

def get_vietnam_now() -> datetime:
    """
    Get current datetime in Vietnam timezone (GMT+7)
    """
    return datetime.now(VIETNAM_TZ)

def get_vietnam_time() -> time:
    """
    Get current time in Vietnam timezone (GMT+7)
    """
    return get_vietnam_now().time()

def get_vietnam_date() -> datetime:
    """
    Get current date in Vietnam timezone (GMT+7)
    """
    return get_vietnam_now().date()

def is_trading_time_vietnam(trading_start: time, trading_end: time) -> bool:
    """
    Check if current Vietnam time is within trading hours
    
    Args:
        trading_start: Start time (e.g., time(9, 0))
        trading_end: End time (e.g., time(14, 25))
    
    Returns:
        bool: True if within trading hours
    """
    current_time = get_vietnam_time()
    return trading_start <= current_time <= trading_end

def get_vietnam_timestamp() -> int:
    """
    Get current Unix timestamp in Vietnam timezone
    """
    return int(get_vietnam_now().timestamp())

def convert_utc_to_vietnam(utc_dt: datetime) -> datetime:
    """
    Convert UTC datetime to Vietnam timezone
    
    Args:
        utc_dt: UTC datetime
    
    Returns:
        datetime: Vietnam timezone datetime
    """
    if utc_dt.tzinfo is None:
        # Assume UTC if no timezone info
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    
    return utc_dt.astimezone(VIETNAM_TZ)

def get_trading_day_vietnam() -> str:
    """
    Get current trading day in YYYY-MM-DD format (Vietnam timezone)
    """
    return get_vietnam_date().strftime('%Y-%m-%d')

def is_weekend_vietnam() -> bool:
    """
    Check if current day is weekend in Vietnam timezone
    """
    current_date = get_vietnam_date()
    return current_date.weekday() >= 5  # Saturday = 5, Sunday = 6

def get_market_status_vietnam() -> dict:
    """
    Get current market status in Vietnam timezone
    
    Returns:
        dict: Market status information
    """
    now = get_vietnam_now()
    current_time = now.time()
    current_date = now.date()
    
    # Trading hours: 9:00-11:30, 13:00-15:00 (Vietnam time)
    morning_start = time(9, 0)
    morning_end = time(11, 30)
    afternoon_start = time(13, 0)
    afternoon_end = time(15, 0)
    
    is_trading = (
        (morning_start <= current_time <= morning_end) or
        (afternoon_start <= current_time <= afternoon_end)
    )
    
    is_weekend = is_weekend_vietnam()
    
    return {
        'current_time': current_time.strftime('%H:%M:%S'),
        'current_date': current_date.strftime('%Y-%m-%d'),
        'is_trading': is_trading and not is_weekend,
        'is_weekend': is_weekend,
        'timezone': 'GMT+7 (Vietnam)',
        'next_trading_day': 'Monday' if is_weekend else 'Today'
    }

# Test function
if __name__ == "__main__":
    print("🇻🇳 Vietnam Timezone Utilities Test")
    print("=" * 40)
    
    print(f"Current Vietnam time: {get_vietnam_now()}")
    print(f"Current Vietnam time only: {get_vietnam_time()}")
    print(f"Current Vietnam date: {get_vietnam_date()}")
    print(f"Unix timestamp: {get_vietnam_timestamp()}")
    print(f"Trading day: {get_trading_day_vietnam()}")
    print(f"Is weekend: {is_weekend_vietnam()}")
    
    print("\n📊 Market Status:")
    status = get_market_status_vietnam()
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    print("\n⏰ Trading Time Test:")
    trading_start = time(9, 0)
    trading_end = time(14, 25)
    print(f"Trading hours: {trading_start} - {trading_end}")
    print(f"Is trading time: {is_trading_time_vietnam(trading_start, trading_end)}")
