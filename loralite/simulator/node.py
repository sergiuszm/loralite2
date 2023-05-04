from __future__ import annotations
from platform import node
# from distutils import log
import loralite.simulator.globals as coglobs
from loralite.simulator.lora_phy import (
    LORALITE_HEADER_SIZE,
    TDMA_SIZE,
    BA_SIZE,
    PE_CT_SIZE,
    PE_SIZE,
    I_SIZE,
    LoraBand,
    LORA_MAIN_BAND,
    LORA_SECONDARY_BAND,
    SF_12,
    TX_PARAMS,
    RX_SENSITIVITY
)
from loralite.simulator.state import State, StateEncoder
from copy import deepcopy
from loralite.simulator.event import add_detached_event, add_event, end_simulation
from loralite.simulator.logger import logger
from loralite.simulator.definitions import *
from loralite.simulator.propagation_loss_model import PROPAGATION_MODEL
from loralite.simulator.propagation_delay_model import DELAY_MODEL
from loralite.simulator.utils import *
from loralite.simulator.toa import TOA
from loralite.simulator.packet_loss_helper import make_decision_based_on_modulo, make_decition_based_on_probability
import math
from loralite.simulator.mobility import get_distance
from loralite.simulator.exceptions import ClockDriftIssue, SimException, ClockDriftException
from loralite.simulator.energy import Energy, EnergyAlt
from random import randint
# from string import ascii_uppercase
from typing import Dict, Callable, TypedDict, Tuple, Optional
from sortedcontainers import SortedDict, SortedList
import json
import struct


class NodeConfig(TypedDict):
    switch_on_ms: int
    switch_off_ms: int
    wait_for_all_network_info_slots: bool
    backoff_s: int

class ParentConfig(TypedDict):
    first_op_at_ms: int
    send_interval_s: int
    network_info_send_interval_s: int
    max_send_interval_s: int
    secondary_schedule: bool
    join_beacon_interval_ms: int
    join_beacon_after_ms: int
    random_t_before_becoming_tmp_parent: bool
    t_before_becoming_tmp_parent: int

class ParentRuntimeParams(TypedDict):
    last_cmd: int|None
    last_b_cmd_at: int
    list_of_nodes: list[int]
    unknown_nodes_left: list[int]
    unknown_nodes_parts: Dict[int, list[int]]
    unknown_nodes_per_disc: int
    # unknown_nodes_only: bool
    expected_network_size: int
    disc_cmd_order: list[int]
    collect_cmd_order: list[int]
    network_info_cmd_order: list[int]
    election_cmd_order: list[int]
    receive_window: Dict[Literal['start', 'end'], int]
    recv_count: int
    expected_recv_count: int
    total_expected_recv_count: int
    join_beacon_sent_at: int
    join_beacons_sent: int
    send_interval_s: int
    network_state: NETWORK_STATE
    network_state_changed_at: int
    repeat_last_cmd: bool
    missing_responses_count: Dict[int, int]
    missing_responses_from_all_count: int

class ChildConfig(TypedDict):
    first_op_at_ms: int
    wait_before_ms: int
    guard_time_ms: int
    op_duration_ms: int
    sleep_before_sending: int

class ChildRuntimeParams(TypedDict):
    wait_before_ms: int
    guard_time_ms: int
    last_pkt_rec_at: int
    last_pkt_from_parent_rec_at: int
    missing_pkts: int
    sbs_phase: bool
    receive_window: Dict[Literal['end'], int]
    is_backup_parent_node: bool
    backup_parent_node_index: int

class NewNodeRuntimeParams(TypedDict):
    first_pkt_rec_at: int
    second_pkt_rec_at: int
    deployed_at: int
    new_node_until: int
    joining_node_from: int
    joining_node_until: int
    tmp_parent_from: int
    tmp_parent_node_until: int

class NodeRuntimeParams(TypedDict):
    packets_sent: int
    packets_received: int
    sent_pkt_seq: int
    total_pkt_seq: int
    received_pkt: BufferedPacket
    received_pkt_payload: Packet
    sent_pkt: BufferedPacket
    sent_pkt_payload: Packet
    nr_of_ret: int
    bytes_sent: int
    bytes_received: int
    neighbor_node_discovered_after: SortedList[int]
    avg_time_between_neighbor_node_discovery: int
    time_since_last_discovered_node: int
    last_discovered_node_at: int
    parent_election_at: int
    parent_node: int
    backup_parent_nodes: list[int]
    preparing_for_sleep: bool
    backoff_s: int

class SimulationParams(TypedDict):
    plm: int
    plm_res: int
    plp: float
    pkts_to_lose: int
    pkts_from_pn: bool
    pkts_from_nodes: list[int]
    pkts_starting_seq: int
    selected_for_pl: bool
    based_on_modulo: bool
    based_on_probability: bool
    received_count: int
    should_receive_count: int
    expected_to_receive_count: int
    lost_due_to_pls: int

class BackhaulType(TypedDict):
    access_at: SortedList[int]
    last_access_at: int
    avg_time_between_accesses: int

KnownNodes = TypedDict(
    'KnownNodes',
    {'rssi': float, 'backhaul': bool, 'last_seen': int, 'known_nodes': list[int], 'is_active': bool},
    total=False
)

PE_RESPONSE_FORMAT = '000#00000#000'

class NodeStats:
    @staticmethod
    def check_if_all_nodes_are_discovered(timestamp: int, data: bytes, p_id: int) -> bool:
        if coglobs.ALL_NODES_DISCOVERED_IN > -1:
            return True

        id_pack = data[-2:]
        id_list = Node._create_tdma_list(id_pack[0], id_pack[1], p_id)
        discovery_seq = Node._shorten_ids(','.join([str(id) for id in id_list]))
        coglobs.DISCOVERY_SEQ[str(timestamp)] = discovery_seq

        if timestamp not in coglobs.DISCOVERY_STATUS:
            coglobs.DISCOVERY_STATUS[timestamp] = SortedDict()

        all_discovered = True
        erliest_deployed_node = 999999999
        for id in coglobs.LIST_OF_NODES:
            node: Node = coglobs.LIST_OF_NODES[id]

            known_nodes = [x for x in node.known_nodes]
            coglobs.DISCOVERY_STATUS[timestamp][id] = known_nodes
            logger.info(coglobs.SIM_TIME, f'[node_{id}][known nodes (of {coglobs.NR_OF_NODES_TO_DISCOVER})]: {known_nodes}({len(known_nodes)})')

            if node.known_nodes.__len__() == coglobs.NR_OF_NODES_TO_DISCOVER:
                if node.new_node_runtime_params['deployed_at'] < erliest_deployed_node:
                    erliest_deployed_node = node.new_node_runtime_params['deployed_at']
                continue

            all_discovered = False

        if not all_discovered:
            return False

        coglobs.ALL_NODES_DISCOVERED_IN = timestamp - erliest_deployed_node

        if coglobs.CONFIG['general']['quit_on_neighborhood_mapping_complete']:
            sim_end_ts = timestamp + 1
            add_detached_event(sim_end_ts, end_simulation, sim_end_ts)

        return True

class Node:
    def __init__(self, nr: int, position: list[int], type: NODE_TYPE, timestamp: int = 0, starting_schedule_f: str = '_setup_starting_schedule'):
        coglobs.NR_OF_NODES += 1
        self.id = nr
        self.type = type
        self.position = position
        self.state = State(self.id, self.type, timestamp=timestamp)
        self.state_table: Dict[int, State] = {}
        self.lora_band = LoraBand(LORA_MAIN_BAND, SF_12)
        self.next_transmission_time = {LORA_MAIN_BAND: 0, LORA_SECONDARY_BAND: 0}
        self.transmission_allowed_at = {LORA_MAIN_BAND: 0, LORA_SECONDARY_BAND: 0}
        self.next_expected_transmission_time = 0.0
        self.receive_buff: list[BufferedPacket] = []
        self.timestamp = timestamp
        self.next_wakeup_time = 0
        self.packet_schedule: Dict[int, Packet] = {}
        self.packet_delay = 0
        self.sync = 0
        self.d = 0
        self.dc = 0
        self.ni = 0
        self.nir = 0
        self.pe = 0
        self.per = 0
        self.dc_bytes_sent = 0
        self.transmission_interval = 0 if self.type is not NODE_TYPE.PARENT else (coglobs.CONFIG['parent']['send_interval_s'] * coglobs.SIU)
        self.cd_negative = get_random_true_false()
        self.clock_drift_total = 0
        self.clock_drift = coglobs.CONFIG['general']['cdppm']
        self.clock_drift_timestamp_modifier = coglobs.CONFIG['general']['cdppm'] - 1 + 3 * 60 * 1000 #3 minutes later
        self.clock_drift_modified_at = 0
        self.detect_preamble_ms = math.ceil(TOA.get_symbols_time() * coglobs.SIU) #5 symbols required to detect the preamble
        self.rx_active = False
        self.rx_active_since = 0
        self.current_event_timestamp = 0
        self.last_event_timestamp = 0
        self.previous_event_timestamp = 0
        self.known_nodes: SortedDict[int, KnownNodes] = SortedDict()
        self.elected_nodes: SortedDict[int, int] = SortedDict()
        self.backhaul_access: BackhaulType = {'access_at': SortedList(), 'avg_time_between_accesses': -1, 'last_access_at': -1}
        
        self.config: NodeConfig = {
            'switch_on_ms': coglobs.CONFIG['node']['sch_on_duration_ms'],    # how long in s it takes to turn on node
            'switch_off_ms': coglobs.CONFIG['node']['sch_off_duration_ms'],   # how long in s it takes to turn off node
            'wait_for_all_network_info_slots': True,
            'backoff_s': coglobs.CONFIG['node']['backoff_s']
        }

        self.parent_config: ParentConfig = {
            'first_op_at_ms': coglobs.CONFIG['parent']['first_op_at_s'] * coglobs.SIU,
            'send_interval_s': coglobs.CONFIG['parent']['send_interval_s'],
            'network_info_send_interval_s': coglobs.CONFIG['parent']['network_info_send_interval_s'],
            'max_send_interval_s': coglobs.CONFIG['parent']['max_send_interval_s'],
            'secondary_schedule': coglobs.CONFIG['parent']['secondary_schedule'],
            'join_beacon_interval_ms': coglobs.CONFIG['parent']['join_beacon_interval_s'] * coglobs.SIU,
            'join_beacon_after_ms': coglobs.CONFIG['parent']['join_beacon_after_s'] * coglobs.SIU,
            'random_t_before_becoming_tmp_parent': coglobs.CONFIG['parent']['random_t_before_becoming_tmp_parent'],
            't_before_becoming_tmp_parent': coglobs.CONFIG['parent']['t_before_becoming_tmp_parent'],
        }

        self.parent_runtime_params: ParentRuntimeParams = {
            'last_cmd': None,
            'last_b_cmd_at': -1,
            'list_of_nodes': [],
            'unknown_nodes_parts': {},
            'unknown_nodes_left': [],
            'unknown_nodes_per_disc': -1,
            # 'unknown_nodes_only': coglobs.CONFIG['parent']['unknown_nodes_only'],
            'expected_network_size': coglobs.CONFIG['general']['number_of_expected_nodes'],
            'disc_cmd_order': [],
            'collect_cmd_order': [],
            'network_info_cmd_order': [],
            'election_cmd_order': [],
            'receive_window': {'start': 0, 'end': 0},
            'recv_count': 0,
            'expected_recv_count': 0,
            'total_expected_recv_count': 0,
            'join_beacon_sent_at': 0,
            'join_beacons_sent': 0,
            'send_interval_s': coglobs.CONFIG['parent']['send_interval_s'],
            'network_state': NETWORK_STATE.UNKNOWN,
            'network_state_changed_at': -1,
            'repeat_last_cmd': False,
            'missing_responses_count': {},
            'missing_responses_from_all_count' : 0
        }

        self.child_config: ChildConfig = {
            'first_op_at_ms': coglobs.CONFIG['child']['first_op_at_s'] * coglobs.SIU,
            'wait_before_ms': math.ceil(coglobs.CONFIG['child']['guard_time_ms'] / 2),
            'guard_time_ms': coglobs.CONFIG['child']['guard_time_ms'],
            'op_duration_ms': coglobs.CONFIG['child']['op_duration_ms'],
            'sleep_before_sending': coglobs.CONFIG['child']['sleep_before_slot']
        }

        self.child_runtime_params: ChildRuntimeParams = {
            'last_pkt_rec_at': 0,
            'last_pkt_from_parent_rec_at': 0,
            'missing_pkts': 0,
            'sbs_phase': False,
            'receive_window': {'end': 0},
            'backup_parent_node_index': -1,
            'is_backup_parent_node': False,
            'wait_before_ms': self.child_config['wait_before_ms'],
            'guard_time_ms': self.child_config['guard_time_ms'] 
        }

        self.new_node_runtime_params: NewNodeRuntimeParams = {
            'first_pkt_rec_at' : -1,
            'second_pkt_rec_at': -1,
            'deployed_at': -1,
            'new_node_until': -1,
            'joining_node_until': -1,
            'joining_node_from': -1,
            'tmp_parent_from': -1,
            'tmp_parent_node_until': -1,
        }
        
        self.node_runtime_params: NodeRuntimeParams = {
            'packets_sent': 0,
            'packets_received': 0,
            'sent_pkt_seq': -1,
            'total_pkt_seq': -1,
            'bytes_sent': 0,
            'bytes_received': 0,
            'received_pkt': {},
            'received_pkt_payload': {},
            'sent_pkt': {},
            'sent_pkt_payload': {},
            'nr_of_ret': -1,
            'neighbor_node_discovered_after': SortedList(),
            'avg_time_between_neighbor_node_discovery': -1,
            'time_since_last_discovered_node': -1,
            'last_discovered_node_at': -1,
            'parent_election_at': -1,
            'parent_node': -1,
            'backup_parent_nodes': [],
            'preparing_for_sleep': False,
            'backoff_s': 0
        }

        self.simulation_params: SimulationParams = {
            'plm': -1,
            'plm_res': -1,
            'plp': 0.0,
            'pkts_to_lose': 0,
            'pkts_starting_seq': -1,
            'pkts_from_pn': False,
            'pkts_from_nodes': [],
            'selected_for_pl': False,
            'based_on_modulo': False,
            'based_on_probability': False,
            'should_receive_count': 0,
            'expected_to_receive_count': 0,
            'received_count': 0,
            'lost_due_to_pls': 0
        }

        self.energy = EnergyAlt()
        node_energy = coglobs.CONFIG['energy']['node']
        radio_energy = coglobs.CONFIG['energy']['radio']

        energy_parent = Energy(
            node_energy[coglobs.CONFIG['parent']['platform']],
            radio_energy[coglobs.CONFIG['parent']['radio_type']],
            coglobs.CONFIG['energy']['v_load_drop']
        )

        energy_child = Energy(
            node_energy[coglobs.CONFIG['child']['platform']],
            radio_energy[coglobs.CONFIG['child']['radio_type']],
            coglobs.CONFIG['energy']['v_load_drop']
        )

        self.energy.add_energy(NODE_TYPE.NEW, energy_child)
        self.energy.add_energy(NODE_TYPE.JOINING, energy_child)
        self.energy.add_energy(NODE_TYPE.CHILD, energy_child)
        self.energy.add_energy(NODE_TYPE.TMP_PARENT, energy_parent)
        self.energy.add_energy(NODE_TYPE.PARENT, energy_parent)

        self.initial_state = deepcopy(self.state)

        # saving initial node state
        self._save_state()
        # scheduling an event at timestamp 0 that will print basic information about the Node
        add_event(self.id, self.timestamp, self._info)
        starting_f = getattr(self, starting_schedule_f)
        add_event(self.id, self.timestamp, starting_f)

    def _setup_starting_schedule(self) -> None:

        if len(self.known_nodes) == 0:
            for id1 in coglobs.LIST_OF_NODES:
                if id1 == self.id:
                    continue
                self.known_nodes[id1] = {'rssi': -1.0, 'last_seen': -1, 'backhaul': False, 'known_nodes': [], 'is_active': True}
                for id2 in coglobs.LIST_OF_NODES:
                    if id2 == id1:
                        continue
                    self.known_nodes[id1]['known_nodes'].append(id2)
                
                self.known_nodes[id1]['known_nodes'].sort()

        match self.type:
            case NODE_TYPE.PARENT:
                add_event(self.id, self.timestamp + self.parent_config['first_op_at_ms'] + self.config['switch_on_ms'], self._change_node_state, STATE_ON)   
                add_event(self.id, self.timestamp + self.parent_config['first_op_at_ms'] + self.config['switch_on_ms'], self._change_radio_state, STATE_ON)
                add_event(self.id, self.timestamp + self.parent_config['first_op_at_ms'] + self.config['switch_on_ms'], self._execute_packet_schedule)
                self.parent_runtime_params['network_state'] = coglobs.LORALITE_STATE
                if len(self.parent_runtime_params['list_of_nodes']) == 0:
                    for id in coglobs.LIST_OF_NODES:
                        node = coglobs.LIST_OF_NODES[id] 
                        match node.type:
                            case NODE_TYPE.NEW:
                                continue
                            case NODE_TYPE.PARENT:
                                continue
                            case NODE_TYPE.CHILD:
                                self.parent_runtime_params['list_of_nodes'].append(node.id)
            case NODE_TYPE.CHILD:
                add_event(self.id, self.timestamp + self.child_config['first_op_at_ms'] + self.config['switch_on_ms'], self._change_node_state, STATE_ON, SUBSTATE_NONE)
                add_event(self.id, self.timestamp + self.child_config['first_op_at_ms'] + self.config['switch_on_ms'], self._change_radio_state, STATE_ON, R_SUBSTATE_RX)
                self.node_runtime_params['parent_node'] = 0
            case NODE_TYPE.NEW:
                add_event(self.id, self.timestamp + self.child_config['first_op_at_ms'] + self.config['switch_on_ms'], self._change_node_state, STATE_ON, SUBSTATE_NONE)
                add_event(self.id, self.timestamp + self.child_config['first_op_at_ms'] + self.config['switch_on_ms'], self._change_radio_state, STATE_ON, R_SUBSTATE_RX)
                self.new_node_runtime_params['deployed_at'] = self.timestamp

    def _starting_schedule_scenario_3a(self) -> None:
        add_event(self.id, self.timestamp + self.config['switch_on_ms'], self._change_node_state, STATE_ON, SUBSTATE_NONE)
        add_event(self.id, self.timestamp + self.config['switch_on_ms'], self._change_radio_state, STATE_ON, R_SUBSTATE_RX)
        self.new_node_runtime_params['deployed_at'] = self.timestamp
        packet = self._prepare_network_info_packet(0, True)
        add_event(self.id, self.timestamp + 200, self._send, packet)

    def _starting_schedule_scenario_3b(self) -> None:
        add_event(self.id, self.timestamp + self.config['switch_on_ms'], self._change_node_state, STATE_ON, SUBSTATE_NONE)
        add_event(self.id, self.timestamp + self.config['switch_on_ms'], self._change_radio_state, STATE_ON, R_SUBSTATE_RX)
        self.new_node_runtime_params['deployed_at'] = self.timestamp

    def _starting_schedule_scenario_ge_4(self) -> None:
        add_event(self.id, self.timestamp + self.config['switch_on_ms'], self._change_node_state, STATE_ON, SUBSTATE_NONE)
        add_event(self.id, self.timestamp + self.config['switch_on_ms'], self._change_radio_state, STATE_ON, R_SUBSTATE_RX)
        is_network_detected_ts = self.timestamp + self.config['switch_on_ms'] + (coglobs.CONFIG['scenarios']['scenario_ge_4']['network_detection_multipler'] * self.parent_config['max_send_interval_s'] * coglobs.SIU)
        add_event(self.id, is_network_detected_ts, self._is_network_detected)
        self.new_node_runtime_params['deployed_at'] = self.timestamp
        self.parent_runtime_params['network_state'] = NETWORK_STATE.UNKNOWN
        if coglobs.SCENARIO == 5:
            self.config['wait_for_all_network_info_slots'] = False

    def _get_active_nodes(self) -> list[int]:
        if len(self.known_nodes.keys()) == 0:
            return []

        return [node_id for node_id in self.known_nodes.keys() if self.known_nodes[node_id]['is_active']]

    def _perform_clock_drift(self) -> None:
        coglobs.CDPPM_SEARCH_RANGE = self.transmission_interval
        search_range_start = self.timestamp + 1
        search_range_end = self.timestamp + coglobs.CONFIG['general']['cdppm'] + coglobs.CDPPM_SEARCH_RANGE

        # no clock drift if node is already awake
        if self.state.state == STATE_ON:
            next_clock_drift = self.timestamp - self.clock_drift_timestamp_modifier
            logger.info(self.timestamp, f'{bcolors.LIGHT_GRAY}[node_{self.id}] is ON. Clock drift moved to {format_ms(next_clock_drift, coglobs.SIU)}{bcolors.ENDC}')
            add_event(self.id, next_clock_drift, self._perform_clock_drift)
            raise ClockDriftIssue(self.id, self.timestamp)

        drift_direction = ''
        drift_sign = 1
        clock_drift = 0
        
        match self.cd_negative:
            case True:
                drift_sign = -1
            case False:
                drift_direction = '+'

        event_list_slice = coglobs.EVENT_LIST.irange(search_range_start, search_range_end)
        logger.info(self.timestamp, f'{bcolors.LIGHT_GRAY}[node_{self.id}] Clock drift search range: {format_ms(search_range_start, coglobs.SIU)} --> {format_ms(search_range_end, coglobs.SIU)}{bcolors.ENDC}')
        tmp_event_list = SortedDict()
        event_list_index: Dict[int, list[int]] = {}
        for timestamp in event_list_slice:
            time_to_next_event = timestamp - self.previous_event_timestamp
            clock_drift = math.ceil(time_to_next_event * self.clock_drift / PPM) * drift_sign
            for event in coglobs.EVENT_LIST[timestamp]:
                if getattr(event, "node_id", None) is None:
                    continue
                drifted_timestamp = timestamp + clock_drift
                if event.node_id == self.id:
                    if drifted_timestamp not in tmp_event_list:
                        tmp_event_list[drifted_timestamp] = []
                    event.timestamp = drifted_timestamp
                    logger.info(self.timestamp, f'{bcolors.LIGHT_GRAY}[node_{self.id}][{self.clock_drift}ppm][{drift_direction}{clock_drift}ms][{format_ms(timestamp, coglobs.SIU)} -> {format_ms(drifted_timestamp, coglobs.SIU)}]: event({event.func_name}, [{event.args}][{event.kwargs}]){bcolors.ENDC}')
                    tmp_event_list[drifted_timestamp].append(event)
                    if timestamp not in event_list_index:
                        event_list_index[timestamp] = []
                    event_list_index[timestamp].append(coglobs.EVENT_LIST[timestamp].index(event))
            
        for timestamp in event_list_index:
            event_list: list = coglobs.EVENT_LIST.pop(timestamp)
            event_to_remain = []
            for event in event_list:
                if event_list.index(event) not in event_list_index[timestamp]:
                    event_to_remain.append(event)
            
            if len(event_to_remain) > 0:
                coglobs.EVENT_LIST[timestamp] = event_to_remain

        for timestamp in tmp_event_list:
            if timestamp not in coglobs.EVENT_LIST:
                coglobs.EVENT_LIST[timestamp] = []

            for event in tmp_event_list[timestamp]:
                coglobs.EVENT_LIST[timestamp].append(event)

        self.clock_drift_total += self.clock_drift
        # add_event(self.id, self.timestamp + 1000000 - coglobs.CONFIG['general']['cdppm'] - 1, self._perform_clock_drift)

    def _change_node_type(self, type: NODE_TYPE) -> None:
        if self.type == type:
            return

        if not isinstance(type, NODE_TYPE):
            raise SimException('Given node type: {type} is not correct!')

        if self.type == NODE_TYPE.NEW:
            self.new_node_runtime_params['new_node_until'] = self.timestamp
            if type == NODE_TYPE.JOINING:
                self.new_node_runtime_params['joining_node_from'] = self.timestamp
            elif type == NODE_TYPE.TMP_PARENT:
                self.new_node_runtime_params['tmp_parent_from'] = self.timestamp

        if self.type == NODE_TYPE.JOINING:
            self.new_node_runtime_params['joining_node_until'] = self.timestamp

        if self.type == NODE_TYPE.TMP_PARENT:
            self.new_node_runtime_params['tmp_parent_node_until'] = self.timestamp

        logger.info(self.timestamp, f'{bcolors.YELLOW_MAGNETA}[node_{self.id}]: {self.type} -> {type}{bcolors.ENDC}')

        self.type = type
        self._save_state()
        self.state.node_type = type

    def _save_state(self, last: bool = False) -> None:
        # if self.state.node_type not in self.state_table:
        #     self.state_table[self.state.node_type] = {}
        if not last:
            self.state_table[self.state.timestamp] = deepcopy(self.state)
        if coglobs.SAVE_STATE_TO_FILE and (len(self.state_table) >= 10000 or (last and len(self.state_table) > 0)):
            if self.id not in coglobs.STATE_FILE_COUNT:
                coglobs.STATE_FILE_COUNT[self.id] = 0
            with open(f'{coglobs.OUTPUT_DIR}/state/{self.id}_{coglobs.STATE_FILE_COUNT[self.id]}', "a", encoding='utf-8') as outfile:
                # encoded = jsonpickle.encode(self.state_table, unpicklable=True, keys=True)
                outfile.write(json.dumps(self.state_table, cls=StateEncoder))
            
            coglobs.STATE_FILE_COUNT[self.id] += 1
            self.state_table = {}

        logger.debug(
            self.state.timestamp,
            f'SAVING STATE. d_state: {self.state.state}, '
            f'd_substate: {self.state.substate}, '
            f'r_state: {self.state.radio_state}, '
            f'r_substate: {self.state.radio_substate}'
        )

    def _change_node_state(self, state: NODE_STATE, substate: NODE_SUBSTATE | None = None) -> None:
        State.check_state(state)
        # no changes to the current state
        if self.state.state == state and \
                self.state.substate == substate and \
                self.type == self.state.node_type:
            return

        if self.type == NODE_TYPE.CHILD and state == STATE_ON and substate == SUBSTATE_NONE:
            if not self.child_runtime_params['sbs_phase']:
                self.simulation_params['should_receive_count'] += 1
            next_schedule_timestamp = math.floor(self.next_expected_transmission_time - self.child_runtime_params['wait_before_ms'])
            wait_time_ms = self.child_runtime_params['guard_time_ms'] + self.detect_preamble_ms
            if self.child_runtime_params['is_backup_parent_node']:
                max_toa_ms = math.ceil(TOA.get_time_on_air(coglobs.CONFIG['lora']['payload_size']) * coglobs.SIU)
                # add_event(self.id, next_schedule_timestamp + self.child_runtime_params['guard_time_ms'] + 2 * max_toa_ms, self.__check_if_received_from_parent, self.child_runtime_params['guard_time_ms'] + 2 * max_toa_ms)
                wait_time_ms = self.child_runtime_params['guard_time_ms'] + 2 * max_toa_ms
            add_event(self.id, next_schedule_timestamp + self.child_runtime_params['guard_time_ms'] + self.detect_preamble_ms, self.__check_if_received_from_parent, wait_time_ms)

        old_state = self.state.state
        self.state.state = state
        self.state.set_timestamp(self.timestamp)

        if substate is not None:
            State.check_node_substate(substate)
            old_substate = self.state.substate
            self.state.substate = substate
            logger.info(
                self.timestamp, 
                f'node_{self.id} node state: {old_state} => {state}, '
                f'substate: {old_substate} => {substate}')

        if substate is None:
            logger.info(
                self.timestamp, 
                f'node_{self.id} node state: {old_state} => {state}, '
                f'substate: {self.state.substate}')

        if state == STATE_ON:
            self.node_runtime_params['preparing_for_sleep'] = False

        if state == STATE_SLEEP and not self.child_runtime_params['sbs_phase']:
            if coglobs.CONFIG['general']['perform_clock_drift']:
                add_event(self.id, self.timestamp + 1, self._perform_clock_drift)

        self._save_state()

    def _change_radio_state(self, state: RADIO_STATE, substate: RADIO_SUBSTATE | None = None) -> None:
        State.check_state(state)
        # no changes to the current state
        if self.state.radio_state == state and self.state.radio_substate == substate and self.type == self.state.node_type:
            return

        old_state = self.state.radio_state
        self.state.radio_state = state
        self.state.set_timestamp(self.timestamp)

        if substate is not None:
            State.check_radio_substate(substate)
            old_substate = self.state.radio_substate
            self.state.radio_substate = substate
            logger.info(self.timestamp, f'node_{self.id} radio state: {old_state} => {state}, substate: {old_substate} => {substate}')

        if substate is None:
            logger.info(self.timestamp, f'node_{self.id} radio state: {old_state} => {state}, substate: {self.state.substate}')

        if self.type is not NODE_TYPE.NEW and state is STATE_OFF and substate is SUBSTATE_NONE:
            self._change_radio_band(LORA_MAIN_BAND, SF_12)

        self._save_state()

    def _change_radio_band(self, band: float, sf: int) -> None:
        if self.lora_band.band == band:
            return
        logger.info(self.timestamp, f'node_{self.id} freq band change: {self.lora_band.band} MHz => {band} MHz')
        self.lora_band = LoraBand(band, sf)

    def _set_optimal_receive_windows(self, number_of_nodes: int = 0) -> None:
        number_of_child_nodes = number_of_nodes if number_of_nodes > 0 else len(self.parent_runtime_params['list_of_nodes'])
        toa_c_ms = math.ceil(TOA.get_time_on_air(coglobs.CONFIG['lora']['payload_size']) * coglobs.SIU)
        bitmap_size = int(len(Node._convert_ids_to_bitmap([], self.parent_runtime_params['expected_network_size'])) / 8)
        disc_req_size = LORALITE_HEADER_SIZE + coglobs.CONFIG['lora']['crc_bytes'] + BA_SIZE + bitmap_size
        toa_disc_ms = math.ceil(TOA.get_time_on_air(disc_req_size) * coglobs.SIU)
        ni_req_size = LORALITE_HEADER_SIZE + coglobs.CONFIG['lora']['crc_bytes'] + BA_SIZE + bitmap_size
        toa_niw_ms = math.ceil(TOA.get_time_on_air(ni_req_size) * coglobs.SIU)
        pe_resp_size = LORALITE_HEADER_SIZE + coglobs.CONFIG['lora']['crc_bytes'] + PE_CT_SIZE + PE_SIZE
        toa_pe_ms = math.ceil(TOA.get_time_on_air(pe_resp_size) * coglobs.SIU)
        rec_cw_s = math.ceil((toa_c_ms + coglobs.CONFIG['child']['reply_gt_ms'] + coglobs.CONFIG['radio']['mode_change_ms']) * number_of_child_nodes / coglobs.SIU)
        rec_dw_s = math.ceil((toa_disc_ms + coglobs.CONFIG['child']['reply_gt_ms'] + coglobs.CONFIG['radio']['mode_change_ms']) * number_of_child_nodes / coglobs.SIU)
        rec_niw_s = math.ceil((toa_niw_ms + coglobs.CONFIG['child']['reply_gt_ms'] + coglobs.CONFIG['radio']['mode_change_ms']) * number_of_child_nodes / coglobs.SIU)
        rec_pe_s = math.ceil((toa_pe_ms + coglobs.CONFIG['child']['reply_gt_ms'] + coglobs.CONFIG['radio']['mode_change_ms']) * number_of_child_nodes / coglobs.SIU)
        # rec_cw_s = math.ceil((toa_c_ms + coglobs.CONFIG['child']['reply_gt_ms'] + coglobs.CONFIG['radio']['mode_change_ms']) * (number_of_child_nodes + 1) / coglobs.SIU)
        # rec_dw_s = math.ceil((toa_disc_ms + coglobs.CONFIG['child']['reply_gt_ms'] + coglobs.CONFIG['radio']['mode_change_ms']) * (number_of_child_nodes + 1) / coglobs.SIU)
        # rec_niw_s = math.ceil((toa_niw_ms + coglobs.CONFIG['child']['reply_gt_ms'] + coglobs.CONFIG['radio']['mode_change_ms']) * (number_of_child_nodes + 1) / coglobs.SIU)
        # rec_pe_s = math.ceil((toa_pe_ms + coglobs.CONFIG['child']['reply_gt_ms'] + coglobs.CONFIG['radio']['mode_change_ms']) * (number_of_child_nodes + 1) / coglobs.SIU)
        coglobs.CONFIG['parent']['collect_window_s'] = rec_cw_s
        coglobs.CONFIG['parent']['disc_window_s'] = rec_dw_s
        coglobs.CONFIG['parent']['network_info_window_s'] = rec_niw_s
        coglobs.CONFIG['parent']['parent_election_window_s'] = rec_pe_s

    def _scheduled_log(self, log_func: Callable, msg: str) -> None:
        log_func(self.timestamp, msg)

    def _info(self) -> None:
        logger.info(
            coglobs.SIM_TIME,
            f'node_{self.id}, \tTYPE:{self.type}, \tSTATE: {self.state.state}, '
            f'\tRADIO_STATE: {self.state.radio_state}, \tPOSITION: {self.position}'
        )

    def _prepare_packet(self, pkt_seq: int, cmd: int, nr_of_ret: int, mm_part: int, mm_count: int, data: Any) -> Packet:
        return {'seq': pkt_seq, 'cmd': cmd, 'nr_of_ret': nr_of_ret, 'mm_part': mm_part, 'mm_count': mm_count, 'data': data}

    def _pack_packet(self, packet: Packet) -> bytes:
        nr_of_ret = bits_little_endian_from_bytes(packet['nr_of_ret'].to_bytes(1, byteorder='little'))[:2]
        mm_part = bits_little_endian_from_bytes(packet['mm_part'].to_bytes(1, byteorder='little'))[:3]
        mm_count = bits_little_endian_from_bytes(packet['mm_count'].to_bytes(1, byteorder='little'))[:3]
        opts = bytes_from_bits_little_endian(nr_of_ret + mm_part + mm_count)

        data = packet['data']
        packet_payload = struct.pack(f'<BHBs{len(packet["data"])}s', self.id, packet['seq'], packet['cmd'], opts, data)
        if bool(TX_PARAMS['crc']):
            crc = coglobs.CRC16(packet_payload)
            packet_payload = struct.pack(f'<BHBs{len(packet["data"])}sH', self.id, packet['seq'], packet['cmd'], opts, data, crc)

        return packet_payload

    def _unpack_packet(self, packet: bytes, packet_len: int) -> Packet:
        if bool(TX_PARAMS['crc']):
            payload = struct.unpack(f'<BHBs{packet_len - LORALITE_HEADER_SIZE - coglobs.CONFIG["lora"]["crc_bytes"]}sH', packet)
        else:
            payload = struct.unpack(f'<BHBs{packet_len - LORALITE_HEADER_SIZE}s', packet)

        data = []
        try:
            if payload[2] == CMD_BEACON:
                data_bytes = struct.unpack('<HH', payload[4])
                data = list(data_bytes)
            elif payload[2] == CMD_DISC:
                data_bytes = struct.unpack(f'<B{len(payload[4]) - BA_SIZE - TDMA_SIZE}sBB', payload[4])
                data = list(data_bytes)
                data[1] = Node._convert_bitmap_to_ids(bits_little_endian_from_bytes(data[1]))
                data[2] = Node._create_tdma_list(data[2], data[3], payload[0])
                del data[3]
            elif payload[2] == CMD_NETWORK_INFO:
                data_bytes = struct.unpack(f'<HB{len(payload[4]) - I_SIZE - BA_SIZE - TDMA_SIZE}sBB', payload[4])
                data = list(data_bytes)
                data[2] = Node._convert_bitmap_to_ids(bits_little_endian_from_bytes(data[2]))
                data[3] = Node._create_tdma_list(data[3], data[4], payload[0])
                del data[4]
            elif payload[2] in [CMD_DISC_REPLY, CMD_NETWORK_INFO_REPLY]:
                data_bytes = struct.unpack(f'<B{len(payload[4]) - BA_SIZE}s', payload[4])
                data = list(data_bytes)
                data[1] = Node._convert_bitmap_to_ids(bits_little_endian_from_bytes(data[1]))
            elif payload[2] == CMD_PARENT_ELECTION:
                elected_ids_count = struct.unpack('<B', payload[4][:1])[0]
                data_bytes = struct.unpack(f'<B{elected_ids_count}s{len(payload[4]) - elected_ids_count - 1}s', payload[4])
                data = list(data_bytes)
                data[1] = list(struct.unpack(f'<{elected_ids_count}B', data[1]))
                data[2] = Node._convert_bitmap_to_ids(bits_little_endian_from_bytes(data[2]))
            elif payload[2] in [CMD_PARENT_ELECTION_REPLY, CMD_PARENT_ELECTION_RESULT]:
                elected_ids_count = struct.unpack('<B', payload[4][:1])[0]
                data_bytes = struct.unpack(f'<B{elected_ids_count}s', payload[4])
                data = list(data_bytes)
                data[1] = list(struct.unpack(f'<{elected_ids_count}B', data[1]))
            elif payload[2] == CMD_DATA_COLLECTION:
                data_bytes = struct.unpack(f'<{len(payload[4]) - TDMA_SIZE}sBB', payload[4])
                bitmap = Node._convert_bitmap_to_ids(bits_little_endian_from_bytes(data_bytes[0]))
                tdma_list = Node._create_tdma_list(data_bytes[1], data_bytes[2], payload[0])
                data = [id for id in tdma_list if id in bitmap]
            else:
                data = payload[4].decode()
        except struct.error as e:
            raise e

        opts = bits_little_endian_from_bytes(payload[3])
        return {
            'id': payload[0],
            'seq': payload[1], 
            'cmd': payload[2],
            'nr_of_ret': struct.unpack('<B', bytes_from_bits_little_endian(opts[:2]))[0],
            'mm_part': struct.unpack('<B', bytes_from_bits_little_endian(opts[2:5]))[0],
            'mm_count': struct.unpack('<B', bytes_from_bits_little_endian(opts[5:8]))[0],
            'data': data
        }

    def _prepare_request_data(self, cmd: int, last_order_key: Literal['disc_cmd_order', 'collect_cmd_order', 'network_info_cmd_order', 'election_cmd_order'], cycle: bool = True) -> list[int]:
        if len(self.parent_runtime_params[last_order_key]) == 0 and cmd not in [CMD_DISC, CMD_NETWORK_INFO, CMD_PARENT_ELECTION, CMD_DATA_COLLECTION]:
            self.parent_runtime_params[last_order_key] = self.parent_runtime_params['list_of_nodes']
            self.parent_runtime_params[last_order_key].sort()
        elif cmd in [CMD_PARENT_ELECTION] or (cmd == CMD_DATA_COLLECTION and len(self.parent_runtime_params[last_order_key]) == 0):
            self.parent_runtime_params[last_order_key] = self._get_active_nodes()
            self.parent_runtime_params[last_order_key].sort()
        elif len(self.parent_runtime_params[last_order_key]) == 0:
            self.parent_runtime_params[last_order_key] = [id for id in range(0, self.parent_runtime_params['expected_network_size']) if id != self.id]
        elif not cycle:
            pass
        else:
            self.parent_runtime_params[last_order_key] = self.parent_runtime_params[last_order_key][1:] + self.parent_runtime_params[last_order_key][:1]

        self._set_optimal_receive_windows(len(self.parent_runtime_params[last_order_key]))
        
        return self.parent_runtime_params[last_order_key]

    def _prepare_beacon_packet(self, pkt_seq: int) -> Packet:
        interval = self.parent_runtime_params["send_interval_s"].to_bytes(2, byteorder='little')
        return self._prepare_packet(pkt_seq, CMD_BEACON, 0, 0, 0, interval + interval)

    def _prepare_discovery_packet(self, pkt_seq: int) -> Packet:
        backhaul_access = 1 if self.backhaul_access['last_access_at'] > -1 else 0
        data = self._prepare_request_data(CMD_DISC, 'disc_cmd_order')
        bitmap = bytes_from_bits_little_endian(Node._convert_ids_to_bitmap(self._get_active_nodes(), self.parent_runtime_params['expected_network_size']))
        return self._prepare_packet(pkt_seq, CMD_DISC, 0, 0, 0, struct.pack(f'<B{len(bitmap)}sBB', backhaul_access, bitmap, data[0], max(data)))

    def _prepare_network_info_packet(self, pkt_seq: int, cycle: bool) -> Packet:
        backhaul_access = 1 if self.backhaul_access['last_access_at'] > -1 else 0
        data = self._prepare_request_data(CMD_NETWORK_INFO, 'network_info_cmd_order', cycle=cycle)
        bitmap = bytes_from_bits_little_endian(Node._convert_ids_to_bitmap(self._get_active_nodes(), self.parent_runtime_params['expected_network_size']))
        return self._prepare_packet(pkt_seq, CMD_NETWORK_INFO, 0, 0, 0, struct.pack(f'<HB{len(bitmap)}sBB', self.parent_runtime_params["send_interval_s"], backhaul_access, bitmap, data[0], max(data)))

    def _prepare_parent_election_packet(self, pkt_seq: int) -> Packet:
        coglobs.PE_ELECTION_AT.append(self.timestamp)
        elected_ids = self._select_parent_node()
        elected_ids_bytes_dict = [struct.pack('<B', id) for id in elected_ids]
        elected_ids_bytes = b''.join(elected_ids_bytes_dict)
        data = self._prepare_request_data(CMD_PARENT_ELECTION, 'election_cmd_order')
        bitmap = bytes_from_bits_little_endian(Node._convert_ids_to_bitmap(data, max(data)))
        return self._prepare_packet(pkt_seq, CMD_PARENT_ELECTION, 0, 0, 0, struct.pack(f'<B{len(elected_ids_bytes)}s{len(bitmap)}s', len(elected_ids_bytes), elected_ids_bytes, bitmap))

    def _prepare_parent_election_result_packet(self, pkt_seq: int) -> Packet:
        elected_parent_ids = self._elect_parent_node()
        elected_ids_bytes_dict = [struct.pack('<B', id) for id in elected_parent_ids]
        elected_ids_bytes = b''.join(elected_ids_bytes_dict)
        return self._prepare_packet(pkt_seq, CMD_PARENT_ELECTION_RESULT, self.node_runtime_params['nr_of_ret'], 0, 0, struct.pack(f'<B{len(elected_ids_bytes)}s', len(elected_ids_bytes), elected_ids_bytes))

    def _prepare_collection_packet(self, pkt_seq: int) -> Packet:
        data = self._prepare_request_data(CMD_DATA_COLLECTION, 'collect_cmd_order')
        bitmap = bytes_from_bits_little_endian(Node._convert_ids_to_bitmap(data, max(data)))
        return self._prepare_packet(pkt_seq, CMD_DATA_COLLECTION, 0, 0, 0, struct.pack(f'<{len(bitmap)}sBB', bitmap, data[0], max(data)))

    def _execute_packet_schedule(self, secondary: bool = False) -> None:
        pkt_seq = self.node_runtime_params['sent_pkt_seq'] + 1
        self.node_runtime_params['total_pkt_seq'] += 1
        schedule_length = len(self.packet_schedule)

        if self.parent_runtime_params['network_state'] == NETWORK_STATE.WARMUP and self.parent_runtime_params['network_state_changed_at'] > 0 and (self.timestamp - self.parent_runtime_params['network_state_changed_at']) >= (86400 * coglobs.SIU):
            self.parent_runtime_params['network_state'] = NETWORK_STATE.DATA_ORIENTED
            logger.info(self.timestamp, f'{bcolors.BMAGNETA}[node_{self.id}]LoRaLitE network state changed from WARMUP to DATA-ORIENTED{bcolors.ENDC}')

        match schedule_length:
            case schedule_length if secondary:
                time_to_next_transmission = self.next_transmission_time[LORA_MAIN_BAND] - self.timestamp
                packet: Packet = self._prepare_packet(pkt_seq, CMD_JOIN_INFO, 0, 0, 0, f'{self.parent_runtime_params["send_interval_s"]}|{time_to_next_transmission}')
            case schedule_length if schedule_length == 0:
                if self.node_runtime_params['nr_of_ret'] > 0:
                    packet = self.node_runtime_params['sent_pkt_payload']
                    packet['seq'] = pkt_seq
                    self.node_runtime_params['nr_of_ret'] -= 1
                    packet['nr_of_ret'] = self.node_runtime_params['nr_of_ret']
                elif self.parent_runtime_params['repeat_last_cmd']:
                    packet = self.node_runtime_params['sent_pkt_payload']
                    packet['seq'] = pkt_seq
                    self.parent_runtime_params['repeat_last_cmd'] = False
                else:
                    match self.parent_runtime_params['network_state']:
                        case NETWORK_STATE.UNKNOWN:
                            match self.parent_runtime_params['last_cmd']:
                                case CMD.PARENT_ELECTION.value:
                                    self.node_runtime_params['nr_of_ret'] = 2
                                    packet = self._prepare_parent_election_result_packet(pkt_seq)
                                case CMD.PARENT_ELECTION_RESULT.value:
                                    packet = self._prepare_packet(pkt_seq, CMD_BEACON, 0, 0, 0, self.parent_runtime_params["send_interval_s"].to_bytes(2, byteorder='little') + self.parent_runtime_params["send_interval_s"].to_bytes(2, byteorder='little'))
                                    # FIXME: Temporary disabled - need to figure out how many times the election proces has to run
                                    # self.parent_runtime_params['network_state'] = NETWORK_STATE.WARMUP
                                    # self.parent_runtime_params['network_state_changed_at'] = self.timestamp
                                    # logger.info(self.timestamp, f'{bcolors.BMAGNETA}[node_{self.id}]LoRaLitE network state changed from UNKNOWN to WARMUP{bcolors.ENDC}')
                                case CMD.NETWORK_INFO.value | None if coglobs.SCENARIO in [4, 5]:
                                    cycle = False if coglobs.SCENARIO == 4 else True
                                    # INFO: Parent node election time
                                    if self._check_if_election_time():
                                        packet = self._prepare_parent_election_packet(pkt_seq)
                                    else:
                                        packet = self._prepare_network_info_packet(pkt_seq, cycle)
                                case CMD.BEACON.value if coglobs.SCENARIO >= 6:
                                    # INFO: Parent node election time
                                    if self._check_if_election_time():
                                        packet = self._prepare_parent_election_packet(pkt_seq)
                                    else:
                                        packet = self._prepare_discovery_packet(pkt_seq)
                                case CMD.DISC.value if self.child_runtime_params['is_backup_parent_node']:
                                    self.child_runtime_params['is_backup_parent_node'] = False
                                    packet = self._prepare_parent_election_packet(pkt_seq)
                                case CMD.DISC.value | None if coglobs.SCENARIO >= 7:
                                    packet = self._prepare_beacon_packet(pkt_seq)
                                case CMD.DISC.value | None if coglobs.SCENARIO == 6:
                                    # INFO: Parent node election time
                                    if self._check_if_election_time():
                                        packet = self._prepare_parent_election_packet(pkt_seq)
                                    else:
                                        packet = self._prepare_discovery_packet(pkt_seq)
                        case NETWORK_STATE.WARMUP:
                            match self.parent_runtime_params['last_cmd']:
                                case CMD.DISC.value:
                                    packet = self._prepare_beacon_packet(pkt_seq)
                                case CMD.BEACON.value:
                                    packet = self._prepare_discovery_packet(pkt_seq)
                                case _:
                                    packet = self._prepare_beacon_packet(pkt_seq)                     
                        case NETWORK_STATE.DATA_ORIENTED:
                            match self.parent_runtime_params['last_cmd']:
                                case CMD.DISC.value:
                                    packet = self._prepare_collection_packet(pkt_seq)
                                case CMD.BEACON.value:
                                    packet = self._prepare_discovery_packet(pkt_seq)
                                case CMD.COLLECTION.value if (self.timestamp - self.parent_runtime_params['last_b_cmd_at'] >= 86400 * coglobs.SIU):
                                    packet = self._prepare_beacon_packet(pkt_seq)
                                case CMD.COLLECTION.value:
                                    packet = self._prepare_collection_packet(pkt_seq)
                                case _:
                                    packet = self._prepare_beacon_packet(pkt_seq)          
            case schedule_length if schedule_length > 0:
                packet = self.packet_schedule[self.node_runtime_params['total_pkt_seq']]
                del self.packet_schedule[self.node_runtime_params['total_pkt_seq']]
        self.parent_runtime_params['last_cmd'] = packet['cmd']
        self._send(packet)

    def add_packet_to_buffer(self, packet: BufferedPacket) -> None:
        self.receive_buff.append(packet)
        add_event(self.id, self.timestamp, self._receive)

    def mark_preamble_detected(self, packet: BufferedPacket) -> None:
        packet_helper = coglobs.IN_THE_AIR[self.lora_band.band].transmissions[packet['t_id']]
        if not packet_helper.c_before_preamble_detected:
            logger.info(self.timestamp, f'{bcolors.OKGREEN}PREAMBLE detected by node_{self.id}!{bcolors.ENDC}')
            self.rx_active = True
            self.rx_active_since = self.timestamp
        else:
            logger.info(self.timestamp, f'{bcolors.FAIL}node_{self.id} will not detect a preamble due to a collision (SNIR: {packet_helper.snir} dBm < SNIR_I: {packet_helper.snir_isolation} dBm)!{bcolors.ENDC}')
            coglobs.NUMBER_OF_COLLISIONS += 1
            return

        add_event(self.id, packet['t_end'], self.add_packet_to_buffer, packet)

    def _can_receive(self, timestamp: int, band: float, packet: BufferedPacket) -> bool:
        if self.state.state in [STATE_OFF, STATE_SLEEP]:
            logger.info(timestamp, f'node_{self.id} is either OFF or SLEEPING.')
            return False

        if self.state.radio_state in [STATE_OFF, STATE_SLEEP]:
            logger.info(timestamp, f'node_{self.id} radio is either OFF or in sleep state.')
            return False

        if self.state.radio_substate is not R_SUBSTATE_RX:
            logger.info(timestamp, f'node_{self.id} radio is not in RX substate.')
            return False

        if self.lora_band.band != band:
            logger.info(timestamp, f'node_{self.id} is listening on different frequency [{self.lora_band.band} <-> {band}].')
            return False

        if self.rx_active:
            logger.info(timestamp, f'node_{self.id} is currently receiving a different transmission.')
            return False

        if self.node_runtime_params['preparing_for_sleep']:
            logger.info(timestamp, f'node_{self.id} is currently going to sleep.')
            return False

        # dropping packet if its sensitivity is below receiver sensitivity
        sensitivity = RX_SENSITIVITY[self.lora_band.sf]
        if packet['rx_dbm'] < sensitivity:
            logger.info(
                timestamp,
                f'Packet is not going to be registered by node_{self.id}. Packet rx_dbm {packet["rx_dbm"]} dBm is below receiver sensitivity '
                f'{sensitivity} dBm.'
            )
            return False

        # Packet loss
        if self.simulation_params['selected_for_pl']:
            can_receive = True
            if self.simulation_params['based_on_modulo']:
                can_receive = make_decision_based_on_modulo(packet['_id'], self.simulation_params['plm'], self.simulation_params['plm_res'])
            elif self.simulation_params['based_on_probability']:
                can_receive = make_decition_based_on_probability(self.simulation_params['plp'])
            elif self.simulation_params['pkts_to_lose'] > 0:
                if self.simulation_params['pkts_from_pn'] and (packet['_sender_id'] == self.node_runtime_params['parent_node'] or self.node_runtime_params['parent_node'] == -1) and self.simulation_params['pkts_starting_seq'] == packet['_id']:
                    can_receive = False
                    self.simulation_params['pkts_to_lose'] -= 1
                    self.simulation_params['pkts_starting_seq'] += 1
                elif packet['_sender_id'] in self.simulation_params['pkts_from_nodes'] and self.simulation_params['pkts_starting_seq'] == packet['_id']:
                    can_receive = False
                    self.simulation_params['pkts_to_lose'] -= 1
                    self.simulation_params['pkts_starting_seq'] += 1

                if self.simulation_params['pkts_to_lose'] == 0 and not self.simulation_params['based_on_modulo'] and not self.simulation_params['based_on_probability']:
                    self.simulation_params['selected_for_pl'] = False
                    self.simulation_params['pkts_starting_seq'] = -1

            if not can_receive:
                # toa_ms = math.ceil(TOA.get_time_on_air(len(packet['payload'])) * coglobs.SIU)
                # add_event(self.id, self.timetamp + toa_ms)
                logger.info(self.timestamp, f'{bcolors.BYELLOW}[node_{self.id}] Packet not received due to packet loss settings.{bcolors.ENDC}')
                self.simulation_params['lost_due_to_pls'] += 1

            return can_receive

        # if self.id == 2 and 2 <= packet['_id'] <= 150:
        #     return False

        # if self.id == 1 and self.node_runtime_params['parent_node'] == 2 and packet['_id'] in [7, 8] and packet['_sender_id'] == 2:
        #     logger.info(self.timestamp, f'{bcolors.BRED}[node_{self.id}] Packet not received due to packet loss settings.{bcolors.ENDC}')
        #     return False

        return True

    def _send(self, sch_packet: Packet) -> None:
        # TODO: we need procedure when the node is not able to send
        if self.__check_send_conditions() is False:
            return

        if int(sch_packet['seq']) >= coglobs.CONFIG['general']['max_packet_nr']:
            self.node_runtime_params['sent_pkt_seq'] = 0
            sch_packet['seq'] = 0

        # INFO: With CMD_DISC_REPLY && CMD_NETWORK_INFO_REPLY the time the data is produced matters!
        if sch_packet['cmd'] in [CMD_DISC_REPLY, CMD_NETWORK_INFO_REPLY]:
            bitmap = bytes_from_bits_little_endian(Node._convert_ids_to_bitmap(self._get_active_nodes(), self.parent_runtime_params['expected_network_size']))
            backhaul_access = 1 if self.backhaul_access['last_access_at'] > -1 else 0
            sch_packet['data'] = struct.pack(f'<B{len(bitmap)}s', backhaul_access, bitmap)

        packet_payload = self._pack_packet(sch_packet)
        # packet_payload = '#'.join([str(x) for x in sch_packet.values()])
        packet: BufferedPacket = {'payload': packet_payload, 'rx_dbm': 0, 't_start': -1, 't_end': -1, 't_id': -1, '_id': sch_packet['seq'], '_sender_id': self.id}
        packet_len = len(packet_payload)
        send_interval = 0
        if self.type == NODE_TYPE.PARENT or self.type == NODE_TYPE.TMP_PARENT:
            send_interval = self.parent_runtime_params['send_interval_s']

        time_on_air, time_on_air_ms = self.__calculate_transmission_times(packet, send_interval)
        if time_on_air_ms is False:
            self._change_radio_state(STATE_OFF, SUBSTATE_NONE)
            self._change_node_state(STATE_OFF, SUBSTATE_NONE)
            return

        self._change_node_state(STATE_ON, D_SUBSTATE_OP)
        self._change_radio_state(STATE_ON, R_SUBSTATE_TX)
        self.node_runtime_params['packets_sent'] += 1
        self.node_runtime_params['bytes_sent'] += len(packet['payload'])
        self.node_runtime_params['sent_pkt_seq'] = int(sch_packet['seq'])
        self.node_runtime_params['sent_pkt'] = packet
        self.node_runtime_params['sent_pkt_payload'] = sch_packet

        receive_time = self.timestamp + time_on_air_ms
        preamble_time = self.timestamp + self.detect_preamble_ms
        packet['t_start'] = self.timestamp
        packet['t_end'] = receive_time

        if self.type == NODE_TYPE.PARENT or self.type == NODE_TYPE.TMP_PARENT:
            if sch_packet['cmd'] in [CMD_DISC, CMD_NETWORK_INFO]:
                self.parent_runtime_params['recv_count'] = 0
                node_id_list = [id for id in range(self.parent_runtime_params['expected_network_size']) if id != self.id]
                self.parent_runtime_params['expected_recv_count'] = len(node_id_list)
                self.parent_runtime_params['total_expected_recv_count'] += len(node_id_list)
                self.simulation_params['should_receive_count'] += len(self._get_active_nodes())
                self.simulation_params['expected_to_receive_count'] += len(node_id_list)
            elif sch_packet['cmd'] in [CMD_PARENT_ELECTION]:
                # INFO: node doesn't need to wait 2 x [max_send_interval] to get sync
                # INFO: when it receives something it can sleep for the time from deployment to that something - interval is not going to be smaller than that
                self.parent_runtime_params['recv_count'] = 0
                node_id_list = self.parent_runtime_params['election_cmd_order']
                self.parent_runtime_params['expected_recv_count'] = len(node_id_list)
                self.parent_runtime_params['total_expected_recv_count'] += len(node_id_list)
                self.node_runtime_params['parent_election_at'] = self.timestamp
                self.simulation_params['should_receive_count'] += len(node_id_list)
                self.simulation_params['expected_to_receive_count'] += len(node_id_list)
            elif sch_packet['cmd'] in [CMD_DATA_COLLECTION]:
                self.parent_runtime_params['recv_count'] = 0
                node_id_list = list(self._get_active_nodes())
                self.parent_runtime_params['expected_recv_count'] = len(node_id_list)
                self.parent_runtime_params['total_expected_recv_count'] += len(node_id_list)
                self.simulation_params['should_receive_count'] += len(node_id_list)
                self.simulation_params['expected_to_receive_count'] += len(node_id_list)

            if sch_packet['cmd'] == CMD_BEACON:
                self.parent_runtime_params['last_b_cmd_at'] = self.timestamp
            elif sch_packet['cmd'] == CMD_JOIN_INFO:
                self.parent_runtime_params['join_beacons_sent'] += 1

        elif self.type == NODE_TYPE.CHILD:
            if sch_packet['cmd'] == CMD_DATA_COLLECTION_REPLY:
                self.dc_bytes_sent += len(packet['payload'])

        else:
            pass

        logger.info(self.timestamp, f'{bcolors.OKBLUE}node_{self.id} is sending packet [CMD: {sch_packet["cmd"]}] with seq_nr {self.node_runtime_params["sent_pkt_seq"]}...{bcolors.ENDC}')
        
        # coglobs.CHANNEL_ACTIVE[self.lora_band.band].set_active(self)
        packet['t_id'] = coglobs.IN_THE_AIR[self.lora_band.band].register_packet(packet)

        for id in coglobs.LIST_OF_NODES:
            node: DeviceType = coglobs.LIST_OF_NODES[id]

            # skip itself
            if self.id == node.id:
                continue

            distance = get_distance(self, node)
            delay = DELAY_MODEL.get_delay(self, node)
            rx_dbm, info = PROPAGATION_MODEL.get_rx_power(self, node, self.lora_band.tx_dbm)
            logger.debug(self.timestamp, f'Propagation for node_{node.id}: {info}')
            node_packet: BufferedPacket = {
                'payload': packet['payload'],
                'rx_dbm': rx_dbm,
                't_start': packet['t_start'],
                't_end': packet['t_end'],
                't_id': packet['t_id'],
                'rx_dbm': rx_dbm,
                '_id': packet['_id'],
                '_sender_id': packet['_sender_id']
            }

            logger.debug(self.timestamp, f'Params for node_{node.id}: txPower={self.lora_band.tx_dbm}dbm, rxPower={rx_dbm}dbm, distance={distance}m, delay=+{round4(delay * 1000000)}ns')

            if node._can_receive(self.timestamp, self.lora_band.band, node_packet):
                add_event(node.id, preamble_time, node.mark_preamble_detected, node_packet)
            
        add_event(self.id, self.timestamp + time_on_air_ms, self._scheduled_log, logger.info, f'{bcolors.OKBLUE}...node_{self.id} has finished sending the message.{bcolors.ENDC}')
        add_event(self.id, self.timestamp + time_on_air_ms, self._scheduled_log, logger.info, f'Next allowed transmission time for node_{self.id}[{self.lora_band.band} MHz]: {format_ms(self.transmission_allowed_at[self.lora_band.band], coglobs.SIU)}')
        
        if self.type == NODE_TYPE.PARENT or self.type == NODE_TYPE.TMP_PARENT:
            if sch_packet['cmd'] not in [CMD_JOIN_INFO, CMD_PARENT_ELECTION_RESULT] or (sch_packet['cmd'] == CMD_PARENT_ELECTION_RESULT and sch_packet['nr_of_ret'] > 0):
                add_event(self.id, self.timestamp + time_on_air_ms, self._scheduled_log, logger.info, f'{bcolors.BMAGNETA}Next scheduled transmission time for node_{self.id}: {format_ms(self.next_transmission_time[self.lora_band.band], coglobs.SIU)}{bcolors.ENDC}')

            if sch_packet['cmd'] in [CMD_BEACON, CMD_JOIN_INFO]:
                self._end_sync(time_on_air_ms)
                return
            elif sch_packet['cmd'] == CMD_PARENT_ELECTION_RESULT:
                if sch_packet['nr_of_ret'] == 0:
                    elected_ids_count = struct.unpack('<B', sch_packet['data'][:1])[0]
                    elected_ids_bytes = struct.unpack(f'<{elected_ids_count}s', sch_packet['data'][1:])[0]
                    elected_ids =  list(struct.unpack(f'<{elected_ids_count}B', elected_ids_bytes))
                    self._handle_parent_node_election_result(elected_ids, time_on_air)
                else:
                    self._end_sync(time_on_air_ms)
                return

            if sch_packet['cmd'] == CMD_DISC:
                receive_window_length = coglobs.CONFIG['parent']['disc_window_s']
                color = bcolors.BBLUE
                cmd_name = 'DISC'
                coglobs.BIGGEST_DISC_REQUEST = coglobs.BIGGEST_DISC_REQUEST if coglobs.BIGGEST_DISC_REQUEST >= packet_len else packet_len
            elif sch_packet['cmd'] == CMD_DATA_COLLECTION:
                receive_window_length = coglobs.CONFIG['parent']['collect_window_s']
                color = bcolors.BCYAN
                cmd_name = 'DATA COLLECTION'
                # node_id_list = _prepare_node_id_list(sch_packet)
                coglobs.BIGGEST_COLL_REQUEST = coglobs.BIGGEST_COLL_REQUEST if coglobs.BIGGEST_COLL_REQUEST >= packet_len else packet_len
            elif sch_packet['cmd'] == CMD_NETWORK_INFO:
                receive_window_length = coglobs.CONFIG['parent']['network_info_window_s']
                color = bcolors.BMAGNETA
                cmd_name = 'NETWORK INFO'
            elif sch_packet['cmd'] == CMD_PARENT_ELECTION:
                receive_window_length = coglobs.CONFIG['parent']['parent_election_window_s']
                color = bcolors.BGREEN
                cmd_name = 'PARENT ELECTION'

            add_event(self.id, self.timestamp + time_on_air_ms, self._scheduled_log, logger.info, f'{color}[node_{self.id}] Waiting for {cmd_name} responses from nodes with ID: {node_id_list}{bcolors.ENDC}')
            add_event(self.id, self.timestamp + time_on_air_ms + coglobs.CONFIG['radio']['mode_change_ms'], self._change_radio_state, STATE_ON, R_SUBSTATE_RX)
            self.parent_runtime_params['receive_window']['start'] = self.timestamp + time_on_air_ms + coglobs.CONFIG['radio']['mode_change_ms']
            self.parent_runtime_params['receive_window']['end'] = self.timestamp + time_on_air_ms + coglobs.CONFIG['radio']['mode_change_ms'] + receive_window_length * coglobs.SIU
            if sch_packet['cmd'] in [CMD_DISC, CMD_NETWORK_INFO]:
                add_detached_event(self.parent_runtime_params['receive_window']['end'], NodeStats.check_if_all_nodes_are_discovered, self.parent_runtime_params['receive_window']['end'], sch_packet['data'], self.id)
            add_event(self.id, self.parent_runtime_params['receive_window']['end'], self.__check_if_received_responses)
            add_event(self.id, self.timestamp + time_on_air_ms, self._scheduled_log, logger.info, f'{color}RECEIVE WINDOW: {format_ms(self.parent_runtime_params["receive_window"]["start"], coglobs.SIU)} - {format_ms(self.parent_runtime_params["receive_window"]["end"], coglobs.SIU)}{bcolors.ENDC}')
            return 
        elif self.type == NODE_TYPE.NEW:
            # TODO: This is just a placeholder - it has to be properly fixed!
            add_event(self.id, receive_time + coglobs.CONFIG['radio']['mode_change_ms'], self._change_radio_state, STATE_ON, R_SUBSTATE_RX)
            return
        elif self.type == NODE_TYPE.CHILD and (sch_packet['cmd'] in [CMD_DISC, CMD_NETWORK_INFO_REPLY] and self.config['wait_for_all_network_info_slots']) or sch_packet['cmd'] == CMD_PARENT_ELECTION_REPLY:
            add_event(self.id, self.timestamp + time_on_air_ms + coglobs.CONFIG['radio']['mode_change_ms'], self._change_radio_state, STATE_ON, R_SUBSTATE_RX)
            return

        self._end_receive(time_on_air_ms)
        self.child_runtime_params['sbs_phase'] = False

    def _receive(self) -> None:
        if self.state.state is STATE_OFF:
            return

        if self.state.radio_state is STATE_OFF:
            return

        if len(self.receive_buff) > 1:
            raise RuntimeError('There should be exactly 1 packet in the receive buffer! Something is wrong: ', self.receive_buff)

        packet = self.receive_buff.pop(0)
        packet_helper = coglobs.IN_THE_AIR[self.lora_band.band].transmissions[packet['t_id']]
        if packet_helper.is_destroyed_by_interference:
            # TODO: What do we do in that case?
            logger.info(self.timestamp, f'{bcolors.FAIL}node_{self.id} received malformed packed due to collision (SNIR: {packet_helper.snir} dBm < SNIR_I: {packet_helper.snir_isolation} dBm)! Packet was dropped!{bcolors.ENDC}')
            coglobs.NUMBER_OF_COLLISIONS += 1
            return

        packet_len = len(packet['payload'])
        if bool(TX_PARAMS['crc']):
            crc = int.from_bytes(packet['payload'][packet_len - coglobs.CONFIG['lora']['crc_bytes']:], 'little')
            calculated_crc = coglobs.CRC16(packet['payload'][:packet_len - coglobs.CONFIG['lora']['crc_bytes']])

            if crc != calculated_crc:
                # TODO: This case has to be handled
                logger.info(self.timestamp, f'{bcolors.FAIL}node_{self.id} received malformed packed. Calculated CRC [{calculated_crc}] does not match the received one [{crc}]! Packet was dropped!{bcolors.ENDC}')
                return

        self.node_runtime_params['received_pkt'] = packet
        self.node_runtime_params['received_pkt_payload'] = self._unpack_packet(packet['payload'], packet_len)
        self.node_runtime_params['packets_received'] += 1

        if self.node_runtime_params['parent_node'] == -1 and self.node_runtime_params['received_pkt_payload']['cmd'] in [CMD_BEACON, CMD_DISC, CMD_DATA_COLLECTION, CMD_NETWORK_INFO]:
            self.node_runtime_params['parent_node'] = int(self.node_runtime_params['received_pkt_payload']['id'])

        if self.type == NODE_TYPE.CHILD and self.node_runtime_params['received_pkt_payload']['id'] == self.node_runtime_params['parent_node']:
            self.simulation_params['received_count'] += 1
            self._configure_guard_time()
        self.node_runtime_params['bytes_received'] += packet_len
        # packet_as_string = '#'.join([str(self.node_runtime_params['received_pkt_payload'][str(k)]) for k in self.node_runtime_params['received_pkt_payload']])
        packet_as_string = ', '.join([f'{k}:{v}' for k, v in self.node_runtime_params['received_pkt_payload'].items()])
        logger.info(self.timestamp, f'{bcolors.OKGREEN}Packet received by node_{self.id} [{CMD(self.node_runtime_params["received_pkt_payload"]["cmd"])}]: {packet["payload"]!r} [{packet_as_string}] [{packet_len}B] with RSSI: {packet["rx_dbm"]} dBm{bcolors.ENDC}')
        self.rx_active = False
        self.rx_active_since = -1

        self.node_runtime_params['received_pkt_payload']['rssi'] = packet['rx_dbm']

        def _extract_known_nodes() -> None:
            if self.id == int(self.node_runtime_params['received_pkt_payload']['id']):
                return

            if int(self.node_runtime_params['received_pkt_payload']['id']) not in self.known_nodes:
                self.known_nodes[int(self.node_runtime_params['received_pkt_payload']['id'])] = {}
                self.node_runtime_params['neighbor_node_discovered_after'].add(self.timestamp - self.new_node_runtime_params['deployed_at'])
                self.node_runtime_params['avg_time_between_neighbor_node_discovery'] = math.ceil(sum(self.node_runtime_params['neighbor_node_discovered_after']) / len(self.node_runtime_params['neighbor_node_discovered_after'])) # type: ignore
                # if self.type == NODE_TYPE.TMP_PARENT:
                self.node_runtime_params['time_since_last_discovered_node'] = 0
                self.node_runtime_params['last_discovered_node_at'] = self.timestamp
            # elif self.type == NODE_TYPE.TMP_PARENT:
            else:
                self.node_runtime_params['time_since_last_discovered_node'] = self.timestamp - self.node_runtime_params['last_discovered_node_at']

            self.known_nodes[int(self.node_runtime_params['received_pkt_payload']['id'])]['rssi'] = float(self.node_runtime_params['received_pkt_payload']['rssi'])
            self.known_nodes[int(self.node_runtime_params['received_pkt_payload']['id'])]['last_seen'] = self.timestamp
            self.known_nodes[int(self.node_runtime_params['received_pkt_payload']['id'])]['is_active'] = self.timestamp
            backhaul_access_index = 1 if self.node_runtime_params['received_pkt_payload']['cmd'] == CMD_NETWORK_INFO else 0
            self.known_nodes[int(self.node_runtime_params['received_pkt_payload']['id'])]['backhaul'] = bool(self.node_runtime_params['received_pkt_payload']['data'][backhaul_access_index])
            known_nodes_index = 2 if self.node_runtime_params['received_pkt_payload']['cmd'] == CMD_NETWORK_INFO else 1
            self.known_nodes[int(self.node_runtime_params['received_pkt_payload']['id'])]['known_nodes'] = self.node_runtime_params['received_pkt_payload']['data'][known_nodes_index]

        def _extract_elected_id() -> None:
            elected_ids = self.node_runtime_params['received_pkt_payload']['data'][1]
            for elected_id in elected_ids:
                if elected_id not in self.elected_nodes:
                    self.elected_nodes[elected_id] = 1
                else:
                    self.elected_nodes[elected_id] += 1

        def _set_pkts_rec_time() -> None:
            if self.new_node_runtime_params['first_pkt_rec_at'] < 0:
                self.new_node_runtime_params['first_pkt_rec_at'] = self.timestamp - time_on_air_ms
            elif self.new_node_runtime_params['second_pkt_rec_at'] < 0:
                self.new_node_runtime_params['second_pkt_rec_at'] = self.timestamp - time_on_air_ms

        time_on_air = TOA.get_time_on_air(len(packet['payload']))
        time_on_air_ms = math.ceil(time_on_air * coglobs.SIU)
        self.child_runtime_params['last_pkt_rec_at'] = self.timestamp - time_on_air_ms

        def _set_next_expected_network_event_time() -> None:
            if self.packet_delay <= 0:
                return

            next_transmission_time = self.timestamp + self.packet_delay - time_on_air_ms
            self.next_expected_transmission_time = self.timestamp + math.ceil(time_on_air * coglobs.SIU / self.lora_band.duty_cycle - time_on_air * coglobs.SIU) - time_on_air_ms
            
            if next_transmission_time > self.next_expected_transmission_time:
                self.next_expected_transmission_time = next_transmission_time

            logger.info(self.timestamp, f'{bcolors.BWHITEDARK}Next possible for node_{self.id} packet arrival time: {format_ms(self.next_expected_transmission_time, coglobs.SIU)}{bcolors.ENDC}')

        def _calculate_delay() -> None:
            if self.packet_delay <= 0 and self.new_node_runtime_params['first_pkt_rec_at'] > 0 and self.new_node_runtime_params['second_pkt_rec_at'] > 0:
                delay = float(self.new_node_runtime_params['second_pkt_rec_at'] - self.new_node_runtime_params['first_pkt_rec_at'])
                self.packet_delay = int(round1(delay / coglobs.SIU) * coglobs.SIU)
                self.transmission_interval = self.packet_delay
                self._configure_guard_time()

        if int(self.node_runtime_params['received_pkt_payload']['id']) in self.known_nodes:
            self.known_nodes[int(self.node_runtime_params['received_pkt_payload']['id'])]['last_seen'] = self.timestamp
            self.known_nodes[int(self.node_runtime_params['received_pkt_payload']['id'])]['is_active'] = True

        if self.type == NODE_TYPE.PARENT or self.type == NODE_TYPE.TMP_PARENT:
            self.parent_runtime_params['recv_count'] += 1
            if self.node_runtime_params['received_pkt_payload']['id'] not in self.parent_runtime_params['list_of_nodes']:
                self.parent_runtime_params['list_of_nodes'].append(int(self.node_runtime_params['received_pkt_payload']['id']))
            
            if self.node_runtime_params['received_pkt_payload']['cmd'] in [CMD_DISC_REPLY]:
                if coglobs.BIGGEST_DISC_RESPONSE < packet_len:
                    coglobs.BIGGEST_DISC_RESPONSE = packet_len
                _extract_known_nodes()
            if self.node_runtime_params['received_pkt_payload']['cmd'] in [CMD_DISC_REPLY, CMD_NETWORK_INFO_REPLY]:
                _extract_known_nodes()
            elif self.node_runtime_params['received_pkt_payload']['cmd'] == CMD_PARENT_ELECTION_REPLY:
                _extract_elected_id()
            
            if self.node_runtime_params['received_pkt_payload']['cmd'] in [CMD_DISC_REPLY, CMD_NETWORK_INFO_REPLY, CMD_PARENT_ELECTION_REPLY, CMD_DATA_COLLECTION_REPLY]:
                self.simulation_params['received_count'] += 1
                if self.node_runtime_params['received_pkt_payload']['id'] in self.parent_runtime_params['missing_responses_count']:
                    del self.parent_runtime_params['missing_responses_count'][self.node_runtime_params['received_pkt_payload']['id']]

            if self.parent_runtime_params['recv_count'] == self.parent_runtime_params['expected_recv_count']:
                # we keep turn off the radio when we have received all expected responses
                add_event(self.id, self.timestamp + self.config['switch_off_ms'], self._change_radio_state, STATE_OFF, SUBSTATE_NONE)
                # we can turn off the node as well
                add_event(self.id, self.timestamp + self.config['switch_off_ms'], self._change_node_state, STATE_SLEEP, SUBSTATE_NONE)
                self._end_send_receive()
        elif self.type == NODE_TYPE.CHILD or self.type == NODE_TYPE.JOINING or (self.type == NODE_TYPE.NEW and self.node_runtime_params['received_pkt_payload']['cmd'] in [CMD_DISC, CMD_NETWORK_INFO]):
            if self.node_runtime_params['received_pkt_payload']['cmd'] not in [CMD_BEACON, CMD_DISC, CMD_DISC_REPLY, CMD_DATA_COLLECTION, CMD_NETWORK_INFO, CMD_NETWORK_INFO_REPLY, CMD_PARENT_ELECTION, CMD_PARENT_ELECTION_REPLY, CMD_PARENT_ELECTION_RESULT]:
                return
            # elif self.node_runtime_params['parent_node'] == -1 and self.node_runtime_params['received_pkt_payload']['cmd'] in [CMD_BEACON, CMD_DISC, CMD_DATA_COLLECTION, CMD_NETWORK_INFO]:
            #     self.node_runtime_params['parent_node'] = int(self.node_runtime_params['received_pkt_payload']['id'])

            if self.node_runtime_params['received_pkt_payload']['cmd'] not in [CMD_DISC_REPLY, CMD_NETWORK_INFO_REPLY, CMD_DATA_COLLECTION_REPLY, CMD_PARENT_ELECTION_REPLY]:                
                # TODO: implement nr_of_ret
                self.child_runtime_params['last_pkt_from_parent_rec_at'] = self.timestamp - time_on_air_ms
                if self.node_runtime_params['received_pkt_payload']['cmd'] in [CMD_BEACON, CMD_NETWORK_INFO]:
                    # TODO: implement switching to a new delay
                    self.sync += 1
                    if self.node_runtime_params['received_pkt_payload']['cmd'] == CMD_BEACON:
                        old_delay, new_delay = self.node_runtime_params['received_pkt_payload']['data']
                    else:
                        _set_pkts_rec_time()
                        old_delay = self.node_runtime_params['received_pkt_payload']['data'][0]
                        self._change_node_type(NODE_TYPE.CHILD)
                    # new_delay = int(self.node_runtime_params['received_pkt_payload']['data'])
                    self.packet_delay = old_delay * coglobs.SIU
                    self.transmission_interval = old_delay * coglobs.SIU
                elif self.node_runtime_params['received_pkt_payload']['cmd'] == CMD_DISC:
                    _set_pkts_rec_time()
                    _calculate_delay()
                    if self.packet_delay > 0 and self.type is not NODE_TYPE.CHILD:
                        self._change_node_type(NODE_TYPE.CHILD)

                    if coglobs.BIGGEST_DISC_REQUEST < packet_len:
                        coglobs.BIGGEST_DISC_REQUEST = packet_len

                _set_next_expected_network_event_time()

            # case where the child node has to respond to the parent node
            if self.node_runtime_params['received_pkt_payload']['cmd'] not in [CMD_BEACON, CMD_JOIN_INFO, CMD_DISC_REPLY, CMD_NETWORK_INFO_REPLY, CMD_PARENT_ELECTION_REPLY, CMD_PARENT_ELECTION_RESULT]:
                if self.node_runtime_params['received_pkt_payload']['cmd'] == CMD_DATA_COLLECTION:
                    received_pkt_data = self.node_runtime_params['received_pkt_payload']['data']
                    # received_pkt_data = Node._unpack_ids(str(self.node_runtime_params['received_pkt_payload']['data']))
                elif self.node_runtime_params['received_pkt_payload']['cmd'] == CMD_DISC:
                    _extract_known_nodes()
                    received_pkt_data = self.node_runtime_params['received_pkt_payload']['data'][2]
                    # Response will correspond in size to Parent request, minus 2 bytes for TDMA
                    max_toa_ms = math.ceil(TOA.get_time_on_air(packet_len - TDMA_SIZE) * coglobs.SIU)
                elif self.node_runtime_params['received_pkt_payload']['cmd'] == CMD_NETWORK_INFO:
                    _extract_known_nodes()
                    received_pkt_data = self.node_runtime_params['received_pkt_payload']['data'][3]
                    max_toa_ms = math.ceil(TOA.get_time_on_air(packet_len - TDMA_SIZE) * coglobs.SIU)
                    if self.config['wait_for_all_network_info_slots']:
                        # Response will correspond in size to Parent request, minus 2 bytes for TDMA
                        rec_niw_s = math.ceil((max_toa_ms + coglobs.CONFIG['child']['reply_gt_ms'] + coglobs.CONFIG['radio']['mode_change_ms']) * (len(received_pkt_data) + 1) / coglobs.SIU)
                        self.child_runtime_params['receive_window']['end'] = self.timestamp + coglobs.CONFIG['radio']['mode_change_ms'] + rec_niw_s * coglobs.SIU
                        logger.info(self.timestamp, f'{bcolors.BWHITEDARK}node_{self.id} listens for NR from other nodes untill {format_ms(self.child_runtime_params["receive_window"]["end"], coglobs.SIU)}{bcolors.ENDC}')
                        add_event(self.id, self.child_runtime_params['receive_window']['end'], self._end_receive, self.child_config['op_duration_ms'])
                elif self.node_runtime_params['received_pkt_payload']['cmd'] == CMD_PARENT_ELECTION:
                    self.elected_nodes = SortedDict()
                    received_pkt_data = self.node_runtime_params['received_pkt_payload']['data'][2]
                    elected_ids = self.node_runtime_params['received_pkt_payload']['data'][1]
                    for elected_id in elected_ids:
                        self.elected_nodes[elected_id] = 1
                    max_toa_ms = math.ceil(TOA.get_time_on_air(LORALITE_HEADER_SIZE + coglobs.CONFIG['lora']['crc_bytes'] + PE_CT_SIZE + PE_SIZE) * coglobs.SIU)
                    rec_pe_s = math.ceil((max_toa_ms + coglobs.CONFIG['child']['reply_gt_ms'] + coglobs.CONFIG['radio']['mode_change_ms']) * (len(received_pkt_data) + 1) / coglobs.SIU)
                    self.child_runtime_params['receive_window']['end'] = self.timestamp + coglobs.CONFIG['radio']['mode_change_ms'] + rec_pe_s * coglobs.SIU
                    logger.info(self.timestamp, f'{bcolors.BWHITEDARK}node_{self.id} listens for ER from other nodes untill {format_ms(self.child_runtime_params["receive_window"]["end"], coglobs.SIU)}{bcolors.ENDC}')
                    add_event(self.id, self.child_runtime_params['receive_window']['end'], self._end_receive, self.child_config['op_duration_ms'])

                if self.id not in received_pkt_data:
                    self._end_receive(self.child_config['op_duration_ms'])
                    return

                pkt_seq = self.node_runtime_params['sent_pkt_seq'] + 1
                if self.node_runtime_params['received_pkt_payload']['cmd'] == CMD_DISC:
                    self.d += 1
                    current_cmd = CMD_DISC_REPLY
                    data = b''
                    if self.type == NODE_TYPE.JOINING:
                        self._change_node_type(NODE_TYPE.CHILD)
                elif self.node_runtime_params['received_pkt_payload']['cmd'] == CMD_DATA_COLLECTION:
                    self.dc += 1
                    current_cmd = CMD_DATA_COLLECTION_REPLY
                    max_toa_ms = math.ceil(TOA.get_time_on_air(coglobs.CONFIG['lora']['payload_size']) * coglobs.SIU)
                    
                    tmp_pkt_len = LORALITE_HEADER_SIZE + coglobs.CONFIG['lora']['crc_bytes']
                    if coglobs.CONFIG['lora']['bytes_to_send'] > 0:
                        to_fill = coglobs.CONFIG['lora']['payload_size'] - tmp_pkt_len
                        if self.dc_bytes_sent + to_fill + tmp_pkt_len > coglobs.CONFIG['lora']['bytes_to_send']:
                            to_fill = coglobs.CONFIG['lora']['bytes_to_send'] - self.dc_bytes_sent - tmp_pkt_len
                            to_fill = to_fill if to_fill > 0 else 0
                        # data = ''.join(choice(ascii_uppercase) for i in range(to_fill))
                        c_data = SAMPLE_DATA[:to_fill]
                    else:
                        # data = ''.join(choice(ascii_uppercase) for i in range(coglobs.CONFIG['lora']['payload_size'] - tmp_pkt_len))
                        c_data = SAMPLE_DATA[:(coglobs.CONFIG['lora']['payload_size'] - tmp_pkt_len)]
                    data = c_data.encode('iso-8859-1')
                elif self.node_runtime_params['received_pkt_payload']['cmd'] == CMD_NETWORK_INFO:
                    self.ni += 1
                    current_cmd = CMD_NETWORK_INFO_REPLY
                    data = b''
                elif self.node_runtime_params['received_pkt_payload']['cmd'] == CMD_PARENT_ELECTION:
                    self.pe += 1
                    current_cmd = CMD_PARENT_ELECTION_REPLY
                    self.node_runtime_params['parent_election_at'] = self.timestamp
                    elected_ids = self._select_parent_node()
                    elected_ids_bytes_dict = [struct.pack('<B', id) for id in elected_ids]
                    elected_ids_bytes = b''.join(elected_ids_bytes_dict)
                    data = struct.pack(f'<B{len(elected_ids_bytes)}s', len(elected_ids_bytes), elected_ids_bytes)

                self.node_runtime_params['sent_pkt_seq'] += 1
                packet_to_send = {'seq': pkt_seq, 'cmd': current_cmd, 'nr_of_ret': 0, 'mm_part': 0, 'mm_count': 0, 'data': data}
                packet_timeslot = coglobs.CONFIG['child']['reply_gt_ms'] + max_toa_ms

                slot_nr = received_pkt_data.index(self.id)
                packet_ts = self.timestamp + coglobs.CONFIG['radio']['mode_change_ms'] + packet_timeslot * slot_nr
                # if slot_nr == 0:
                #     packet_ts += coglobs.CONFIG['radio']['mode_change_ms']
                    # packet_ts += coglobs.CONFIG['child']['reply_gt_ms'] - coglobs.CONFIG['radio']['mode_change_ms']

                if self.child_config['sleep_before_sending'] and self.node_runtime_params['received_pkt_payload']['cmd'] == CMD_DATA_COLLECTION:
                    # if waiting (idle) time is bigger than Guard Time + switch on + switch off + radio mode_change the node goes to sleep to conserve energy
                    # TODO: What about mode_change_ms?
                    guarded_period_ms = max_toa_ms + coglobs.CONFIG["child"]["reply_gt_ms"] + self.config['switch_off_ms'] + self.config['switch_on_ms']
                    if packet_ts > self.timestamp + guarded_period_ms:
                        self.child_runtime_params['sbs_phase'] = True
                        add_event(self.id, self.timestamp + self.config['switch_off_ms'], self._change_radio_state, STATE_OFF, SUBSTATE_NONE)
                        add_event(self.id, self.timestamp + self.config['switch_off_ms'], self._change_node_state, STATE_SLEEP, SUBSTATE_NONE)
                        self.node_runtime_params['preparing_for_sleep'] = True

                        # we need to wake-up the node before the response slot time
                        wakeup_ts = packet_ts - guarded_period_ms
                        add_event(self.id, wakeup_ts, self._change_node_state, STATE_ON, SUBSTATE_NONE)
                        add_event(self.id, wakeup_ts, self._change_radio_state, STATE_ON, R_SUBSTATE_RX)

                        # FIXME: verify it!
                        sleep_ms = packet_ts - (self.timestamp + guarded_period_ms)
                        logger.info(self.timestamp, f'{bcolors.MAGNETA}Response timeslot for node_{self.id}[{slot_nr}]: {format_ms(packet_ts, coglobs.SIU)} -> ' \
                            f'{format_ms(packet_ts + max_toa_ms, coglobs.SIU)} [sleeps_for: {sleep_ms}ms wakes_at:{format_ms(wakeup_ts, coglobs.SIU)}]{bcolors.ENDC}')
                    else:
                        logger.info(self.timestamp, f'{bcolors.MAGNETA}Response timeslot for node_{self.id}[{slot_nr}]: {format_ms(packet_ts, coglobs.SIU)} -> {format_ms(packet_ts + max_toa_ms, coglobs.SIU)}{bcolors.ENDC}')
                else:
                    logger.info(self.timestamp, f'{bcolors.MAGNETA}Response timeslot for node_{self.id}[{slot_nr}]: {format_ms(packet_ts, coglobs.SIU)} -> {format_ms(packet_ts + max_toa_ms, coglobs.SIU)}{bcolors.ENDC}')

                add_event(self.id, packet_ts, self._change_radio_state, STATE_ON, R_SUBSTATE_TX)            
                add_event(self.id, packet_ts, self._send, packet_to_send)            

                return
            elif self.node_runtime_params['received_pkt_payload']['cmd'] in [CMD_DISC_REPLY, CMD_NETWORK_INFO_REPLY]:
                # INFO: If the node is outside parent/tmp_parent range it might be able to receive other nodes responses
                # QUESTION: What do we do in the case described above?
                _extract_known_nodes()
                return
            elif self.node_runtime_params['received_pkt_payload']['cmd'] == CMD_PARENT_ELECTION_REPLY:
                _extract_elected_id()
                return
            elif self.node_runtime_params['received_pkt_payload']['cmd'] == CMD_PARENT_ELECTION_RESULT:
                if self.node_runtime_params['received_pkt_payload']['nr_of_ret'] == 0:
                    elected_ids = self.node_runtime_params['received_pkt_payload']['data'][1]
                    self._handle_parent_node_election_result(elected_ids, time_on_air)
                    return
            
            self._end_receive(self.child_config['op_duration_ms'])
        elif self.type == NODE_TYPE.NEW:
            if self.node_runtime_params['received_pkt_payload']['cmd'] in [CMD_DISC_REPLY, CMD_NETWORK_INFO_REPLY]:
                # TODO: implement me!
                _extract_known_nodes()
            if self.node_runtime_params['received_pkt_payload']['cmd'] not in [CMD_BEACON, CMD_DISC, CMD_DATA_COLLECTION, CMD_JOIN_INFO]:
                return
            if self.node_runtime_params['received_pkt_payload']['cmd'] == CMD_JOIN_INFO:
                cmd_interval_s, time_to_next_transmission = [int(x) for x in str(self.node_runtime_params['received_pkt_payload']['data']).split('|')]
                self.next_expected_transmission_time = self.timestamp + time_to_next_transmission - time_on_air_ms
                self.packet_delay = cmd_interval_s * coglobs.SIU
                self._change_node_type(NODE_TYPE.JOINING)
                # self.new_node_runtime_params['new_node_until'] = self.timestamp
                add_event(self.id, self.timestamp + coglobs.CONFIG['radio']['mode_change_ms'], self._change_radio_band, LORA_MAIN_BAND, SF_12)
                # self._change_radio_band(LORA_MAIN_BAND, SF_12)
                self._end_receive(coglobs.CONFIG['radio']['mode_change_ms'])
            else:
                def _set_node_schedule() -> None:
                    _set_next_expected_network_event_time()
                    
                    self._change_node_type(NODE_TYPE.JOINING)
                    self._configure_guard_time()
                    self.new_node_runtime_params['new_node_until'] = self.timestamp
                    self._end_receive(self.child_config['op_duration_ms'])
                
                _set_pkts_rec_time()
                if self.node_runtime_params['received_pkt_payload']['cmd'] == CMD_BEACON:
                    delay, _ = self.node_runtime_params['received_pkt_payload']['data']
                    self.packet_delay = delay * coglobs.SIU
                    self.transmission_interval = delay * coglobs.SIU
                    _set_node_schedule()
                else:
                    if self.new_node_runtime_params['first_pkt_rec_at'] > 0 and self.new_node_runtime_params['second_pkt_rec_at'] > 0:
                        _calculate_delay()
                        _set_node_schedule()

    def _is_network_detected(self, recheck: bool = False) -> bool:
        if self.rx_active:
            return True

        if self.new_node_runtime_params['first_pkt_rec_at'] < 0:
            if not recheck:
                if self.parent_config['random_t_before_becoming_tmp_parent']:
                    event_ts = self.timestamp + randint(0, self.parent_config['max_send_interval_s'])
                else:
                    event_ts = self.timestamp + self.parent_config['t_before_becoming_tmp_parent']
                add_event(self.id, event_ts, self._become_temporary_parent)
            return False

        return True

    def _check_if_should_perform_backoff(self) -> None:
        if self.rx_active:
            return

        max_toa_ms = math.ceil(TOA.get_time_on_air(coglobs.CONFIG['lora']['payload_size']) * coglobs.SIU)
        ts_start = self.timestamp - self.parent_config['max_send_interval_s'] * coglobs.SIU - max_toa_ms
        if ts_start < self.child_runtime_params['last_pkt_from_parent_rec_at'] <= self.timestamp:
            return

        self._perform_backoff()

    def _perform_backoff(self) -> None:
        self.node_runtime_params['backoff_s'] == self.node_runtime_params['backoff_s'] * 2 if self.node_runtime_params['backoff_s'] > 0 else self.config['backoff_s']
        sleep_starts_at = self.timestamp + self.config['switch_off_ms']
        add_event(self.id, sleep_starts_at, self._change_radio_state, STATE_OFF, SUBSTATE_NONE)
        add_event(self.id, sleep_starts_at, self._change_node_state, STATE_OFF, SUBSTATE_NONE)
        next_wakeup_ts = sleep_starts_at + self.config['switch_on_ms'] + self.node_runtime_params['backoff_s'] * coglobs.SIU
        add_event(self.id, next_wakeup_ts, self._change_node_state, STATE_ON, SUBSTATE_NONE)
        add_event(self.id, next_wakeup_ts, self._change_radio_state, STATE_ON, R_SUBSTATE_RX)
        max_toa_ms = math.ceil(TOA.get_time_on_air(coglobs.CONFIG['lora']['payload_size']) * coglobs.SIU)
        add_event(self.id, next_wakeup_ts + self.parent_config['max_send_interval_s'] * coglobs.SIU + max_toa_ms, self._check_if_should_perform_backoff)

    def _become_temporary_parent(self) -> None:
        if self._is_network_detected(True):
            return

        self._change_node_type(NODE_TYPE.TMP_PARENT)
        self.node_runtime_params['parent_node'] = self.id
        time_on_air = TOA.get_time_on_air(TX_PARAMS['max_payload'])
        send_interval = math.ceil(round2(time_on_air / self.lora_band.duty_cycle - time_on_air))
        if self.parent_config['network_info_send_interval_s'] > -1 and self.parent_config['network_info_send_interval_s'] < send_interval:
            raise SimException(f'network_info_send_interval_s (-tni) cannot be smaller than {send_interval}s!')
        elif self.parent_config['network_info_send_interval_s'] > -1:
            send_interval = self.parent_config['network_info_send_interval_s']
        self.parent_runtime_params['send_interval_s'] = send_interval
        self.packet_delay = send_interval * coglobs.SIU
        self.transmission_interval = self.packet_delay

        add_event(self.id, self.timestamp + coglobs.CONFIG['radio']['mode_change_ms'], self._change_radio_state, STATE_ON, R_SUBSTATE_TX)
        add_event(self.id, self.timestamp + coglobs.CONFIG['radio']['mode_change_ms'], self._execute_packet_schedule)

    def _replace_parent(self) -> None:
        received_any_pkt = self.child_runtime_params['last_pkt_rec_at'] > self.child_runtime_params['last_pkt_from_parent_rec_at']
        if not received_any_pkt:
            self.parent_runtime_params['send_interval_s'] = math.ceil(self.packet_delay / coglobs.SIU)
            self.parent_runtime_params['last_cmd'] = CMD_BEACON
            self.node_runtime_params['parent_node'] = self.id
            self.next_transmission_time[self.lora_band.band] = int(self.next_expected_transmission_time)
            add_event(self.id, self.timestamp, self._change_node_type, NODE_TYPE.PARENT)
            add_event(self.id, self.timestamp, self._scheduled_log, logger.info, f'{bcolors.BMAGNETA}Next scheduled transmission time for node_{self.id}: {format_ms(self.next_transmission_time[self.lora_band.band], coglobs.SIU)}{bcolors.ENDC}')
            self._end_sync(0)

    def _check_if_election_time(self) -> bool:
        avg_discovery_factor = math.ceil(self.node_runtime_params['avg_time_between_neighbor_node_discovery'] * coglobs.CONFIG['scenarios']['scenario_ge_4']['parent_election_multipler'])
        if not coglobs.CONFIG['scenarios']['scenario_ge_4']['parent_election_disabled'] \
            and self.node_runtime_params['time_since_last_discovered_node'] >= 0 \
            and self.node_runtime_params['parent_election_at'] < self.node_runtime_params['last_discovered_node_at'] \
            and self.node_runtime_params['time_since_last_discovered_node'] >= avg_discovery_factor:

            return True

        return False

    def _select_parent_node(self) -> list[int]:
        #TODO: backhaul access has to be factored in as well
        node_count = {}
        active_nodes = self._get_active_nodes()
        node_count[self.id] = len(active_nodes)
        for known_node_id in active_nodes:
            node_count[known_node_id] = len(self.known_nodes[known_node_id]['known_nodes'])
        
        node_count = dict(sorted(node_count.items(), key=lambda item: item[1], reverse=True))
        elected_ids = []
        current_parent_node_count = node_count[self.node_runtime_params['parent_node']]
        max_node_count = max(node_count.values())

        to_fill = 3
        if current_parent_node_count >= max_node_count:
            elected_ids.append(self.node_runtime_params['parent_node'])
            del node_count[self.node_runtime_params['parent_node']]
            to_fill -= 1

        if len(node_count) >= to_fill:
            elected_ids += list(node_count.keys())[:to_fill]
        else:
            elected_ids += list(node_count.keys())

        # if self.id in [0]:
        #     elected_ids[2] = 2

        return elected_ids

    def _elect_parent_node(self) -> list[int]:
        node_ids: Dict[int, int] = dict(sorted(self.elected_nodes.items(), key=lambda item: int(item[1]), reverse=True))
        to_fill = 3
        elected_nodes: list[int] = []
        max_votes = max(list(self.elected_nodes.values()))
        if self.elected_nodes[self.id] >= max_votes:
            elected_nodes.append(self.id)
            del node_ids[self.id]
            to_fill -= 1

        if len(node_ids) >= to_fill:
            elected_nodes += list(node_ids.keys())[:to_fill]
        else:
            elected_nodes = list(node_ids.keys())

        if coglobs.CONFIG['general']['force_parent_node_change']:
            elected_nodes.reverse()

        return elected_nodes

    def _handle_parent_node_election_result(self, elected_ids: list[int], time_on_air: float) -> None:
        time_on_air_ms = math.ceil(time_on_air * coglobs.SIU)
        additional_time = 0
        was_a_parent = (self.type in [NODE_TYPE.TMP_PARENT, NODE_TYPE.PARENT] and self.id != elected_ids[0])
        remains_a_parent = (self.type in [NODE_TYPE.TMP_PARENT, NODE_TYPE.PARENT] and self.id == elected_ids[0])
        if was_a_parent or (self.id in elected_ids and elected_ids.index(self.id) > 0):      
            if was_a_parent:
                self.next_expected_transmission_time = self.timestamp + self.parent_runtime_params['send_interval_s'] * coglobs.SIU
                self._configure_guard_time()
                add_event(self.id, self.timestamp + time_on_air_ms, self._change_node_type, NODE_TYPE.CHILD)
                add_event(self.id, self.timestamp + time_on_air_ms, self._end_receive, self.child_config['op_duration_ms'])

            self.node_runtime_params['parent_node'] = elected_ids[0]
            del elected_ids[0]
            if self.id in elected_ids:
                self.child_runtime_params['is_backup_parent_node'] = True
                self.child_runtime_params['backup_parent_node_index'] = elected_ids.index(self.id)
            
            if not was_a_parent:
                self._end_receive(self.child_config['op_duration_ms'])
        elif self.id in elected_ids and elected_ids.index(self.id) == 0:
            if not was_a_parent and not remains_a_parent:
                self.parent_runtime_params['send_interval_s'] = math.ceil(self.packet_delay / coglobs.SIU)
                self.next_transmission_time[self.lora_band.band] = int(self.next_expected_transmission_time)
                logger.info(self.timestamp, f'{bcolors.BMAGNETA}Next scheduled transmission time for node_{self.id}: {format_ms(self.next_transmission_time[self.lora_band.band], coglobs.SIU)}{bcolors.ENDC}')
                self._change_node_type(NODE_TYPE.PARENT)
                self.parent_runtime_params['last_cmd'] == CMD_BEACON
            elif remains_a_parent:
                add_event(self.id, self.timestamp + time_on_air_ms, self._change_node_type, NODE_TYPE.PARENT)
            
            self.child_runtime_params['is_backup_parent_node'] = False
            del elected_ids[0]
            if remains_a_parent:
                self._end_sync(time_on_air_ms)
                additional_time = time_on_air_ms
            else:
                self._end_sync(0)
            # if self.timestamp not in coglobs.PE_FINISHED_AT:
            #     coglobs.PE_FINISHED_AT.append(self.timestamp)
        else:
            self.node_runtime_params['parent_node'] = elected_ids[0]
            self.child_runtime_params['is_backup_parent_node'] = False
            del elected_ids[0]
            self._end_receive(self.child_config['op_duration_ms'])
            # if self.timestamp not in coglobs.PE_FINISHED_AT:
            #     coglobs.PE_FINISHED_AT.append(self.timestamp)

        self.parent_runtime_params['repeat_last_cmd'] = False
        self.node_runtime_params['backup_parent_nodes'] = elected_ids

        if self.timestamp not in coglobs.PE_FINISHED_AT:
            coglobs.PE_FINISHED_AT.append(self.timestamp + time_on_air_ms)

    def _end_receive(self, op_duration: int = 0) -> None:
        # we got the packet so we can turn off radio
        add_event(self.id, self.timestamp + op_duration + self.config['switch_off_ms'], self._change_radio_state, STATE_OFF, SUBSTATE_NONE)

        # node needs to execute some jobs related to the received call but after the given operational time it can
        # be turned off
        add_event(self.id, self.timestamp + op_duration + self.config['switch_off_ms'], self._change_node_state, STATE_SLEEP, SUBSTATE_NONE)

        # we need to turn on the node so it can potentially receive the next cmd around the next expected
        # transmission time
        next_schedule_timestamp = math.floor(self.next_expected_transmission_time - self.child_runtime_params['wait_before_ms'])
        
        self.next_wakeup_time = next_schedule_timestamp - self.config['switch_on_ms']
        add_event(self.id, self.next_wakeup_time, self._change_node_state, STATE_ON, SUBSTATE_NONE)
        add_event(self.id, self.next_wakeup_time, self._change_radio_state, STATE_ON, SUBSTATE_NONE)
        add_event(self.id, next_schedule_timestamp, self._change_radio_state, STATE_ON, R_SUBSTATE_RX)

        guard_time_start = next_schedule_timestamp
        guard_time_end = next_schedule_timestamp + self.child_runtime_params['guard_time_ms']
        guard_time_end_with_preamble = next_schedule_timestamp + self.child_runtime_params['guard_time_ms'] + self.detect_preamble_ms
        if self.child_runtime_params['is_backup_parent_node']:
            max_toa_ms = math.ceil(TOA.get_time_on_air(coglobs.CONFIG['lora']['payload_size']) * coglobs.SIU)
            guard_time_end_with_preamble = next_schedule_timestamp + self.child_runtime_params['guard_time_ms'] + 2 * max_toa_ms
        logger.info(
            self.timestamp, f'{bcolors.BWHITEDARK}[node_{self.id}]{"[BPN]" if self.child_runtime_params["is_backup_parent_node"] else ""} next guard time: <{format_ms(guard_time_start, coglobs.SIU)} : {format_ms(guard_time_end, coglobs.SIU)} [{format_ms(guard_time_end_with_preamble, coglobs.SIU)}]>{bcolors.ENDC}'
        )

    def _end_sync(self, time_on_air_ms: int) -> None:
        # we keep the radio on as long as ToA duration of the packet
        add_event(self.id, self.timestamp + time_on_air_ms + self.config['switch_off_ms'], self._change_radio_state, STATE_OFF, SUBSTATE_NONE)
        # we can turn off the node when packet is sent
        add_event(self.id, self.timestamp + time_on_air_ms + self.config['switch_off_ms'], self._change_node_state, STATE_SLEEP, SUBSTATE_NONE)
        self._end_send_receive()

    def _end_send_receive(self) -> None:
        # we need to prepare schedule for the next transmission
        self.next_wakeup_time = self.next_transmission_time[LORA_MAIN_BAND] - self.config['switch_on_ms']
        self._prepare_join_beacon()
        if self.lora_band.band == LORA_MAIN_BAND:
            add_event(self.id, self.next_wakeup_time, self._change_node_state, STATE_ON, SUBSTATE_NONE)      
            add_event(self.id, self.next_wakeup_time, self._change_radio_state, STATE_ON, SUBSTATE_NONE)
            add_event(self.id, self.next_transmission_time[self.lora_band.band], self._execute_packet_schedule)    

    def _prepare_join_beacon(self) -> None:
        if not self.parent_config['secondary_schedule']:
            return
        time_to_next_wakeup = self.next_wakeup_time - self.timestamp
        time_to_next_transmission = self.next_transmission_time[LORA_MAIN_BAND] - self.timestamp
        tmp_packet = self._prepare_packet(self.node_runtime_params['sent_pkt_seq'] + 1, CMD_JOIN_INFO, 0, 0, 0, f'{self.parent_runtime_params["send_interval_s"]}|{time_to_next_transmission}')
        packet_payload = self._pack_packet(tmp_packet)
        join_beacon_toa_ms = math.ceil(TOA.get_time_on_air(len(packet_payload)) * coglobs.SIU)
        needed_time = join_beacon_toa_ms + self.config['switch_on_ms'] + self.config['switch_off_ms']
        
        if needed_time > time_to_next_wakeup:
            return

        last_beacon_ms_ago = self.timestamp - self.parent_runtime_params['join_beacon_sent_at'] if self.parent_runtime_params['join_beacon_sent_at'] > 0 else self.parent_config['join_beacon_after_ms']
        ms_to_next_beacon = last_beacon_ms_ago - self.parent_config['join_beacon_interval_ms']
        ms_to_next_beacon = abs(ms_to_next_beacon) if ms_to_next_beacon < 0 else self.parent_config['join_beacon_after_ms']
        ms_to_next_beacon = self.parent_config['join_beacon_after_ms'] if ms_to_next_beacon < self.parent_config['join_beacon_after_ms'] else ms_to_next_beacon
        
        join_beacon_ts = self.timestamp + ms_to_next_beacon
        if join_beacon_ts + needed_time >= self.next_wakeup_time:
            return
            
        add_event(self.id, join_beacon_ts - self.config['switch_on_ms'] - coglobs.CONFIG['radio']['mode_change_ms'], self._change_node_state, STATE_ON)
        add_event(self.id, join_beacon_ts - self.config['switch_on_ms'] - coglobs.CONFIG['radio']['mode_change_ms'], self._change_radio_state, STATE_ON, SUBSTATE_NONE)
        add_event(self.id, join_beacon_ts - self.config['switch_on_ms'], self._change_radio_band, LORA_SECONDARY_BAND, SF_12)
        add_event(self.id, join_beacon_ts, self._execute_packet_schedule, True)

    def _increase_guard_time(self) -> None:
        self.child_runtime_params['guard_time_ms'] += self.child_config['guard_time_ms']
        self.child_runtime_params['wait_before_ms'] = math.ceil(self.child_runtime_params['guard_time_ms'] / 2)

    def _configure_guard_time(self) -> None:
        gt = self.child_config['guard_time_ms']
        if self.packet_delay > 0:
            gt = math.ceil(coglobs.CONFIG['parent']['send_interval_s'] * coglobs.SIU * (coglobs.CONFIG['general']['cdppm'] / coglobs.SIU ** 2)) * 4
            if not gt % 2 == 0:
                gt += 1
        self.child_runtime_params['guard_time_ms'] = gt
        self.child_runtime_params['wait_before_ms'] = math.ceil(gt / 2)
        if gt != self.child_config['guard_time_ms']:
            self.child_config['guard_time_ms'] = gt
            self.child_config['wait_before_ms'] = math.ceil(gt / 2)
            logger.info(self.timestamp, f'{bcolors.BWHITEDARK}[node_{self.id}] new guard time [{gt}ms] was set for packet interval of {format_ms(int(self.packet_delay), coglobs.SIU)}{bcolors.ENDC}')
        #     return

        # logger.info(self.timestamp, f'{bcolors.BWHITEDARK}[node_{self.id}] guard time set to {gt}ms{bcolors.ENDC}')

    def __check_if_received_responses(self) -> None:
        if self.state.state is STATE_SLEEP:
            return

        if self.state.radio_state is STATE_OFF:
            return

        #if the node is still up it means that it did not receive all expected responses :(
        #if didn't receive any response then packet was lost and has to be repeated
        if self.parent_runtime_params['recv_count'] == 0 and len(self._get_active_nodes()) > 0:
            logger.info(self.timestamp, f'{bcolors.WARNING}node_{self.id} did not receive any response from {self.parent_runtime_params["expected_recv_count"]} nodes. Request packet was probably lost.{bcolors.ENDC}')
            self.parent_runtime_params['repeat_last_cmd'] = True
            self.parent_runtime_params['missing_responses_from_all_count'] += 1
        elif self.parent_runtime_params['recv_count'] < self.parent_runtime_params['expected_recv_count']:
            # TODO: verify!
            missing_nodes = [node_id for node_id in self.known_nodes if self.known_nodes[node_id]['last_seen'] < self.timestamp - self.packet_delay]
            if len(missing_nodes) > 0:
                for node_id in missing_nodes:
                    if node_id not in self.parent_runtime_params['missing_responses_count']:
                        self.parent_runtime_params['missing_responses_count'][node_id] = 1
                        continue

                    self.parent_runtime_params['missing_responses_count'][node_id] += 1
            
            for node_id in self.parent_runtime_params['missing_responses_count']:
                if self.parent_runtime_params['missing_responses_count'][node_id] >= 3:
                    self.known_nodes[node_id]['is_active'] = False
                    logger.info(self.timestamp, f'{bcolors.BYELLOW}{bcolors.FAIL}[node_{self.id}] node_{node_id} was marked as inactive.{bcolors.ENDC}')
            
            logger.info(self.timestamp, f'{bcolors.WARNING}node_{self.id} received only {self.parent_runtime_params["recv_count"]} / {self.parent_runtime_params["expected_recv_count"]}.{bcolors.ENDC}')
            if coglobs.CONFIG['general']['quit_on_failure']:
                raise ClockDriftException(f'node_{self.id} received only {self.parent_runtime_params["recv_count"]} / {self.parent_runtime_params["expected_recv_count"]}.')


        if self.parent_runtime_params['missing_responses_from_all_count'] >= 3:
            self.parent_runtime_params['missing_responses_from_all_count'] = 0
            self.parent_runtime_params['missing_responses_count'] = {}
            logger.info(self.timestamp, f'{bcolors.WARNING}node_{self.id} did not receive any response 3 times in a row.{bcolors.ENDC}')
            self._change_node_type(NODE_TYPE.CHILD)
            self.node_runtime_params['parent_node'] = -1
            last_pkt_toa_ms = math.ceil(TOA.get_time_on_air(len(self.node_runtime_params['sent_pkt']['payload'])) * coglobs.SIU)
            ts_before_sending_pkt = self.parent_runtime_params['receive_window']['start'] - coglobs.CONFIG['radio']['mode_change_ms'] - last_pkt_toa_ms
            self.child_runtime_params['last_pkt_from_parent_rec_at'] = ts_before_sending_pkt
            self.next_expected_transmission_time = ts_before_sending_pkt + self.parent_runtime_params['send_interval_s'] * coglobs.SIU
            self._configure_guard_time()
            for _ in range(3):
                self._increase_guard_time()
            self._end_receive()
            return

        add_event(self.id, self.timestamp + self.config['switch_off_ms'], self._change_radio_state, STATE_OFF, SUBSTATE_NONE)
        add_event(self.id, self.timestamp + self.config['switch_off_ms'], self._change_node_state, STATE_SLEEP, SUBSTATE_NONE)
        # if NodeStats.check_if_all_nodes_are_discovered(self.timestamp) and coglobs.CONFIG['general']['quit_on_neighborhood_mapping_complete']:
        self._end_send_receive()

    def __check_if_received_from_parent(self, waiting_time_ms: int) -> None:
        if self.type == NODE_TYPE.NEW and self.new_node_runtime_params['first_pkt_rec_at'] < 0:
            return

        if self.rx_active:
            return

        interval_since_last_pkt = self.timestamp - self.child_runtime_params['last_pkt_from_parent_rec_at']
        # node did not receive a packet within an expected receive window
        if interval_since_last_pkt > self.child_runtime_params['guard_time_ms'] + self.detect_preamble_ms:
            self.rx_active = False
            self.rx_active_since = -1

            nr_of_lost_pkts = math.floor(interval_since_last_pkt / self.packet_delay)
            nr_of_lost_pkts = nr_of_lost_pkts if nr_of_lost_pkts > 0 else 1
            self._increase_guard_time()
            # TODO: verify if known_nodes or active_nodes
            known_nodes = self.known_nodes.keys()
            backup_parent_nodes = self.node_runtime_params['backup_parent_nodes']
            pkts_before_backoff = 3 + len(backup_parent_nodes) * 2
            self.next_expected_transmission_time = self.next_expected_transmission_time + self.packet_delay
            replacing_parent_node = False

            logger.info(
                self.timestamp, 
                f'{bcolors.WARNING}node_{self.id} did not receive expected packet!{bcolors.ENDC} ' \
                f'{bcolors.BWHITEDARK}Next possible for node_{self.id} packet arrival time: {format_ms(int(self.next_expected_transmission_time), coglobs.SIU)}{bcolors.ENDC}'
            )
            if coglobs.CONFIG['general']['quit_on_failure']:
                raise ClockDriftException(f'{bcolors.WARNING}node_{self.id} did not receive expected packet!{bcolors.ENDC}')

            # after three lost pkts the child node waits for the backup node to kick in - if there is any and if the backup node is known to the child node
            if nr_of_lost_pkts >= 3 and nr_of_lost_pkts < pkts_before_backoff:
                self.node_runtime_params['parent_node'] = -1
                bpn_index = 0 if nr_of_lost_pkts >= 3 and nr_of_lost_pkts < 6 else 1
                if self.child_runtime_params['is_backup_parent_node'] and self.child_runtime_params['backup_parent_node_index'] == bpn_index:
                    received_any_pkt = self.child_runtime_params['last_pkt_rec_at'] > self.child_runtime_params['last_pkt_from_parent_rec_at']
                    if not received_any_pkt:
                        replacing_parent_node = True

            elif nr_of_lost_pkts >= pkts_before_backoff:
                max_toa_ms = math.ceil(TOA.get_time_on_air(coglobs.CONFIG['lora']['payload_size']) * coglobs.SIU)
                add_event(self.id, self.timestamp + self.parent_config['max_send_interval_s'] * coglobs.SIU + max_toa_ms, self._check_if_should_perform_backoff)
                return

            # BPN waits for additional 2 * MAX_ToA to check if it can receive anything from other nodes
            if waiting_time_ms > self.child_runtime_params['guard_time_ms'] + self.detect_preamble_ms:
                waiting_time_ms -= self.child_runtime_params['guard_time_ms'] - self.detect_preamble_ms
                if replacing_parent_node:
                    add_event(self.id, self.timestamp + waiting_time_ms, self._replace_parent)
                else:
                    add_event(self.id, self.timestamp + waiting_time_ms, self._end_receive, self.child_config['op_duration_ms'])
                return
            
            self._end_receive(self.child_config['op_duration_ms'])

        return

    def __check_send_conditions(self) -> bool:
        if self.state.state is not STATE_ON:
            logger.warning(
                self.timestamp,
                f'Node can\'t send a message if it is off'
            )
            return False

        if self.state.radio_state is not STATE_ON:
            logger.warning(
                self.timestamp,
                f'Node can\'t send a message if its radio is off'
            )
            return False

        if self.transmission_allowed_at[self.lora_band.band] > coglobs.SIM_TIME:
            logger.warning(
                self.timestamp,
                f'{bcolors.WARNING}node_{self.id} is not allowed to transmit before {format_ms(self.next_transmission_time[self.lora_band.band], coglobs.SIU)}{bcolors.ENDC}'
            )
            return False

        if self.rx_active:
            logger.error(
                self.timestamp,
                f'{bcolors.FAIL}node_{self.id} is currently receiving packet. Sending a packet at the same time is not possible!{bcolors.ENDC}'
            )
            raise SimException()

        return True

    def __calculate_transmission_times(self, packet: BufferedPacket, send_interval: int) -> Tuple[float, int]:
        payload_size = len(packet['payload'])
        if payload_size > TX_PARAMS['max_payload']:
            if bool(TX_PARAMS['crc']):
                payload = struct.unpack(f'<BHBB{payload_size - LORALITE_HEADER_SIZE - coglobs.CONFIG["lora"]["crc_bytes"]}sH', packet['payload'])
            else:
                payload = struct.unpack(f'<BHBB{payload_size - LORALITE_HEADER_SIZE}s', packet['payload'])

            packet_payload = {
                'id': payload[0],
                'seq': payload[1], 
                'cmd': payload[2],
                'nr_of_ret': payload[3],
                'data': payload[4].decode()
            }

            if bool(TX_PARAMS['crc']):
                packet_payload['crc'] = payload[5]

            packet_as_string = ', '.join([f'{k}:{v}' for k, v in packet_payload.items()])

            logger.error(
                coglobs.SIM_TIME,
                f'{bcolors.FAIL}Packet payload is too big [{CMD(packet_payload["cmd"])}][{packet_as_string}]({payload_size}B) for SF{TX_PARAMS["sf"]} and BW {TX_PARAMS["bw"]}Hz{bcolors.ENDC}'
            )
            raise SimException()

        time_on_air = TOA.get_time_on_air(len(packet['payload']))
        time_on_air_ms = time_on_air * coglobs.SIU

        next_transmission_delay = math.ceil(time_on_air_ms / self.lora_band.duty_cycle - time_on_air_ms)
        self.transmission_allowed_at[self.lora_band.band] = self.timestamp + next_transmission_delay
        if self.type == NODE_TYPE.CHILD or self.type == NODE_TYPE.NEW:
            self.next_transmission_time[self.lora_band.band] = self.timestamp + next_transmission_delay
            return time_on_air, math.ceil(time_on_air_ms)

        # parent part. We need to check if config[parent][send_interval] is within allowed Duty Cycle
        if self.lora_band.band == LORA_MAIN_BAND:
            self.next_transmission_time[self.lora_band.band] = self.timestamp + send_interval * coglobs.SIU
            if self.type == NODE_TYPE.PARENT and next_transmission_delay > send_interval * coglobs.SIU:
                logger.info(self.timestamp, f"Send interval ({send_interval * coglobs.SIU}ms) is smaller than allowed by the duty cycle ({next_transmission_delay}ms) for selected LoRa parameters!")
                logger.info(self.timestamp, "Please fix the send interval and run the simulation again")

                raise SimException()

        return time_on_air, math.ceil(time_on_air_ms)

    @staticmethod
    def _convert_ids_to_bitmap(ids: list[int], size: int) -> str:
        if size > 0:
            diff = size % 8
            bitmap_size = size + 8 - diff if diff > 0 else size
        else:
            bitmap_size = 8
        bitmap = [0 for i in range(bitmap_size)]
        for id in ids:
            bitmap[id] = 1

        return ''.join([str(i) for i in bitmap])

    @staticmethod
    def _convert_bitmap_to_ids(bitmap: str) -> list[int]:
        return [i for i in range(len(bitmap)) if bitmap.startswith('1', i)]

    @staticmethod
    def _create_tdma_list(start_id: int, end_id: int, p_id: int) -> list[int]:
        left_list = [i for i in range(start_id, end_id + 1) if i != p_id]
        right_list = []
        if start_id > 0:
            right_list = [i for i in range(0, start_id) if i != p_id]

        tdma_list = left_list + right_list
        return tdma_list

    @staticmethod
    def _unpack_ids(id_string: str) -> list[int]:
        if len(id_string) == 0:
            return []

        ids = []
        parts = id_string.split(',')
        for part in parts:
            seq = part.split(':')
            if len(seq) == 2:
                id_r = [int(x) for x in seq]
                if id_r[0] < id_r[1]:
                    ids += [x for x in range(id_r[0], id_r[1] + 1)]
                else:
                    ids += [x for x in range(id_r[0], id_r[1] - 1, -1)]
                    
            if len(seq) == 1:
                ids.append(int(seq[0]))

        return ids

    @staticmethod
    def _shorten_ids(id_string: str) -> str:
        if len(id_string) == 0:
            return ''
            
        ids_str = id_string.split(',')
        ids = [int(x) for x in ids_str]

        res = []
        seq: list[int] = []
        prev = ids[0]
        if len(ids) > 1:
            growing = True if prev + 1 == ids[1] else False

        for id in ids:
            if len(seq) == 0:
                seq.append(id)
                prev = id
                continue
            
            growing = True if prev + 1 == id else False

            if id == prev + 1 and growing:
                seq.append(id)
            elif id == prev - 1 and not growing:
                seq.append(id)
            else:
                res.append(seq)
                seq = []
                seq.append(id)

            prev = id

        res.append(seq)
        short = []
        for r in res:
            if len(r) > 1:
                short.append(f'{r[0]}:{r[len(r) - 1]}')
            if len(r) == 1:
                short.append(f'{r[0]}')

        return ','.join(short)
