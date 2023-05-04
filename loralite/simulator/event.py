from typing import Callable, Any, Dict, TypeAlias, Union
import loralite.simulator.globals as coglobs
import threading

def add_event(node_id: int, timestamp: int, f: Callable, *args: Any, **kwargs: Dict[str, Any]) -> None:
    if timestamp >= coglobs.SIM_DURATION_MS:
        return
    
    if timestamp not in coglobs.EVENT_LIST:
        coglobs.EVENT_LIST[timestamp] = []

    event = EventUnit(node_id, timestamp, f, *args, **kwargs)
    coglobs.EVENT_LIST[timestamp].append(event)


def add_new_node_event(timestamp: int, f: Callable, *args: Any, **kwargs: Dict[str, Any]) -> None:
    if timestamp >= coglobs.SIM_DURATION_MS:
        return
    
    if timestamp not in coglobs.EVENT_LIST:
        coglobs.EVENT_LIST[timestamp] = []

    event = NewNodeEventUnit(timestamp, f, *args, **kwargs)
    coglobs.EVENT_LIST[timestamp].append(event)

def add_detached_event(timestamp: int, f: Callable, *args: Any, **kwargs: Dict[str, Any]) -> None:
    if timestamp >= coglobs.SIM_DURATION_MS:
        return
    
    if timestamp not in coglobs.EVENT_LIST:
        coglobs.EVENT_LIST[timestamp] = []

    event = DetachedEventUnit(timestamp, f, *args, **kwargs)
    coglobs.EVENT_LIST[timestamp].append(event)


class EventUnit:
    def __init__(self, node_id: int, timestamp: int, f: Callable, *args: Any, **kwargs: Dict[str, Any]):
        self.node_id = node_id
        self.timestamp = timestamp
        self.func = f
        self.func_name = f.__name__
        self.args = args
        self.kwargs = kwargs
        self.expired = False

    def execute(self) -> None:
        coglobs.SIM_TIME = self.timestamp
        coglobs.LIST_OF_NODES[self.node_id].timestamp = coglobs.SIM_TIME
        coglobs.LIST_OF_NODES[self.node_id].current_event_timestamp = coglobs.SIM_TIME
        self.func(*self.args, **self.kwargs)
        coglobs.LIST_OF_NODES[self.node_id].previous_event_timestamp = coglobs.SIM_TIME


class NewNodeEventUnit:
    def __init__(self, timestamp: int, f: Callable, *args: Any, **kwargs: Dict[str, Any]):
        self.timestamp = timestamp
        self.func = f
        self.func_name = f.__name__
        self.args = args
        self.kwargs = kwargs
        self.expired = False

    def execute(self) -> None:
        node = self.func(*self.args, **self.kwargs)
        node.child_config['first_op_at_ms'] = 0
        coglobs.LIST_OF_NODES[node.id] = node
        coglobs.SIM_TIME = self.timestamp

class DetachedEventUnit:
    def __init__(self, timestamp: int, f: Callable, *args: Any, **kwargs: Dict[str, Any]):
        self.timestamp = timestamp
        self.func = f
        self.func_name = f.__name__
        self.args = args
        self.kwargs = kwargs
        self.expired = False

    def execute(self) -> None:
        self.func(*self.args, **self.kwargs)


def end_simulation(timestamp: int) -> None:
    coglobs.SIM_DURATION_MS = timestamp
    coglobs.SIM_TIME = timestamp

