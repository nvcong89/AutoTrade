import numpy as np
import technical_analysis as ta
from agent import Agent
from logger_config import setup_logger, log_agent_signal
from datetime import datetime, time
from symbol_manager import get_data_symbol
from timezone_utils import get_vietnam_time, is_trading_time_vietnam

class SmartBotAgent(Agent):
    """
    SmartBot Trading Strategy Agent
    
    Intraday derivative trading strategy focused on MACD momentum with RSI and ADX confirmation.
    Includes dynamic trailing stop and time-based trading restrictions.
    
    Features:
    - MACD for momentum detection
    - RSI for overbought/oversold confirmation  
    - ADX for trend strength
    - Intraday trading hours (9:00-14:18)
    - Dynamic trailing stop loss
    - High/Low breakout exit conditions
    """
    
    def __init__(self,
                 macd_fast: int = 23,
                 macd_slow: int = 26,
                 macd_signal: int = 24,
                 rsi_period: int = 14,
                 adx_period: int = 8,
                 adx_threshold: float = 22.0,
                 rsi_buy_threshold: float = 40.0,
                 rsi_sell_threshold: float = 45.0,
                 hl_period: int = 24,
                 hl_buffer: float = 1.5,
                 trigger_profit: float = 3.0,
                 trailing_stop_buy: float = 10.0,
                 trailing_stop_short: float = 10.0,
                 stop_loss: float = 15.0,
                 trading_start_hour: int = 9,
                 trading_start_minute: int = 15,
                 trading_end_hour: int = 14,
                 trading_end_minute: int = 25,
                 name: str = "SmartBot Agent"):
        
        super().__init__(name)
        
        # MACD parameters
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow  
        self.macd_signal = macd_signal
        
        # RSI parameters
        self.rsi_period = rsi_period
        self.rsi_buy_threshold = rsi_buy_threshold
        self.rsi_sell_threshold = rsi_sell_threshold
        
        # ADX parameters
        self.adx_period = adx_period
        self.adx_threshold = adx_threshold
        
        # High/Low breakout parameters
        self.hl_period = hl_period
        self.hl_buffer = hl_buffer
        
        # Risk management parameters
        self.trigger_profit = trigger_profit
        self.trailing_stop_buy = trailing_stop_buy
        self.trailing_stop_short = trailing_stop_short
        self.stop_loss = stop_loss
        
        # Trading time parameters
        self.trading_start = time(trading_start_hour, trading_start_minute)
        self.trading_end = time(trading_end_hour, trading_end_minute)
        
        # Position tracking
        self.entry_price = None
        self.highest_price = None
        self.lowest_price = None
        self.buy_sl = None
        self.short_sl = None
        
        # Setup logger
        self.logger = setup_logger("SmartBot_Agent")
        
        self.logger.info(f"Initialized {self.name} with parameters:")
        self.logger.info(f"MACD: fast={macd_fast}, slow={macd_slow}, signal={macd_signal}")
        self.logger.info(f"RSI: period={rsi_period}, buy_thresh={rsi_buy_threshold}, sell_thresh={rsi_sell_threshold}")
        self.logger.info(f"ADX: period={adx_period}, threshold={adx_threshold}")
        self.logger.info(f"Trading hours: {self.trading_start} - {self.trading_end}")
        self.logger.info(f"Risk: trigger_profit={trigger_profit}, trailing_stop={trailing_stop_buy}/{trailing_stop_short}, SL={stop_loss}")

    def is_trading_time(self) -> bool:
        """Check if current Vietnam time is within trading hours"""
        return is_trading_time_vietnam(self.trading_start, self.trading_end)

    def update_trailing_stop(self, current_price: float):
        """Update trailing stop levels based on current price and profit"""
        if self.deal_pos == 1 and self.entry_price is not None:  # Long position
            if self.highest_price is None or current_price > self.highest_price:
                self.highest_price = current_price
            
            profit = self.highest_price - self.entry_price
            if profit >= self.trigger_profit:
                # Dynamic trailing stop
                self.buy_sl = self.highest_price - self.trailing_stop_buy
                self.logger.info(f"Buy trailing stop updated to {self.buy_sl:.1f}")
            else:
                # Fixed stop loss
                self.buy_sl = self.entry_price - self.stop_loss
                self.logger.info(f"Buy stop loss updated to {self.buy_sl:.1f}")
                
        elif self.deal_pos == -1 and self.entry_price is not None:  # Short position
            if self.lowest_price is None or current_price < self.lowest_price:
                self.lowest_price = current_price
            
            profit = self.entry_price - self.lowest_price
            if profit >= self.trigger_profit:
                # Dynamic trailing stop
                self.short_sl = self.lowest_price + self.trailing_stop_short
                self.logger.info(f"Short trailing stop updated to {self.short_sl:.1f}")
            else:
                # Fixed stop loss
                self.short_sl = self.entry_price + self.stop_loss
                self.logger.info(f"Short stop loss updated to {self.short_sl:.1f}")

    def check_stop_loss(self, current_price: float) -> bool | None:
        """Check if stop loss should be triggered"""
        if self.deal_pos == 1 and self.buy_sl is not None:
            if current_price <= self.buy_sl:
                self.logger.info(f"Buy stop loss triggered at {current_price:.1f}, SL={self.buy_sl:.1f}")
                self._reset_position()
                return False  # Close long position (sell)
                
        elif self.deal_pos == -1 and self.short_sl is not None:
            if current_price >= self.short_sl:
                self.logger.info(f"Short stop loss triggered at {current_price:.1f}, SL={self.short_sl:.1f}")
                self._reset_position()
                return True  # Close short position (cover/buy)
        
        return None

    def _reset_position(self):
        """Reset position tracking variables"""
        self.deal_pos = 0
        self.entry_price = None
        self.highest_price = None
        self.lowest_price = None
        self.buy_sl = None
        self.short_sl = None
        self.logger.info("Position reset")

    def Calculate(self, data) -> bool | None:
        """
        Calculate SmartBot trading signals
        
        Buy Signal: MACD > Signal AND RSI >= 40 AND ADX > 22 AND timeOK
        Short Signal: ((Cross(Signal, MACD) AND RSI <= 45) OR (Signal > MACD AND Cross(45, RSI))) AND timeOK
        
        Additional exit conditions:
        - Stop loss triggers
        - High/Low breakouts
        - End of trading session
        """
        try:
            np_data = np.array(data, dtype=np.float32)
            
            # Need enough data for calculations (5-minute timeframe)
            min_periods = max(self.macd_slow, self.rsi_period, self.adx_period, self.hl_period)
            required_candles = min_periods * 3  # Need 3x the max period for stable calculations
            if len(np_data) < required_candles:
                self.logger.debug(f"Insufficient 5m data: {len(np_data)} < {required_candles} (max_period: {min_periods})")
                return None
            
            # Validate data integrity
            if np.any(np.isnan(np_data)) or np.any(np.isinf(np_data)):
                self.logger.warning("Invalid data detected (NaN or Inf values)")
                return None
            
            # Check trading time
            if not self.is_trading_time():
                # Close positions at end of trading session
                if self.deal_pos != 0:
                    self.logger.info("Closing position due to end of trading hours")
                    result = False if self.deal_pos == 1 else True
                    self._reset_position()
                    return result
                return None
            
            # Get current price data
            current_close = np_data[-1, 3]
            current_high = np_data[-1, 1]
            current_low = np_data[-1, 2]
            
            # Update trailing stop
            self.update_trailing_stop(current_close)
            
            # Check stop loss first
            sl_signal = self.check_stop_loss(current_close)
            if sl_signal is not None:
                return sl_signal
            
            # Calculate technical indicators
            macd_line, signal_line, histogram = ta.MACD(
                np_data, fast=self.macd_fast, slow=self.macd_slow, signal=self.macd_signal
            )
            
            # Validate MACD results
            if (macd_line is None or signal_line is None or 
                len(macd_line) == 0 or len(signal_line) == 0):
                self.logger.warning("MACD calculation failed")
                return None
            
            rsi_values = ta.RSI(np_data, period=self.rsi_period)
            if rsi_values is None or len(rsi_values) == 0:
                self.logger.warning("RSI calculation failed")
                return None
                
            adx_values = ta.ADX(np_data, period=self.adx_period)
            if adx_values is None or len(adx_values) == 0:
                self.logger.warning("ADX calculation failed")
                return None
            
            # Get current values
            current_macd = macd_line[-1]
            current_signal = signal_line[-1]
            current_rsi = rsi_values[-1]
            current_adx = adx_values[-1]
            
            # Get previous values for cross detection
            prev_macd = macd_line[-2] if len(macd_line) > 1 else current_macd
            prev_signal = signal_line[-2] if len(signal_line) > 1 else current_signal
            prev_rsi = rsi_values[-2] if len(rsi_values) > 1 else current_rsi
            
            # Calculate High/Low levels for breakout exits
            hhv_values = ta.HHV(np_data, period=self.hl_period, price_col=1)  # High
            llv_values = ta.LLV(np_data, period=self.hl_period, price_col=2)  # Low
            
            high_breakout_level = hhv_values[-6] + self.hl_buffer if len(hhv_values) > 5 else current_high
            low_breakout_level = llv_values[-6] - self.hl_buffer if len(llv_values) > 5 else current_low
            
            # Check breakout exit conditions
            if self.deal_pos == 1 and current_close <= low_breakout_level:
                self.logger.info(f"Long position closed due to low breakout at {current_close:.1f}")
                self._reset_position()
                return False
                
            if self.deal_pos == -1 and current_close >= high_breakout_level:
                self.logger.info(f"Short position closed due to high breakout at {current_close:.1f}")
                self._reset_position() 
                return True
            
            # Define cross conditions
            macd_bullish_cross = prev_macd <= prev_signal and current_macd > current_signal
            macd_bearish_cross = prev_signal <= prev_macd and current_signal > current_macd
            rsi_down_cross = prev_rsi >= self.rsi_sell_threshold and current_rsi < self.rsi_sell_threshold
            
            # Log current indicators
            self.logger.debug(f"MACD: {current_macd:.3f}, Signal: {current_signal:.3f}")
            self.logger.debug(f"RSI: {current_rsi:.1f}, ADX: {current_adx:.1f}")
            self.logger.debug(f"Position: {self.deal_pos}, Entry: {self.entry_price}")
            
            # Check Buy conditions
            # Buy: MACD > Signal AND RSI >= 40 AND ADX > 22
            if (current_macd > current_signal and 
                current_rsi >= self.rsi_buy_threshold and
                current_adx > self.adx_threshold):
                
                if self.deal_pos < 1:  # Not already long
                    self.deal_pos = 1
                    self.entry_price = current_close
                    self.highest_price = current_close
                    self.lowest_price = None
                    
                    reason = f"MACD>{current_signal:.3f}, RSI={current_rsi:.1f}, ADX={current_adx:.1f}"
                    symbol = get_data_symbol()
                    log_agent_signal(self.name, True, symbol, current_close, reason)
                    self.logger.info(f"BUY signal generated at {current_close:.1f} - {reason}")
                    return True
            
            # Check Short conditions
            # Short: (Cross(Signal, MACD) AND RSI <= 45) OR (Signal > MACD AND Cross(45, RSI))
            elif ((macd_bearish_cross and current_rsi <= self.rsi_sell_threshold) or
                  (current_signal > current_macd and rsi_down_cross)):
                
                if self.deal_pos > -1:  # Not already short
                    self.deal_pos = -1
                    self.entry_price = current_close
                    self.lowest_price = current_close
                    self.highest_price = None
                    
                    reason = f"Signal>{current_macd:.3f}, RSI={current_rsi:.1f}, ADX={current_adx:.1f}"
                    symbol = get_data_symbol()
                    log_agent_signal(self.name, False, symbol, current_close, reason)
                    self.logger.info(f"SELL signal generated at {current_close:.1f} - {reason}")
                    return False
            
            # No signal
            return None
            
        except Exception as e:
            self.logger.error(f"Error in SmartBot calculation: {e}")
            return None

# Create instance
smartbot_agent = SmartBotAgent()
