from __future__ import annotations
from typing import Dict, Literal, Tuple, TYPE_CHECKING
from loralite.simulator.definitions import *
from loralite.simulator.utils import bcolors, ROUND_N, round4
from loralite.simulator.state import State, StateDecoder
from loralite.simulator.logger import logger
from loralite.simulator.exceptions import SimException
import loralite.simulator.globals as coglobs
import json

if TYPE_CHECKING:
    from loralite.simulator.config import NodeEnergyCharacteristic, RadioEnergyCharacteristic

class Energy:
    # DEVICE default values for Sparkfun Arthemis Nano
    #
    # RADIO default values for sx1276 from Semtech datasheet:
    # https://www.mouser.com/datasheet/2/761/sx1276-1278113.pdf page 14
    #
    # pylint: disable=too-many-instance-attributes
    def __init__(self, node_energy_ch: NodeEnergyCharacteristic, radio_energy_ch: RadioEnergyCharacteristic, v_load_drop: float):
        self.d_sleep_a = node_energy_ch['sleep_a']
        self.d_on_a = node_energy_ch['on_a']
        self.d_op_a = node_energy_ch['op_a']
        self.d_v = node_energy_ch['v']
        self.d_sleep_w = self.d_v * self.d_sleep_a
        self.d_on_w = self.d_v * self.d_on_a
        self.d_op_w = self.d_v * self.d_op_a
        self.d_off_w = 0.0
        self.d_off_a = 0.0
        self.d_none_w = 0.0
        self.d_none_a = 0.0

        self.r_sleep_a = radio_energy_ch['sleep_a']
        self.r_on_a = radio_energy_ch['on_a']
        self.r_rx_a = radio_energy_ch['rx_a']
        self.r_tx_a = radio_energy_ch['tx_a']
        self.r_v = radio_energy_ch['v']
        self.r_sleep_w = self.r_v * self.r_sleep_a
        self.r_on_w = self.r_v * self.r_on_a
        self.r_off_w = 0.0
        self.r_off_a = 0.0
        self.r_none_w = 0.0
        self.r_none_a = 0.0
        self.r_rx_w = self.r_v * self.r_rx_a
        self.r_tx_w = self.r_v * self.r_tx_a
        self.v_load_drop = v_load_drop


    def calculate_energy_usage(self, ini_state: State, state_table: Dict[int, State], node_id: int, sim_time: int) -> None:
        sim_duration_ms = sim_time * coglobs.SIU
        mm = []
        # duration of given node/radio state & substate
        state_d: Dict[STATE_TYPE, Dict[ALL_STATES, int]] = {
            'state': {STATE_SLEEP: 0, STATE_ON: 0, STATE_OFF: 0},
            'substate': {SUBSTATE_NONE: 0, D_SUBSTATE_OP: 0},
            'radio_state': {STATE_SLEEP: 0, STATE_ON: 0, STATE_OFF: 0},
            'radio_substate': {SUBSTATE_NONE: 0, R_SUBSTATE_RX: 0, R_SUBSTATE_TX: 0}
        }

        # keeping previous state to compare in the loop
        prev_state_ts = {'state': 0, 'substate': 0, 'radio_state': 0, 'radio_substate': 0}
        prev_state = PrevState({'state': ini_state.state, 'substate': ini_state.substate, 'radio_state': ini_state.radio_state,
                      'radio_substate': ini_state.radio_substate})
        prev_state_node_type = ini_state.node_type

        # f = open(file_name, 'a')
        def _check_and_increase_state_d(state: State, state_type: STATE_TYPE) -> None:
            # if the current state if different than the previous state
            if prev_state[state_type] is not getattr(state, state_type):
                state_d[state_type][prev_state[state_type]] += round(state.timestamp - prev_state_ts[state_type])
                if state_type.find('radio') > -1:
                    r_a = getattr(self, f'r_{prev_state[state_type].lower()}_a')
                    r_v = self.r_v
                    if f'r_{prev_state[state_type].lower()}' in [R_SUBSTATE_RX, R_SUBSTATE_TX]:
                        r_v = round(r_v - self.v_load_drop, 3)
                    mm.append((prev_state_ts[state_type], state.timestamp, r_a, r_v))
                else:
                    d_a = getattr(self, f'd_{prev_state[state_type].lower()}_a')
                    d_v = self.d_v
                    if f'd_{prev_state[state_type].lower()}_a' in [STATE_ON, D_SUBSTATE_OP]:
                        d_v = round(d_v - self.v_load_drop, 3)
                        print(d_v)
                    mm.append((prev_state_ts[state_type], state.timestamp, d_a, d_v))
                prev_state[state_type] = getattr(state, state_type)
                prev_state_ts[state_type] = state.timestamp

        last_ts = 0.0
        for ts, state in state_table.items():
            _check_and_increase_state_d(state, 'state')
            _check_and_increase_state_d(state, 'substate')
            _check_and_increase_state_d(state, 'radio_state')
            _check_and_increase_state_d(state, 'radio_substate')
            prev_state_node_type = state.node_type
            last_ts = ts

        # additional calculation for the last state
        if last_ts < sim_duration_ms:
            state = State(node_id, prev_state_node_type, STATE_SIM_END, SUBSTATE_SIM_END, STATE_SIM_END, SUBSTATE_SIM_END)
            state.set_timestamp(sim_duration_ms)
            _check_and_increase_state_d(state, 'state')
            _check_and_increase_state_d(state, 'substate')
            _check_and_increase_state_d(state, 'radio_state')
            _check_and_increase_state_d(state, 'radio_substate')

        energy_used: Dict[Literal['node'] | Literal['radio'], Dict[ALL_STATES, float]] = {'node': {}, 'radio': {}}
        total_energy_used = 0.0
        logger.crucial(
            sim_duration_ms,
            f'{bcolors.HEADER}{bcolors.UNDERLINE}Energy usage for node_{node_id}{bcolors.ENDC}'
        )

        # for each state_type duration
        for state_type in state_d:
            for state_state in state_d[state_type]:
                # print(f'{state_type} {state_state}')
                duration = state_d[state_type][state_state]
                if state_type.find('radio') > -1:
                    joules = float(duration) / coglobs.SIU * getattr(self, f'r_{state_state.lower()}_w')
                    # joules1 = joules
                    # joules = float(duration) / globals.SIU * (getattr(self, f'r_{state_state.lower()}_a') * 
                    if state_state in [R_SUBSTATE_RX, R_SUBSTATE_TX] and self.v_load_drop > 0:
                        r_v = getattr(self, 'r_v') - self.v_load_drop
                        r_w = getattr(self, f'r_{state_state.lower()}_a') * r_v
                        # r_w_o = getattr(self, f'r_{state_state.lower()}_w')
                        joules = float(duration) / coglobs.SIU * r_w 
                        # joules2 = joules
                        # print(f'RADIO {state_state}: {joules1} <=> {joules2} [{r_w_o} <=> {r_w}]')

                    energy_used['radio'][state_state] = joules
                    info = f'\t{bcolors.HEADER}[RADIO][{state_type}][{state_state}]{bcolors.ENDC}'
                    logger.crucial(sim_duration_ms, f'{bcolors.HEADER}{info:40s}: {joules:.5f}J, {duration / coglobs.SIU}s / {round(sim_time, ROUND_N)}s{bcolors.ENDC}')
                    total_energy_used += joules
                    continue

                joules = float(duration) / coglobs.SIU * getattr(self, f'd_{state_state.lower()}_w')
                # joules1 = joules
                if state_state in [STATE_ON, D_SUBSTATE_OP] and self.v_load_drop > 0:
                    d_v = getattr(self, 'd_v') - self.v_load_drop
                    d_w = getattr(self, f'd_{state_state.lower()}_a') * d_v
                    # d_w_o = getattr(self, f'd_{state_state.lower()}_w')
                    joules = float(duration) / coglobs.SIU * d_w
                    # joules2 = joules
                    # print(f'DEVICE {state_state}: {joules1} <=> {joules2} [{d_w_o} <=> {d_w}]')

                energy_used['node'][state_state] = joules
                info = f'\t{bcolors.HEADER}[NODE][{state_type}][{state_state}]{bcolors.ENDC}'
                logger.crucial(sim_duration_ms, f'{bcolors.HEADER}{info:40s}: {joules:.5f}J, {duration / coglobs.SIU}s / {round(sim_time, ROUND_N)}s{bcolors.ENDC}')
                total_energy_used += joules

        # some additional conversions
        wh_to_j = 1 / WH
        total_j_to_wh = total_energy_used * wh_to_j
        total_mah = total_j_to_wh / self.d_v * 1000.0
        logger.crucial(
            sim_duration_ms,
            f'{bcolors.BOLD}{bcolors.HEADER}TOTAL ENERGY USED: {total_energy_used:.5f}J => {total_j_to_wh:.5f}Wh '
            f'=> {total_mah:.5f}mAh @ {self.d_v}V{bcolors.ENDC}\n'
        )


class EnergyAlt:
    energy: Dict[NODE_TYPE, Energy] = {}

    def add_energy(self, node_type: NODE_TYPE, energy: Energy) -> None:
        if not isinstance(node_type, NODE_TYPE):
            raise SimException(f'Given node type: {node_type} is not correct!')

        self.energy[node_type] = energy

    def calculate_energy_usage(self, ini_state: State, state_table: Dict[int, State], node_id: int, sim_time: int, print_energy: bool = True) -> Tuple[Dict[NODE_TYPE, float], Dict[Literal['ON', 'OFF', 'SLEEP', 'END', 'OP', 'NONE', 'END', 'ON', 'OFF', 'SLEEP', 'END', 'RX', 'TX', 'NONE', 'END'], int]]:
        # node state: NEW, CHILD and in some cases PARENT

        sim_duration_ms = sim_time * coglobs.SIU
        # duration of given node/radio state & substate
        state_in_type: Dict[NODE_TYPE, Dict[STATE_TYPE, Dict[ALL_STATES, int]]] = {}
        for type in NODE_TYPE:
            state_in_type[type] = {
                'state': {STATE_SLEEP: 0, STATE_ON: 0, STATE_OFF: 0},
                'substate': {SUBSTATE_NONE: 0, D_SUBSTATE_OP: 0},
                'radio_state': {STATE_SLEEP: 0, STATE_ON: 0, STATE_OFF: 0},
                'radio_substate': {SUBSTATE_NONE: 0, R_SUBSTATE_RX: 0, R_SUBSTATE_TX: 0}
        }

        # keeping previous state to compare in the loop
        prev_state_ts = {'state': ini_state.timestamp, 'substate': ini_state.timestamp, 'radio_state': ini_state.timestamp, 'radio_substate': ini_state.timestamp}
        prev_state = PrevState({'state': ini_state.state, 'substate': ini_state.substate, 'radio_state': ini_state.radio_state,
                      'radio_substate': ini_state.radio_substate})
        prev_state_node_type = ini_state.node_type
        
        # f = open(file_name, 'a')
        def _check_and_increase_state_d(state: State, state_type: STATE_TYPE) -> None:
            # if the current state if different than the previous state
            if prev_state[state_type] is not getattr(state, state_type):
                # state_d[state_type][prev_state[state_type]] += round(state.timestamp - prev_state_ts[state_type])
                state_in_type[prev_state_node_type][state_type][prev_state[state_type]] += round(state.timestamp - prev_state_ts[state_type])
                prev_state[state_type] = getattr(state, state_type)
                prev_state_ts[state_type] = state.timestamp
                # prev_state_ts[state_type] = state.node_type


        last_ts = 0.0
        if coglobs.SAVE_STATE_TO_FILE:
            for file_nr in range(0, coglobs.STATE_FILE_COUNT[node_id]):
                with open(f'{coglobs.OUTPUT_DIR}/state/{node_id}_{file_nr}', "r", encoding='utf-8') as outfile:
                    encoded = outfile.read()

                state_table = json.loads(encoded, object_hook=StateDecoder.decode)
                # state_table = jsonpickle.decode(encoded, keys=True)
                for ts, state in state_table.items():
                    _check_and_increase_state_d(state, 'state')
                    _check_and_increase_state_d(state, 'substate')
                    _check_and_increase_state_d(state, 'radio_state')
                    _check_and_increase_state_d(state, 'radio_substate')
                    prev_state_node_type = state.node_type
                    last_ts = ts

        else:
            for ts, state in state_table.items():
                _check_and_increase_state_d(state, 'state')
                _check_and_increase_state_d(state, 'substate')
                _check_and_increase_state_d(state, 'radio_state')
                _check_and_increase_state_d(state, 'radio_substate')
                prev_state_node_type = state.node_type
                last_ts = ts

        # additional calculation for the last state
        if last_ts < sim_duration_ms:
            state = State(node_id, prev_state_node_type, STATE_SIM_END, SUBSTATE_SIM_END, STATE_SIM_END, SUBSTATE_SIM_END)
            state.set_timestamp(sim_duration_ms)
            _check_and_increase_state_d(state, 'state')
            _check_and_increase_state_d(state, 'substate')
            _check_and_increase_state_d(state, 'radio_state')
            _check_and_increase_state_d(state, 'radio_substate')

        energy_used: Dict[NODE_TYPE, Dict[Literal['node'] | Literal['radio'], Dict[ALL_STATES, float]]] = {}
        for node_type in NODE_TYPE:
            energy_used[node_type] = {'node': {}, 'radio': {}}
        total_energy_used = {NODE_TYPE.NEW: 0.0, NODE_TYPE.JOINING: 0.0, NODE_TYPE.CHILD: 0.0, NODE_TYPE.TMP_PARENT: 0.0, NODE_TYPE.PARENT: 0.0}
        if print_energy: logger.crucial(sim_duration_ms, f'{bcolors.HEADER}{bcolors.UNDERLINE}Energy usage for node_{node_id}{bcolors.ENDC}')

        colors = {
            NODE_TYPE.PARENT: bcolors.HEADER,
            NODE_TYPE.CHILD: bcolors.HEADER2,
            NODE_TYPE.NEW: bcolors.HEADER3,
            NODE_TYPE.JOINING: bcolors.OKGREEN,
            NODE_TYPE.TMP_PARENT: bcolors.OKBLUE,
            None: bcolors.WARNING
        }

        total_duration_of_state = {}
        # for each state_type duration
        for node_type in state_in_type:
            for state_type in state_in_type[node_type]:
                for state_state in state_in_type[node_type][state_type]:
                    # print(f'{state_type} {state_state}')
                    duration = state_in_type[node_type][state_type][state_state]
                    if state_type.find('radio') > -1:
                        if state_state not in total_duration_of_state:
                            total_duration_of_state[state_state] = 0
                        total_duration_of_state[state_state] += duration
                        joules = float(duration) / coglobs.SIU * getattr(self.energy[node_type], f'r_{state_state.lower()}_w')
                        energy_used[node_type]['radio'][state_state] = joules
                        info = f'\t{colors[node_type]}[{node_type}][RADIO][{state_type}][{state_state}]{bcolors.ENDC}'
                        if print_energy: logger.crucial(sim_duration_ms, f'{colors[node_type]}{info:65s}: {joules:.5f}J, {duration / coglobs.SIU}s / {round4(sim_time)}s{bcolors.ENDC}')
                        total_energy_used[node_type] += joules
                        continue

                    joules = float(duration) / coglobs.SIU * getattr(self.energy[node_type], f'd_{state_state.lower()}_w')
                    energy_used[node_type]['node'][state_state] = joules
                    info = f'\t{colors[node_type]}[{node_type}][NODE][{state_type}][{state_state}]{bcolors.ENDC}'
                    if print_energy: logger.crucial(sim_duration_ms, f'{colors[node_type]}{info:65s}: {joules:.5f}J, {duration / coglobs.SIU}s / {round4(sim_time)}s{bcolors.ENDC}')
                    total_energy_used[node_type] += joules

        total_energy_used_for_all_node_type = 0.0
        wh_to_j = 1 / WH
        def _convert_energy(node_type: NODE_TYPE | None, total_energy_used_type: float, d_v: float) -> None:
            total_j_to_wh = total_energy_used_type * wh_to_j
            total_mah = total_j_to_wh / d_v * 1000.0
            node_type_enc = f'{bcolors.BOLD}{colors[node_type]}[{node_type}]'
            node_type_str = f'{node_type_enc:20s} ENERGY USED: ' if node_type is not None else f'TOTAL ENERGY USED: '
            new_line_ch = '\n' if node_type is None else ''
            if print_energy:
                logger.crucial(
                    sim_duration_ms,
                    f'{node_type_str}{total_energy_used_type:.5f}J => {total_j_to_wh:.5f}Wh '
                    f'=> {total_mah:.5f}mAh @ {d_v}V{bcolors.ENDC}{new_line_ch}'
                )
        
        last_d_v = 0.0
        energy_csv = ''
        for node_type in total_energy_used:
            _convert_energy(node_type, total_energy_used[node_type], self.energy[node_type].d_v)
            total_energy_used_for_all_node_type += total_energy_used[node_type]
            last_d_v = self.energy[node_type].d_v
            energy_csv += f'{total_energy_used[node_type]},'

        # energy_csv = energy_csv[:len(energy_csv) - 1]
        energy_csv += f'{total_energy_used_for_all_node_type}'
        with open(f'{coglobs.OUTPUT_DIR}/energy.csv', "a", encoding='utf-8') as outfile:
        # encoded = jsonpickle.encode(self.state_table, unpicklable=True, keys=True)
            outfile.write(f'{energy_csv}\n')

        _convert_energy(None, total_energy_used_for_all_node_type, last_d_v)

        return total_energy_used, total_duration_of_state

        