from typing import Any, Dict, Optional
from loralite.simulator.definitions import *
from json import JSONEncoder, JSONDecoder


class State(object):
    def __init__(
        self,
        node_id: int,
        node_type: NODE_TYPE,
        d_state: NODE_STATE = STATE_SLEEP,
        d_substate: NODE_SUBSTATE = SUBSTATE_NONE,
        r_state: RADIO_STATE = STATE_OFF,
        r_substate: RADIO_SUBSTATE = SUBSTATE_NONE,
        timestamp: int = 0
    ):
        self.state = d_state
        self.substate = d_substate
        self.radio_state = r_state
        self.radio_substate = r_substate
        self._node_id = node_id
        self.node_type = node_type
        self.timestamp = timestamp

    def set_timestamp(self, timestamp: int) -> None:
        self.timestamp = timestamp

    @staticmethod
    def check_state(state: NODE_STATE | RADIO_STATE) -> None:
        if state not in STATE:
            raise RuntimeError(f"Given node state: {state} is not valid!")

    @staticmethod
    def check_node_substate(substate: NODE_SUBSTATE) -> None:
        if substate not in D_SUBSTATE:
            raise RuntimeError(f"Given node substate: {substate} is not valid!")

    @staticmethod
    def check_radio_substate(substate: RADIO_SUBSTATE) -> None:
        if substate not in R_SUBSTATE:
            raise RuntimeError(f"Given radio substate: {substate} is not valid!")

    def __deepcopy__(self, memo: Optional[Dict[int, Any]] = {}) -> Any:
        copy_object = State(
            self._node_id,
            self.node_type,
            self.state,
            self.substate,
            self.radio_state,
            self.radio_substate,
            self.timestamp
        )
        
        return copy_object


class StateEncoder(JSONEncoder):
    def default(self, state: State) -> Any:
        return [
            state._node_id, state.node_type.value, state.state, state.substate, state.radio_state, state.radio_substate, state.timestamp
        ]


class StateDecoder:

    @staticmethod
    def decode(sd: Any) -> State | Dict[int, State]:
        # if 'timestamp' not in sd:
        if isinstance(sd, dict):
            state_list = {}
            for k, v in sd.items():
                state_list[int(k)] = State(
                    v[0],
                    NODE_TYPE(v[1]),
                    v[2],
                    v[3],
                    v[4],
                    v[5],
                    v[6]
                )
            # return {int(k):v for k, v in sd.items()}
            return state_list
        
        return State(
            sd[0],
            NODE_TYPE(sd[1]),
            sd[2],
            sd[3],
            sd[4],
            sd[5],
            sd[6]
        )
