import numpy as np
import technical_analysis as ta
from agent import Agent

class HFT(Agent):
    def __init__(self, short_period : int = 7, long_period : int = 30, name = "HFT"):
        super().__init__(name)
        self.short_period = short_period
        self.long_period = long_period

    def Calculate(self, data) -> bool | None:
        np_data = np.array(data, dtype=np.float32)

        short_ma = ta.MA(np_data[-self.short_period:])
        long_ma = ta.MA(np_data[-self.long_period:])

        if short_ma > long_ma and self.deal_pos < 1:
            self.deal_pos = 1
            return True
        elif short_ma < long_ma and self.deal_pos > -1:
            self.deal_pos = -1
            return False
        else:
            return None


