from __future__ import annotations
from typing import Callable, Dict, Any, List, TYPE_CHECKING
from sortedcontainers import SortedDict
from loralite.simulator.definitions import NETWORK_STATE
# from loralite.simulator.fake_collision_helper import FakeInTheAir as InTheAir

if TYPE_CHECKING:
    from loralite.simulator.definitions import DeviceType, LoRaWANGateway
    from loralite.simulator.config import ConfigType
    from loralite.simulator.collision_helper import InTheAir

CONFIG: ConfigType
SIU: int = 0
EVENT_LIST: SortedDict = SortedDict()
SIM_TIME: int = 0
LIST_OF_NODES: SortedDict[int, DeviceType] = SortedDict()
LORAWAN_GW: LoRaWANGateway | None = None
CDPPM_SEARCH_RANGE = 1000000
COMMAND_LINE: str = 'python3 -m loralite.simulator.simulator '
OUTPUT_DIR: str = ''
STATE_FILE_COUNT: Dict[int, int] = {}
SAVE_STATE_TO_FILE: bool = False
NR_OF_NODES = 0
LORALITE_STATE = NETWORK_STATE.DATA_ORIENTED
LORALITE_STATE_CHANGED_AT = -1
SIM_DURATION_MS = 0
CRC16: Callable
CRC32: Callable

IN_THE_AIR: Dict[float, InTheAir] = {}
NUMBER_OF_COLLISIONS = 0
NUMBER_OF_PACKETS = 0

SCENARIO = -1
NR_OF_NODES_TO_DISCOVER = -1
ALL_NODES_DISCOVERED_IN = -1
BIGGEST_DISC_RESPONSE = -1
BIGGEST_DISC_REQUEST = -1
BIGGEST_COLL_REQUEST = -1
PE_ELECTION_AT: list[int] = []
PE_FINISHED_AT: list[int] = []

DISCOVERY_STATUS: SortedDict[int, SortedDict[int, List[int]]] = SortedDict()
DISCOVERY_SEQ: SortedDict[int, str] = SortedDict()
