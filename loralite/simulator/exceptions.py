class SimException(Exception):
    pass

class NoException(Exception):
    pass

class ClockDriftException(Exception):
    pass

class ClockDriftIssue(Exception):
    node_id: int
    timestamp: int

    def __init__(self, node_id: int, timestamp: int) -> None:
        self.node_id = node_id
        self.timestamp = timestamp

