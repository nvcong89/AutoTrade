import numpy as np
from datetime import datetime
import technical_analysis as ta
from agent import Agent

class rsiAgent(Agent):
    def __init__(self, period : int = 8, name = "RSI"):
        super().__init__(name)
        self.period = period

    def Calculate(self, data) -> bool | None:
        np_data = np.array(data, dtype=np.float32)

        rsi_lastvalue = ta.rsi(np_data[-self.period:],3,True)[-1]

        print(f"{self.name} rsi_lastvalue =  {rsi_lastvalue:.1f} ({datetime.now().strftime("%H:%M %d/%m")})")

        if (rsi_lastvalue <=100 and rsi_lastvalue > 70 ) and self.deal_pos < 1:
            self.deal_pos = 1
            return True
        elif (rsi_lastvalue >= 0 or rsi_lastvalue < 30)  and self.deal_pos > -1:
            self.deal_pos = -1
            return False
        else:
            return None

rsi_agent = rsiAgent(period = 14, name="BOT")
