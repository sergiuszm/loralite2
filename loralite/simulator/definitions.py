from __future__ import annotations
from enum import Enum
from typing import Literal, Final, TypedDict, Any, TypeAlias, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from loralite.simulator.device import LoRaWANGateway, LoRaWANEndDevice
    from loralite.simulator.node import Node as NodeType
    LoRaWANDeviceType: TypeAlias = LoRaWANGateway | LoRaWANEndDevice
    # INFO: new syntax | doesn't work in that case with mypy (yet)
    DeviceType: TypeAlias = Union[LoRaWANDeviceType, NodeType]
    # DeviceType: TypeAlias = NodeType


class NODE_TYPE(Enum):
    NEW = 1
    JOINING = 2
    CHILD = 3
    TMP_PARENT = 4
    PARENT = 5
    
LWAN_DEV_TYPE = Enum('Dev', 'GW END_DEV')

NETWORK_STATE = Enum('Network', 'UNKNOWN WARMUP DATA_ORIENTED')

# CMD_BEACON: Final = 'B'
# CMD_DISC: Final = 'D'
# CMD_DISC_REPLY: Final = 'DR'
# CMD_DATA_COLLECTION: Final = 'C'
# CMD_DATA_COLLECTION_REPLY: Final = 'CR'
# CMD_JOIN_INFO: Final = 'J'
# CMD_NETWORK_INFO: Final = 'N'
# CMD_NETWORK_INFO_REPLY: Final = 'NR'
# CMD_PARENT_ELECTION: Final = 'E'
# CMD_PARENT_ELECTION_REPLY: Final = 'ER'
# CMD_PARENT_ELECTION_RESULT: Final = 'P'
# ALL_PARENT_PRIMARY_CMD = Literal['B', 'D', 'C', 'N', 'E', 'P']

CMD_BEACON: Final = 0
CMD_DISC: Final = 1
CMD_DISC_REPLY: Final = 2
CMD_DATA_COLLECTION: Final = 3
CMD_DATA_COLLECTION_REPLY: Final = 4
CMD_NETWORK_INFO: Final = 5
CMD_NETWORK_INFO_REPLY: Final = 6
CMD_PARENT_ELECTION: Final = 7
CMD_PARENT_ELECTION_REPLY: Final = 8
CMD_PARENT_ELECTION_RESULT: Final = 9
CMD_JOIN_INFO: Final = 10
ALL_PARENT_PRIMARY_CMD = Literal[0, 1, 3, 5, 7, 9]

# class CMD(Enum):
#     BEACON = CMD_BEACON
#     DISC = CMD_DISC
#     DISC_RESPONSE = CMD_DISC_REPLY
#     COLLECTION = CMD_DATA_COLLECTION
#     COLLECTION_RESPONSE = CMD_DATA_COLLECTION_REPLY
#     NETWORK_INFO = CMD_NETWORK_INFO
#     NETWORK_INFO_RESPONSE = CMD_NETWORK_INFO_REPLY
#     PARENT_ELECTION = CMD_PARENT_ELECTION
#     PARENT_ELECTION_RESPONSE = CMD_PARENT_ELECTION_REPLY
#     PARENT_ELECTION_RESULT = CMD_PARENT_ELECTION_RESULT
#     JOIN_INFO = CMD_JOIN_INFO

class CMD(Enum):
    BEACON = 0
    DISC = 1
    DISC_RESPONSE = 2
    COLLECTION = 3
    COLLECTION_RESPONSE = 4
    NETWORK_INFO = 5
    NETWORK_INFO_RESPONSE = 6
    PARENT_ELECTION = 7
    PARENT_ELECTION_RESPONSE = 8
    PARENT_ELECTION_RESULT = 9
    JOIN_INFO = 10


Packet = TypedDict(
    'Packet',
    {'id': int, 'seq': int, 'cmd': int, 'nr_of_ret': int, 'mm_part': int, 'mm_count': int, 'data': Any, 'crc': int, 'rssi': float},
    total=False
)

BufferedPacket = TypedDict(
    'BufferedPacket',
    {'payload': bytes, 'rx_dbm': float, 't_start': int, 't_end': int, 't_id': int, '_id': int, '_sender_id': int},
    total=False
)

class LoRaLitEFormat(Enum):
    id = 0
    seq = 1
    cmd = 2
    nr_of_ret = 4
    data = 5
    crc = 6

class LoRaWANFormat(Enum):
    ftype = 0
    rfu = 1
    major = 2
    dev_addr = 3
    fctrl = 4
    fcnt = 5
    fopts = 6
    fport = 7
    frmpayload = 8
    mic = 9
    crc = 10

# node/radio state
STATE_ON: Final = 'ON'
STATE_OFF: Final = 'OFF'
STATE_SLEEP: Final = 'SLEEP'
STATE_SIM_END: Final = 'END'
SUBSTATE_NONE: Final = 'NONE'
SUBSTATE_SIM_END: Final = 'END'

# node additional substate - while ON and not IDLE
D_SUBSTATE_OP: Final = 'OP'

# radio additional substate
R_SUBSTATE_RX: Final = 'RX'
R_SUBSTATE_TX: Final = 'TX'

STATE = [STATE_ON, STATE_OFF, STATE_SLEEP]
D_SUBSTATE = [SUBSTATE_NONE, D_SUBSTATE_OP]
R_SUBSTATE = [SUBSTATE_NONE, R_SUBSTATE_RX, R_SUBSTATE_TX]

STATE_TYPE = Literal['state', 'substate', 'radio_state', 'radio_substate']
NODE_STATE = Literal['ON', 'OFF', 'SLEEP', 'END']
NODE_SUBSTATE = Literal['OP', 'NONE', 'END']
RADIO_STATE = Literal['ON', 'OFF', 'SLEEP', 'END']
RADIO_SUBSTATE = Literal['RX', 'TX', 'NONE', 'END']
ALL_STATES = Literal[NODE_STATE, NODE_SUBSTATE, RADIO_STATE, RADIO_SUBSTATE]

class PrevState(TypedDict):
    state: NODE_STATE
    substate: NODE_SUBSTATE
    radio_state: RADIO_STATE
    radio_substate: RADIO_SUBSTATE

WH = 3600
PPM = 1000000

SAMPLE_DATA = 'some_sample_data_used_in_a_simulation_to_fill_up_to_59_bytes_in_a_packet'