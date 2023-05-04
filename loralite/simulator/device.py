# from globals import SIM_TIME, LIST_OF_DEVICES, LORAWAN_GW
from typing import Tuple, Dict
import loralite.simulator.globals as coglobs
from loralite.simulator.lora_phy import FHDR_SIZE, FPORT_SIZE, MHDR_SIZE, MIC_SIZE, LoraBand, LORA_BAND_48, SF_12, TX_PARAMS, RX_SENSITIVITY
from sortedcontainers import SortedList
from loralite.simulator.state import State
from copy import deepcopy
from loralite.simulator.event import add_event
from loralite.simulator.logger import logger
from loralite.simulator.definitions import *
from loralite.simulator.propagation_loss_model import PROPAGATION_MODEL
from loralite.simulator.propagation_delay_model import DELAY_MODEL
from loralite.simulator.utils import *
# from config import CONFIG
from loralite.simulator.toa import TOA
import math
from loralite.simulator.mobility import get_distance
from loralite.simulator.exceptions import SimException
from loralite.simulator.energy import Energy, EnergyAlt
from random import choice
from string import ascii_uppercase
from deprecated import deprecated
import struct

@deprecated(reason="Moved LoRaLitE classes to Node class")
class Device:
    def __init__(self, nr: int, position, type):
        self.id = nr
        self.type = type
        self.position = position
        self.state = State(self.id, self.type)
        self.state_table = {}
        self.lora_band = LoraBand(LORA_BAND_48, SF_12)
        self.packets_sent = 0
        self.packets_received = 0
        self.sent_pkt_seq = -1
        self.last_pkt_rec_at = 0
        self.received_pkt_payload = None
        self.sent_pkt_payload = None
        self.bytes_sent = 0
        self.bytes_received = 0
        self.next_transmission_time = 0
        self.receive_buff = []
        self.dc_bytes_sent = 0
        self.total_expected_recv_count = 0
        self.d = 0
        self.dc = 0
        self.current_event_timestamp = 0
        self.previous_event_timestamp = 0
        self.cd_negative = False
        # self.event_table = {}
        # self.event_list = SortedList()
        # self.receive_events = SortedList()
        self.timestamp = 0

        self.initial_state = deepcopy(self.state)
        self.config = {
            'switch_on_duration': coglobs.CONFIG['node']['sch_on_duration_ms'],    # how long in s it takes to turn on node
            'switch_off_duration': coglobs.CONFIG['node']['sch_off_duration_ms']   # how long in s it takes to turn off node
        }

        # saving initial Device state
        self._save_state()
        # scheduling an event at timestamp 0 that will print basic information about the Device
        add_event(self.id, 0, self._info)

    def _save_state(self):
        self.state_table[self.state.timestamp] = deepcopy(self.state)
        logger.debug(
            self.state.timestamp,
            f'SAVING STATE. d_state: {self.state.state}, d_substate: {self.state.substate}, '
            f'r_state: {self.state.radio_state}, r_substate: {self.state.radio_substate}'
        )

    def _change_node_state(self, state, substate=None):
        State.check_state(state)
        # no changes to the current state
        if self.state.state == state and self.state.substate == substate and self.type == self.state.node_type:
            return

        old_state = self.state.state
        self.state.state = state
        self.state.set_timestamp(self.timestamp)

        if substate is not None:
            State.check_node_substate(substate)
            old_substate = self.state.substate
            self.state.substate = substate
            logger.info(self.timestamp, f'node_{self.id} node state: {old_state} => {state}, substate: {old_substate} => {substate}')

        if substate is None:
            logger.info(self.timestamp, f'node_{self.id} node state: {old_state} => {state}, substate: {self.state.substate}')

        self._save_state()

    def _change_radio_state(self, state, substate=None):
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

        self._save_state()

    def _scheduled_log(self, log_func, msg):
        log_func(self.timestamp, msg)

    def _info(self):
        logger.info(
            coglobs.SIM_TIME,
            f'node_{self.id}, \tTYPE:{type(self).__name__}, \tSTATE: {self.state.state}, '
            f'\tRADIO_STATE: {self.state.radio_state}, \tPOSITION: {self.position}'
        )

    def add_packet_to_buffer(self, packet):
        if self.state.state in [STATE_OFF, STATE_SLEEP]:
            logger.info(self.timestamp, f'Device node_{self.id} is either OFF or SLEEPING. Dropping packet')
            return

        if self.state.radio_state in [STATE_OFF, STATE_SLEEP]:
            logger.info(self.timestamp, f'Device node_{self.id} radio is either OFF or in sleep state. Dropping packet')
            return

        if self.state.radio_substate is not R_SUBSTATE_RX:
            logger.info(self.timestamp, f'Device node_{self.id} radio is not in RX substate. Dropping packet')
            return

        self.receive_buff.append(packet)
        add_event(self.id, self.timestamp, self._receive)

    # def _send(self, sch_packet):
    #     if self.__check_send_conditions() is False:
    #         return

    #     packet_payload = '#'.join([str(sch_packet[x]) for x in sch_packet])
    #     packet = {'payload': f"{self.id}#{packet_payload}", 'rx_dbm': 0}
    #     send_interval = 0
    #     if self.type == NODE_TYPE.PARENT:
    #         send_interval = self.config['send_interval']

    #     time_on_air_ms = self.__calculate_transmission_times(packet, send_interval)
    #     if time_on_air_ms is False:
    #         self._change_radio_state(STATE_OFF, SUBSTATE_NONE)
    #         self._change_node_state(STATE_OFF, SUBSTATE_NONE)
    #         return

    #     self._change_node_state(STATE_ON, D_SUBSTATE_OP)
    #     self._change_radio_state(STATE_ON, R_SUBSTATE_TX)
    #     self.packets_sent += 1
    #     self.bytes_sent += len(packet['payload'].encode('utf8'))
    #     if sch_packet['cmd'] == CMD_DATA_COLLECTION_REPLY:
    #         self.dc_bytes_sent += len(packet['payload'].encode('utf8'))

    #     if self.type == NODE_TYPE.PARENT and sch_packet['cmd'] != CMD_BEACON:
    #         self.recv_count = 0
    #         self.expected_recv_count = len(Device._unpack_ids(sch_packet['data']))
    #         self.total_expected_recv_count += len(Device._unpack_ids(sch_packet['data']))
    #     self.sent_pkt_seq = sch_packet['seq']
    #     self.sent_pkt_payload = sch_packet

    #     logger.info(self.timestamp, f'{bcolors.OKBLUE}node_{self.id} is sending packet with seq_nr {self.sent_pkt_seq}...{bcolors.ENDC}')

    #     for id in coglobs.LIST_OF_NODES:
    #         node = coglobs.LIST_OF_NODES[id]

    #         # skip itself
    #         if self.id == node.id:
    #             continue

    #         if self.type is not NODE_TYPE.PARENT:
    #             if node.type is not NODE_TYPE.PARENT:
    #                 continue

    #         distance = get_distance(self, node)
    #         delay = DELAY_MODEL.get_delay(self, node)
    #         rx_dbm, info = PROPAGATION_MODEL.get_rx_power(self, node, self.lora_band.tx_dbm)
    #         logger.debug(self.timestamp, f'Propagation for node_{node.id}: {info}')
    #         node_packet = deepcopy(packet)
    #         node_packet['rx_dbm'] = rx_dbm

    #         logger.debug(
    #             self.timestamp,
    #             f'Params for node_{node.id}: txPower={self.lora_band.tx_dbm}dbm, rxPower={rx_dbm}dbm, '
    #             f'distance={distance}m, delay=+{round(delay * 1000000, ROUND_N)}ns'
    #         )

    #         receive_time = self.timestamp + time_on_air_ms
    #         add_event(node.id, receive_time, node.add_packet_to_buffer, node_packet)
            
    #     add_event(self.id, self.timestamp + time_on_air_ms, self._scheduled_log, logger.info, f'{bcolors.OKBLUE}...node_{self.id} has finished sending the message.{bcolors.ENDC}')
    #     add_event(
    #         self.id,
    #         self.timestamp + time_on_air_ms, self._scheduled_log, logger.info,
    #         f'Next allowed transmission time for node_{self.id}: {format_ms(self.next_transmission_time, coglobs.SIU)}'
    #             # f'{int((self.next_transmission_time - self.next_transmission_time % globals.SIU) / globals.SIU):,}' \
    #             # f'.{self.next_transmission_time % globals.SIU}s'
    #     )

    #     # here is the difference between commands
    #     # - sync works as before
    #     # - discovery and data collection have to have listening window

    #     if self.type == NODE_TYPE.PARENT and sch_packet['cmd'] == CMD_BEACON:
    #         self._end_sync(time_on_air_ms)
    #         return 

    #     if self.type == NODE_TYPE.PARENT:
    #         receive_window = coglobs.CONFIG['parent']['collect_window_s']
    #         color = bcolors.BCYAN
    #         cmd_name = 'DATA COLLECTION'
    #         if sch_packet['cmd'] == CMD_DISC:
    #             receive_window = coglobs.CONFIG['parent']['disc_window_s']
    #             color = bcolors.BBLUE
    #             cmd_name = 'DISC'

    #         add_event(self.id, self.timestamp + time_on_air_ms, self._scheduled_log, logger.info, f'{color}Waiting for {cmd_name} responses from nodes with ID: {sch_packet["data"]}{bcolors.ENDC}')
    #         add_event(self.id, self.timestamp + time_on_air_ms + coglobs.CONFIG['radio']['mode_change_ms'], self._change_radio_state, STATE_ON, R_SUBSTATE_RX)
    #         self.receive_window = {
    #             'start': self.timestamp + time_on_air_ms + coglobs.CONFIG['radio']['mode_change_ms'],
    #             'end': self.timestamp + time_on_air_ms + coglobs.CONFIG['radio']['mode_change_ms'] + receive_window * coglobs.SIU}
    #         add_event(self.id, self.receive_window['end'], self._check_if_received_all)
    #         # add_event(self.id, self.timestamp + time_on_air_ms, self._scheduled_log, logger.info, f'{color}RECEIVE WINDOW: {self.receive_window["start"]:,} - {self.receive_window["end"]:,}{bcolors.ENDC}')
    #         add_event(self.id, self.timestamp + time_on_air_ms, self._scheduled_log, logger.info, f'{color}RECEIVE WINDOW: {format_ms(self.receive_window["start"], coglobs.SIU)} - {format_ms(self.receive_window["end"], coglobs.SIU)}{bcolors.ENDC}')

    #         # self._continue_receive()
    #         return 

    #     self._end_receive(time_on_air_ms)

    def _can_receive(self, timestamp: int, subband: float, packet: BufferedPacket) -> bool:
        return True

    def mark_preamble_detected(self) -> None:
        pass

    # def __check_send_conditions(self) -> bool:
    #     # it should not happen
    #     # TODO: what do we do it that case
    #     if self.type is NODE_TYPE.PARENT and self.next_transmission_time > coglobs.SIM_TIME:
    #         logger.warning(
    #             self.timestamp,
    #             f'There is something wrong with the schedule. NTT[{self.next_transmission_time}] '
    #             f'>= SIM_TIME[{coglobs.SIM_TIME}]'
    #         )
    #         return False

    #     if self.state.state is not STATE_ON:
    #         logger.warning(
    #             self.timestamp,
    #             f'Device can\'t send a message if it is off'
    #         )
    #         return False

    #     if self.state.radio_state is not STATE_ON:
    #         logger.warning(
    #             self.timestamp,
    #             f'Device can\'t send a message if its radio is off'
    #         )
    #         return False

    #     if self.next_transmission_time > coglobs.SIM_TIME:
    #         logger.warning(
    #             self.timestamp,
    #             f'{bcolors.WARNING}node_{self.id} is not allowed to transmitt before {format_ms(self.next_transmission_time, coglobs.SIU)}{bcolors.ENDC}'
    #             # f'{int((self.next_transmission_time - self.next_transmission_time % globals.SIU) / globals.SIU):,}' \
    #             # f'.{self.next_transmission_time % globals.SIU}s{bcolors.ENDC}'
    #         )
    #         return False

    #     return True

    # def __calculate_transmission_times(self, packet: BufferedPacket, send_interval: int) -> int:
    #     payload_size = len(packet['payload'].encode('utf8'))
    #     if payload_size > TX_PARAMS['max_payload']:
    #         logger.error(
    #             coglobs.SIM_TIME,
    #             f'Packet payload is too big ({payload_size}B) for SF{TX_PARAMS["sf"]} and BW {TX_PARAMS["bw"]}Hz'
    #         )
    #         raise SimException()

    #     time_on_air = TOA.get_time_on_air(len(packet['payload'].encode('utf8')))
    #     time_on_air_ms = time_on_air * coglobs.SIU

    #     next_transmission_delay = math.ceil(time_on_air_ms / self.lora_band.duty_cycle - time_on_air_ms)
    #     if self.type == NODE_TYPE.CHILD:
    #         self.next_transmission_time = self.timestamp + next_transmission_delay
    #         return math.ceil(time_on_air_ms)

    #     # GW part. We need to check if config[child][send_interval] is within allowed Duty Cycle
    #     self.next_transmission_time = self.timestamp + send_interval * coglobs.SIU
    #     if self.type == NODE_TYPE.PARENT and next_transmission_delay > send_interval * coglobs.SIU:
    #         logger.info(self.timestamp, f"Send interval ({send_interval * coglobs.SIU}ms) is smaller than allowed by the duty cycle ({next_transmission_delay}ms) for selected LoRa parameters!")
    #         logger.info(self.timestamp, "Please fix the send interval and run the simulation again")

    #         raise SimException()        

    #     return math.ceil(time_on_air_ms)

    # @staticmethod
    # def _unpack_ids(id_string):
    #     def _get_ids(part):
    #         id_r = part.split(':')
    #         id_r = [int(x) for x in id_r]
    #         if len(id_r) == 1:
    #             return id_r
    #         if len(id_r) == 2:
    #             return [x for x in range(id_r[0], id_r[len(id_r) - 1] + 1)]

    #     ids = []
    #     parts = id_string.split(',')
    #     if len(parts) == 2:
    #         ids += _get_ids(parts[0])
    #         ids += _get_ids(parts[1])
    #     if len(parts) == 1:
    #         ids = _get_ids(parts[0])

    #     return ids

class LoRaWANGateway(Device):
    def __init__(self, nr: int, position: list[int]):
        self.nr_of_retransmissions = 0
        self.predefined_frame_size = MHDR_SIZE + FHDR_SIZE + FPORT_SIZE + MIC_SIZE + coglobs.CONFIG['lora']['crc_bytes']
        self.energy = Energy(
            coglobs.CONFIG['energy']['node'][coglobs.CONFIG['lwangw']['platform']], 
            coglobs.CONFIG['energy']['radio'][coglobs.CONFIG['lwangw']['radio_type']],
            coglobs.CONFIG['energy']['v_load_drop']
        )

        super().__init__(nr, position, LWAN_DEV_TYPE.GW)

        self._change_node_state(STATE_ON)
        self._change_radio_state(STATE_ON, R_SUBSTATE_RX)

    def _receive(self):
        if self.state.state is STATE_OFF:
            return

        if self.state.radio_state is STATE_OFF:
            return

        if len(self.receive_buff) > 1:
            raise RuntimeError('There should be exactly 1 packet in the receive buffer! Something is wrong.')
        
        packet = self.receive_buff.pop(0)
        sensitivity = RX_SENSITIVITY[self.lora_band.sf]

        # dropping packet if its sensitivity is below receiver sensitivity
        if packet['rx_dbm'] < sensitivity:
            logger.info(
                self.timestamp,
                f'Packet dropped by node_{self.id}. Packet rx_dbm {packet["rx_dbm"]} dBm is below receiver sensitivity '
                f'{sensitivity} dBm.'
            )
            return

        self.packets_received += 1
        packet_len = len(packet['payload'])
        self.bytes_received += packet_len
        payload_len = packet_len - self.predefined_frame_size
        # mhdr, dev_id, fctrl, f_count, fport, payload, mic, crc = 0, 0, 0, 0, 0, '', 0, 0
        mhdr, dev_id, fctrl, f_count, fport, payload, mic, crc = struct.unpack(f'<BIBHB{payload_len}sLH', packet['payload'])
        packet_as_string = f'MHDR:{mhdr}, DEV_ADDR:{dev_id}, FCtrl:{fctrl}, FCnt:{f_count}, FPort:{fport}, FRMPayload:{payload!r}, MIC:{mic}, CRC:{crc}'
        logger.info(self.timestamp, f'{bcolors.OKGREEN}Packet received by GW_{self.id}: {packet["payload"]!r} [{packet_as_string}] [{packet_len}B] with RSSI: {packet["rx_dbm"]} dBm{bcolors.ENDC}')


class LoRaWANEndDevice(Device):
    def __init__(self, nr: int, position: list[int]):
        self.packet_schedule: Dict[int, Dict[int, str]] = {}
        self.rx1 = {}
        self.rx2 = {}
        self.rx1_timeout = False
        self.rx2_timeout = False
        self.last_packet = False
        self.energy = Energy(
            coglobs.CONFIG['energy']['node'][coglobs.CONFIG['lwaned']['platform']], 
            coglobs.CONFIG['energy']['radio'][coglobs.CONFIG['lwaned']['radio_type']],
            coglobs.CONFIG['energy']['v_load_drop']
        )

        super().__init__(nr, position, LWAN_DEV_TYPE.END_DEV)
        self.config['send_interval'] = coglobs.CONFIG['lwaned']['send_interval_s'] * coglobs.SIU
        self.config['send_delay'] = coglobs.CONFIG['lwaned']['send_delay_s'] * coglobs.SIU
        self.config['rx_window'] = math.ceil(TOA.get_symbols_time() * coglobs.SIU) #5 symbols required to detect the preamble

        first_op_at_s = coglobs.CONFIG['lwaned']['first_op_at_s']
        first_op_at_s += first_op_at_s + coglobs.CONFIG['lwaned']['separation_s'] * self.id - 1
        first_op_at_ms = first_op_at_s * coglobs.SIU

        add_event(self.id, self.timestamp + first_op_at_ms - coglobs.CONFIG['node']['sch_on_duration_ms'], self._change_node_state, STATE_ON)
        add_event(self.id, self.timestamp + first_op_at_ms - coglobs.CONFIG['node']['sch_on_duration_ms'], self._change_radio_state, STATE_ON)
        add_event(self.id, self.timestamp + first_op_at_ms, self._execute_packet_schedule)
       

    def _execute_packet_schedule(self):
        pkt_seq = self.sent_pkt_seq + 1
        if len(self.packet_schedule) == 0:
            return
        else:
            packet = self.packet_schedule[pkt_seq]
            del self.packet_schedule[pkt_seq]

            if len(self.packet_schedule) == 0:
                self.last_packet = True

        self._send(packet)

    def _send(self, sch_packet):
        packet = {'payload': sch_packet['data'], 'rx_dbm': 0}
        time_on_air_ms = math.ceil(TOA.get_time_on_air(len(sch_packet['data'])) * coglobs.SIU)
        next_transmission_delay = math.ceil(time_on_air_ms / self.lora_band.duty_cycle - time_on_air_ms)
        self.next_transmission_time = self.timestamp + next_transmission_delay

        self._change_node_state(STATE_ON, D_SUBSTATE_OP)
        self._change_radio_state(STATE_ON, R_SUBSTATE_TX)
        self.packets_sent += 1
        self.bytes_sent += len(packet['payload'])
        self.sent_pkt_seq = int.from_bytes(packet['payload'][6:8], 'little')
        self.sent_pkt_payload = sch_packet

        logger.info(self.timestamp, f'{bcolors.OKBLUE}node_{self.id} is sending packet with seq_nr {self.sent_pkt_seq}...{bcolors.ENDC}')

        distance = get_distance(self, coglobs.LORAWAN_GW)
        delay = DELAY_MODEL.get_delay(self, coglobs.LORAWAN_GW)
        rx_dbm, info = PROPAGATION_MODEL.get_rx_power(self, coglobs.LORAWAN_GW, self.lora_band.tx_dbm)
        logger.debug(self.timestamp, f'Propagation for GW_{coglobs.LORAWAN_GW.id}: {info}')
        node_packet = deepcopy(packet)
        node_packet['rx_dbm'] = rx_dbm

        logger.debug(
            self.timestamp,
            f'Params for GW_{coglobs.LORAWAN_GW.id}: txPower={self.lora_band.tx_dbm}dbm, rxPower={rx_dbm}dbm, '
            f'distance={distance}m, delay=+{round(delay * 1000000, ROUND_N)}ns'
        )

        receive_time = int(round(self.timestamp + time_on_air_ms, 0))
        add_event(coglobs.LORAWAN_GW.id, receive_time, coglobs.LORAWAN_GW.add_packet_to_buffer, node_packet)

        add_event(self.id, self.timestamp + time_on_air_ms, self._scheduled_log, logger.info, f'{bcolors.OKBLUE}...node_{self.id} has finished sending the message.{bcolors.ENDC}')
        add_event(self.id, 
            self.timestamp + time_on_air_ms, self._scheduled_log, logger.info,
            f'Next allowed transmission time for node_{self.id}: {format_ms(self.next_transmission_time, coglobs.SIU)}'
        )

        if self.timestamp + self.config['send_interval'] < self.next_transmission_time:
            raise RuntimeError(f'Send interval is too small for node_{self.id}!') 

        # we keep the radio in TX mode as long as ToA duration of the packet
        add_event(self.id, self.timestamp + time_on_air_ms + coglobs.CONFIG['radio']['mode_change_ms'], self._change_radio_state, STATE_OFF, SUBSTATE_NONE)
        add_event(self.id, self.timestamp + time_on_air_ms + coglobs.SIU - coglobs.CONFIG['radio']['mode_change_ms'], self._change_radio_state, STATE_ON, R_SUBSTATE_RX)

        self.rx1 = {
            'start': self.timestamp + time_on_air_ms + coglobs.SIU,
            'end': self.timestamp + time_on_air_ms + coglobs.SIU + self.config['rx_window']}

        add_event(self.id, self.rx1['end'] + coglobs.CONFIG['radio']['mode_change_ms'], self._change_radio_state, STATE_OFF, SUBSTATE_NONE)

        self.rx2 = {
            'start': self.rx1['end'] + coglobs.SIU,
            'end': self.rx1['end'] + coglobs.SIU + self.config['rx_window']}

        add_event(self.id, self.rx2['start'] - coglobs.CONFIG['radio']['mode_change_ms'], self._change_radio_state, STATE_ON, R_SUBSTATE_RX)
        add_event(self.id, self.rx2['end'] + coglobs.CONFIG['node']['sch_off_duration_ms'], self._change_radio_state, STATE_OFF, SUBSTATE_NONE)
        add_event(self.id, self.rx2['end'] + coglobs.CONFIG['node']['sch_off_duration_ms'], self._change_node_state, STATE_SLEEP, SUBSTATE_NONE)

        if not self.last_packet:
            # we need to prepare schedule for the next transmission
            add_event(self.id, self.timestamp + self.config['send_interval'] - self.config['switch_on_duration'] + self.config['send_delay'], self._change_node_state, STATE_ON, SUBSTATE_NONE)            
            add_event(self.id, self.timestamp + self.config['send_interval'] - self.config['switch_on_duration'] + self.config['send_delay'], self._change_radio_state, STATE_ON, SUBSTATE_NONE)
            add_event(self.id, self.timestamp + self.config['send_interval'] + self.config['send_delay'], self._execute_packet_schedule)

        self.rx1_timeout = False
        self.rx2_timeout = False

        # we schedule _receive() 1s after transmission (LoRaWAN specification)
        # add_event(self.id, self.rx1['start'], self._receive)

    # def _receive(self):
    #     if self.state.state is STATE_OFF:
    #         return

    #     if self.state.radio_state is STATE_OFF:
    #         return

    #     # no packet
    #     msg_in_buffer = False
    #     if len(self.receive_buff) > 0:
    #         msg_in_buffer = True

    #     if len(self.receive_buff) > 1:
    #         raise RuntimeError('There should be exactly 1 packet in the receive buffer! Something is wrong.')

    #     #we have a specified receive-window where we expect the packet(s) to arrive
    #     if not msg_in_buffer and not self.rx1_timeout and self.rx1['start'] <= self.timestamp <= self.rx1['end']:
    #         add_event(self.id, self.timestamp + config['general']['sim_sensitive_part_resolution'], self._receive)
    #         return
    #     elif not self.rx1_timeout:
    #         self.rx1_timeout = True
    #         return

    #     if not msg_in_buffer and not self.rx2_timeout and self.rx2['start'] <= self.timestamp <= self.rx2['end']:
    #         add_event(self.id, self.timestamp + config['general']['sim_sensitive_part_resolution'], self._receive)
    #         return
    #     elif not self.rx2_timeout:
    #         self.rx2_timeout = True
    #         return

    #     if self.rx1_timeout and self.rx2_timeout:
    #         return

    #     #we are outside receive-window
    #     if not msg_in_buffer:
    #         return

    #     packet = self.receive_buff.pop(0)
    #     sensitivity = RX_SENSITIVITY[self.lora_band.sf]

    #     # dropping packet if its sensitivity is below receiver sensitivity
    #     if packet['rx_dbm'] < sensitivity:
    #         logger.info(
    #             self.timestamp,
    #             f'Packet dropped by node_{self.id}. Packet rx_dbm {packet["rx_dbm"]} dBm is below receiver sensitivity '
    #             f'{sensitivity} dBm.'
    #         )
    #         return

    #     self.packets_received += 1
    #     self.bytes_received += len(packet['payload'].encode('utf8'))
    #     logger.info(self.timestamp, f'{bcolors.OKGREEN}Packet received by node_{self.id}: {packet["payload"]} with RSSI: {packet["rx_dbm"]} dBm{bcolors.ENDC}')
