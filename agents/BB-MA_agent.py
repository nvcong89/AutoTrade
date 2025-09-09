from agent import Agent
from agents import BB_agent, ma_cross_agent

class BB_MA_Agent(Agent):
    def __init__(self, low_thres: float = -1, high_thres: float = 1, window: int = 20, short_period : int = 7, long_period : int = 30, name = "Bot BB-MA"):
        super().__init__(name)
        self.bb_agent = BB_agent.BBAgent(low_thres, high_thres, window)
        self.ma_agent = ma_cross_agent.MACrossAgent(short_period, long_period)

    def Calculate(self, data) -> bool | None:
        bb_result = self.bb_agent.Calculate(data)
        ma_result = self.ma_agent.Calculate(data)

        if bb_result == True and ma_result == True:
            return True
        elif bb_result == False and ma_result == False:
            return False
        else:
            return None

bb_ma_agent = BB_MA_Agent()