class Agent:
    def __init__(self, name: str):
        self.name = name
        self.deal_pos = 0 # Set agent to have no deal position at start

    def Calculate(self, data) -> bool | None:
        return None
