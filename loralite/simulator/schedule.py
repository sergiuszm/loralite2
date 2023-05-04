from __future__ import annotations
from typing import TYPE_CHECKING, Tuple, Dict
import math
from loralite.simulator.exceptions import SimException, NoException
from loralite.simulator.definitions import *
from random import choice, shuffle
from itertools import cycle
from string import ascii_uppercase
import loralite.simulator.globals as coglobs
from loralite.simulator.lora_phy import FCTRL, FHDR_SIZE, FPORT, FPORT_SIZE, MHDR, MHDR_SIZE, MIC_SIZE, LORALITE_HEADER_SIZE, BA_SIZE, PE_CT_SIZE, PE_SIZE
from loralite.simulator.toa import TOA
from loralite.simulator.utils import bits_little_endian_from_bytes, bytes_from_bits_little_endian
from loralite.simulator.node import Node
import struct

if TYPE_CHECKING:
    from loralite.simulator.lora_phy import Params
    from loralite.simulator.device import LoRaWANEndDevice


class Scheduler:
    def __init__(self, tx_params: Params, rx_sensitivity: int, subbands: Dict[float, Tuple[float, float, float, int]]):
        self.tx_params = tx_params
        self.rx_sensitivity = rx_sensitivity
        self.subbands = subbands

    def get_recommended_dw_cw(self, number_of_nodes: int) -> Tuple[int, int]:
        number_of_child_nodes = number_of_nodes - 1
        toa_c_ms = math.ceil(TOA.get_time_on_air(coglobs.CONFIG['lora']['payload_size']) * coglobs.SIU)
        bitmap_size = int(len(Node._convert_ids_to_bitmap([], number_of_nodes)) / 8)
        disc_req_size = LORALITE_HEADER_SIZE + coglobs.CONFIG['lora']['crc_bytes'] + BA_SIZE + bitmap_size
        toa_disc_ms = math.ceil(TOA.get_time_on_air(disc_req_size) * coglobs.SIU)
        rec_cw = math.ceil((toa_c_ms + coglobs.CONFIG['child']['reply_gt_ms'] + coglobs.CONFIG['radio']['mode_change_ms']) * number_of_child_nodes / coglobs.SIU)
        rec_dw = math.ceil((toa_disc_ms + coglobs.CONFIG['child']['reply_gt_ms'] + coglobs.CONFIG['radio']['mode_change_ms']) * number_of_child_nodes / coglobs.SIU)        
        print(f'Configured optimal lengths of dw: {rec_dw}s, and cw: {rec_cw}s! Requested with -c -d flags.')

        return rec_dw, rec_cw

    def find_smallest_cw(self, sim_seconds: int, number_of_nodes: int, bytes_to_send: int) -> Tuple[int, BaseException | None]:
        cw = int(coglobs.CONFIG['parent']['collect_window_s'])
        error = None
        while True:
            try:
                delay_s = self.get_longest_possible_interval(sim_seconds, number_of_nodes, bytes_to_send, cw)
                break
            except RuntimeError as e:
                if error is None:
                    error = e
                cw += 1
                continue

        print(f'Smallest allowed CW: {cw} with send_interval_s: {delay_s}')

        return cw, error

    def get_longest_possible_interval(self, sim_seconds: int, number_of_nodes: int, bytes_to_send: int, cw: int = 0) -> int:
        if bytes_to_send > 0:
            days = int(sim_seconds / 86400)
            toa_c_ms = math.ceil(TOA.get_time_on_air(coglobs.CONFIG['lora']['payload_size']) * coglobs.SIU)
            bitmap_size = int(len(Node._convert_ids_to_bitmap([], number_of_nodes)) / 8)
            disc_req_size = LORALITE_HEADER_SIZE + coglobs.CONFIG['lora']['crc_bytes'] + BA_SIZE + bitmap_size
            toa_disc_ms = math.ceil(TOA.get_time_on_air(disc_req_size) * coglobs.SIU)
            
            # rec_cw = math.ceil((toa_c_ms + globals.CONFIG['child']['reply_gt_ms'] + globals.CONFIG['radio']['mode_change_ms']) * (number_of_nodes - 1) / globals.CONFIG['general']['second_in_unit'])
            # rec_dw = math.ceil((toa_disc_ms + globals.CONFIG['child']['reply_gt_ms'] + globals.CONFIG['radio']['mode_change_ms']) * (number_of_nodes - 1) / globals.CONFIG['general']['second_in_unit'])

            if cw == 0:
                cw = coglobs.CONFIG['parent']['collect_window_s']

            packets_per_disc_window = math.floor(coglobs.CONFIG['parent']['disc_window_s'] * coglobs.CONFIG['general']['second_in_unit'] / (toa_disc_ms + coglobs.CONFIG['child']['reply_gt_ms'] + coglobs.CONFIG['radio']['mode_change_ms']))
            packets_per_collect_window =  math.floor(cw * coglobs.CONFIG['general']['second_in_unit'] / (toa_c_ms + coglobs.CONFIG['child']['reply_gt_ms'] + coglobs.CONFIG['radio']['mode_change_ms']))

            dcr_packets_count = math.ceil(bytes_to_send / coglobs.CONFIG['lora']['payload_size'])

            def _get_number_of_slots_for_cmd(for_cmd, packets_per_cmd):
                return math.ceil((number_of_nodes - 1) / packets_per_cmd)

            slots_per_disc_cmd = _get_number_of_slots_for_cmd(CMD_DISC, packets_per_disc_window)
            slots_per_collect_cmd = _get_number_of_slots_for_cmd(CMD_DATA_COLLECTION, packets_per_collect_window)

            dcr_packets_count = math.ceil(bytes_to_send / coglobs.CONFIG['lora']['payload_size']) * slots_per_collect_cmd

            possible_nr_of_cmd = dcr_packets_count + days + slots_per_disc_cmd * days
            possible_delay_s = math.floor((sim_seconds - coglobs.CONFIG['parent']['first_op_at_s']) / possible_nr_of_cmd)
            # the send delay can not be smaller than 
            minimum_allowed_delay_s = toa_c_ms / coglobs.CONFIG['general']['second_in_unit'] / self.subbands[self.tx_params['band']][2]
            if possible_delay_s < minimum_allowed_delay_s:
                cw = coglobs.CONFIG['parent']['collect_window_s']
                raise RuntimeError(f'It is not possible to request {bytes_to_send} bytes of data from {number_of_nodes - 1} ' \
                    f'EDs with a given CW: {cw}. Required send_interval_s == {possible_delay_s}. Minimum allowed send_interval_s == {minimum_allowed_delay_s}')
            print(f'Maximum allowed delay for the specified amount ({bytes_to_send}B) of data: {possible_delay_s}s!')
        else:
            possible_delay_s = int(coglobs.CONFIG['parent']['send_interval_s'])

        return possible_delay_s

    def generate_schedule_for_parent_data(self, sim_seconds: int, number_of_nodes: int, bytes_to_send: int, balance_energy : bool = True) -> Dict[int, Packet]:
        seq_max = 2**16 - 1
        days = int(sim_seconds / 86400)
        days = days if days > 0 else 1
        number_of_child_nodes = number_of_nodes - 1
        # toa_c_ms = math.ceil(TOA.get_time_on_air(coglobs.CONFIG['lora']['payload_size']) * coglobs.CONFIG['general']['second_in_unit'])
        # toa_disc_ms = math.ceil(TOA.get_time_on_air(len(f'{number_of_nodes + 1}#{coglobs.CONFIG["general"]["max_packet_nr"]}#{CMD_DISC_REPLY}##0#0:60'.encode('utf8'))) * coglobs.CONFIG['general']['second_in_unit'])
        # rec_cw = math.ceil((toa_c_ms + coglobs.CONFIG['child']['reply_gt_ms'] + coglobs.CONFIG['radio']['mode_change_ms']) * (number_of_nodes + 1) / coglobs.CONFIG['general']['second_in_unit'])
        # rec_dw = math.ceil((toa_disc_ms + coglobs.CONFIG['child']['reply_gt_ms'] + coglobs.CONFIG['radio']['mode_change_ms']) * (number_of_nodes + 1) / coglobs.CONFIG['general']['second_in_unit'])

        toa_c_ms = math.ceil(TOA.get_time_on_air(coglobs.CONFIG['lora']['payload_size']) * coglobs.SIU)
        bitmap_size = int(len(Node._convert_ids_to_bitmap([], number_of_nodes)) / 8)
        disc_req_size = LORALITE_HEADER_SIZE + coglobs.CONFIG['lora']['crc_bytes'] + BA_SIZE + bitmap_size
        toa_disc_ms = math.ceil(TOA.get_time_on_air(disc_req_size) * coglobs.SIU)
        rec_cw = math.ceil((toa_c_ms + coglobs.CONFIG['child']['reply_gt_ms'] + coglobs.CONFIG['radio']['mode_change_ms']) * number_of_child_nodes / coglobs.SIU)
        rec_dw = math.ceil((toa_disc_ms + coglobs.CONFIG['child']['reply_gt_ms'] + coglobs.CONFIG['radio']['mode_change_ms']) * number_of_child_nodes / coglobs.SIU)

        for x in range(1, number_of_nodes):
            per_x_cw = math.ceil((toa_c_ms + coglobs.CONFIG['child']['reply_gt_ms'] + coglobs.CONFIG['radio']['mode_change_ms']) * x / coglobs.CONFIG['general']['second_in_unit'])
            print(f'[CW][{x}]: {per_x_cw}')

        if coglobs.CONFIG['parent']['disc_window_s'] != rec_dw or coglobs.CONFIG['parent']['collect_window_s'] != rec_cw:
            print(f'Recommended dw: {rec_dw}s, cw: {rec_cw}s')

        delay_s = coglobs.CONFIG['parent']['send_interval_s']
        nr_of_cmd = math.floor((sim_seconds - coglobs.CONFIG['parent']['first_op_at_s']) / delay_s)
        nr_of_cmd_per_day = math.floor(nr_of_cmd / days)
        cmd_left = nr_of_cmd - days * nr_of_cmd_per_day

        packets_per_disc_window = math.floor(coglobs.CONFIG['parent']['disc_window_s'] * coglobs.CONFIG['general']['second_in_unit'] / (toa_disc_ms + coglobs.CONFIG['child']['reply_gt_ms'] + coglobs.CONFIG['radio']['mode_change_ms']))
        packets_per_collect_window =  math.floor(coglobs.CONFIG['parent']['collect_window_s'] * coglobs.CONFIG['general']['second_in_unit'] / (toa_c_ms + coglobs.CONFIG['child']['reply_gt_ms'] + coglobs.CONFIG['radio']['mode_change_ms']))

        dcr_packets_count = 0
        if bytes_to_send > 0:
            dcr_packets_count = math.ceil(bytes_to_send / coglobs.CONFIG['lora']['payload_size'])

        def _get_number_of_slots_for_cmd(for_cmd: Literal[1, 3], packets_per_cmd: int) -> int:
            return math.ceil(number_of_child_nodes / packets_per_cmd)

        slots_per_disc_cmd = _get_number_of_slots_for_cmd(CMD_DISC, packets_per_disc_window)
        slots_per_collect_cmd = _get_number_of_slots_for_cmd(CMD_DATA_COLLECTION, packets_per_collect_window)

        cmd_per_day = []
        for day in range(0, days):
            if cmd_left > 0:
                cmd_per_day.append([x for x in range(0, nr_of_cmd_per_day + slots_per_collect_cmd)])
                cmd_left -= slots_per_collect_cmd
                continue

            cmd_per_day.append([x for x in range(0, nr_of_cmd_per_day)])

        max_allowed_dcr_count = nr_of_cmd - days - slots_per_disc_cmd * days
        if bytes_to_send > 0:
            dcr_packets_count = math.ceil(bytes_to_send / coglobs.CONFIG['lora']['payload_size']) * slots_per_collect_cmd
        else:
            dcr_packets_count = math.floor((nr_of_cmd - days - slots_per_disc_cmd * days) / slots_per_collect_cmd)

        nr_of_dcr_per_day = math.floor(dcr_packets_count / days)
        if nr_of_dcr_per_day == 0:
            nr_of_dcr_per_day = 1
        dcr_left = dcr_packets_count - nr_of_dcr_per_day * days
        # nr_of_sync_cmd (days) - nr_of_disc_responses_cmd (slots_per_disc_cmd * days) - nr_of_scheduled_dc_responses_cmd (nr_of_dcr_per_day * days)
        cmd_left = (nr_of_cmd - days - slots_per_disc_cmd * days - nr_of_dcr_per_day * days)
        if dcr_left < 0:
            dcr_left = 0

        if dcr_packets_count > max_allowed_dcr_count:
            nr_of_cmd = dcr_packets_count + days + slots_per_disc_cmd * days
            delay_s = math.floor((sim_seconds - coglobs.CONFIG['parent']['first_op_at_s']) / nr_of_cmd)
            raise RuntimeError(f'It is not possible to request {bytes_to_send} bytes of data from {number_of_child_nodes}' \
                f'EDs with the current configuration. Needed DCRs: {dcr_packets_count}. Scheduled DCRs: {max_allowed_dcr_count}! ' \
                f'Maximum send_interval_s == {delay_s}!')

        if bytes_to_send > 0:
            possible_nr_of_cmd = dcr_packets_count + days + slots_per_disc_cmd * days
            possible_delay_s = math.floor((sim_seconds - coglobs.CONFIG['parent']['first_op_at_s']) / possible_nr_of_cmd)
            if possible_delay_s != delay_s:
                print(f'Maximum allowed delay for the specified amount ({bytes_to_send}B) of data: {possible_delay_s}s!')
            dcr_packets_count = math.ceil(bytes_to_send / coglobs.CONFIG['lora']['payload_size'])

        dcr_every_n_cmd = math.floor((nr_of_cmd - days - slots_per_disc_cmd * days) / (dcr_packets_count))
        if dcr_every_n_cmd > nr_of_cmd_per_day:
            dcr_every_n_cmd = nr_of_cmd_per_day - 1

        dc_count = dc_total_count = bytes_scheduled = count = 0
        current_cmd = previous_cmd = CMD_BEACON
        current_delay = delay_s
        nr_of_retransmissions = slots_to_schedule = dev_per_slot = 0
        data = ''
        schedule = {}
        dev_ids = [x for x in range(1, number_of_nodes)]
        d_slots = {}
        dc_slots = {}
        sync_free_slots = []
        orig_nr_of_dcr_per_day = nr_of_dcr_per_day
        def _count_slots(slots_list, slots_to_schedule, devs):
            if slots_to_schedule not in slots_list:
                slots_list[slots_to_schedule] = {'devs': devs, 'count': 0}

            slots_list[slots_to_schedule]['count'] += 1
            return slots_list

        d_slots_balancing = {}
        dc_slots_balancing = {}
        dev_stats = {}
        for i in range(1, number_of_nodes):
            dev_stats[i] = {'c': 0, 'b': 0}

        def _balance_slots(cyclic_dev_list, dc=False):
            new_order = next(cyclic_dev_list)
            if dc:
                for id in new_order:
                    dev_stats[id]['c'] += 1
                    dev_stats[id]['b'] += coglobs.CONFIG['lora']['payload_size']

            return ','.join([str(x) for x in new_order])

        def _balance_devs(cnt, devs):
            all = []
            for d in devs:
                all += d
            # new_order = [all[-1]] + all[:-1]
            new_order = all[1:] + all[:1]

            nr_slots = len(cnt) - 1
            dev_assigned = 0
            for i in range(0, len(cnt)):
                if i == 0:
                    devs[i] = new_order[:cnt[i]]
                elif i == nr_slots:
                    devs[i] = new_order[dev_assigned:]
                else:
                    devs[i] = new_order[dev_assigned:dev_assigned + cnt[i]]

                dev_assigned += len(devs[i])

            return devs

        def _get_balanced_list_of_devs(slots_per_window):
            it = 1
            iit = 0
            cyclic_devs = []
            condition = []
            is_gen_done = False
            all_devs = [x for x in range(1, number_of_nodes)]
            # slots_to_schedule = slots_per_collect_cmd
            nodes = []
            cnt = []
            while len(all_devs) > 0:
                slot_devs = all_devs[:slots_per_window]
                cnt.append(len(slot_devs))
                nodes.append(slot_devs)
                del all_devs[:slots_per_window]
            
            while True:
                iit = 1
                for node in nodes:
                    if it == 1 and len(condition) == 0:
                        condition = node
                    if it > 1 and condition == node and iit == 1:
                        is_gen_done = True
                        break
                    cyclic_devs.append(node)
                    iit += 1
                if is_gen_done:
                    break
                it += 1
                nodes = _balance_devs(cnt, nodes)
            
            return cyclic_devs

        # d_balanced_list_of_devs = _get_balanced_list_of_devs(packets_per_disc_window)
        # dc_balanced_list_of_devs = _get_balanced_list_of_devs(packets_per_collect_window)

        d_balanced_list_of_devs = cycle(_get_balanced_list_of_devs(packets_per_disc_window))
        dc_balanced_list_of_devs = cycle(_get_balanced_list_of_devs(packets_per_collect_window))

        count, seq = 0, 0
        days_separator = []
        data_str = ''
        for day in range(0, days):
            dc_count = 0
            for cmd_nr in cmd_per_day[day]:
                if cmd_nr == 0:
                    if day > 0:
                        days_separator.append(count - 1)
                    current_cmd = CMD_BEACON
                    # data = f'{current_delay}|{current_delay}'
                    data = current_delay.to_bytes(2, byteorder='little') + current_delay.to_bytes(2, byteorder='little')
                    data_str = f'{current_delay}|{current_delay}'
                    nr_of_dcr_per_day = orig_nr_of_dcr_per_day
                elif cmd_nr == 1:
                    current_cmd = CMD_DISC
                    slots_to_schedule = slots_per_disc_cmd
                    dev_per_slot = packets_per_disc_window
                    dev_ids = [x for x in range(1, number_of_nodes)]
                    data = ','.join([str(x) for x in dev_ids[:dev_per_slot]])
                    orig_data = data
                    if balance_energy:
                        data = _balance_slots(d_balanced_list_of_devs)
                    dev_ids = [int(x) for x in data.split(',')]
                    d_slots = _count_slots(d_slots, slots_to_schedule, data)
                    data_str = f'0|{orig_data}|{dev_ids[0]}|{max(dev_ids)}'
                    bitmap = bytes_from_bits_little_endian(Node._convert_ids_to_bitmap(dev_ids, max(dev_ids)))
                    data = struct.pack(f'<B{len(bitmap)}sBB', 0, bitmap, dev_ids[0], max(dev_ids))
                    slots_to_schedule -= 1
                elif slots_to_schedule > 0:
                    current_cmd = previous_cmd
                    del dev_ids[:dev_per_slot]
                    data = ','.join([str(x) for x in dev_ids[:dev_per_slot]])
                    orig_data = data
                    if current_cmd == CMD_DATA_COLLECTION:
                        if balance_energy:
                            data = _balance_slots(dc_balanced_list_of_devs, True)
                        else:
                            for x in dev_ids[:dev_per_slot]:
                                dev_stats[x]['c'] += 1
                                dev_stats[x]['b'] += coglobs.CONFIG['lora']['payload_size']
                        dev_ids = [int(x) for x in data.split(',')]
                        dc_slots = _count_slots(dc_slots, slots_to_schedule, data)
                        data_str = f'{data}|{dev_ids[0]}|{max(dev_ids)}'
                        bitmap = bytes_from_bits_little_endian(Node._convert_ids_to_bitmap(dev_ids, max(dev_ids)))
                        data =  struct.pack(f'<{len(bitmap)}sBB', bitmap, dev_ids[0], max(dev_ids))
                    else:
                        if balance_energy:
                            data = _balance_slots(d_balanced_list_of_devs)
                        d_slots = _count_slots(d_slots, slots_to_schedule, data)
                        dev_ids = [int(x) for x in data.split(',')]
                        data_str = f'0|{orig_data}|{dev_ids[0]}|{max(dev_ids)}'
                        bitmap = bytes_from_bits_little_endian(Node._convert_ids_to_bitmap(dev_ids, max(dev_ids)))
                        data = struct.pack(f'<B{len(bitmap)}sBB', 0, bitmap, dev_ids[0], max(dev_ids))
                    slots_to_schedule -= 1
                    if current_cmd == CMD_DATA_COLLECTION and number_of_child_nodes == slots_per_collect_cmd and bytes_scheduled >= bytes_to_send:
                        slots_to_schedule = len([x for x in dev_stats if dev_stats[x]['b'] < bytes_to_send])
                elif (
                    cmd_nr > 1 
                    and (cmd_nr % dcr_every_n_cmd == 0 or slots_to_schedule == 0) 
                    and (bytes_scheduled < bytes_to_send or bytes_to_send == 0) 
                    and (dc_count < nr_of_dcr_per_day or (slots_per_collect_cmd == 1 and dcr_left < days and bytes_to_send == 0))
                ):
                    if dc_count >= nr_of_dcr_per_day and (slots_per_collect_cmd == 1 and dcr_left < days and bytes_to_send == 0):
                        dcr_left -= 1
                    current_cmd = CMD_DATA_COLLECTION
                    slots_to_schedule = slots_per_collect_cmd
                    dev_per_slot = packets_per_collect_window
                    dev_ids = [x for x in range(1, number_of_nodes)]
                    data = ','.join([str(x) for x in dev_ids[:dev_per_slot]])
                    if number_of_child_nodes == slots_to_schedule:
                        bytes_scheduled = max([dev_stats[x]['b'] for x in dev_stats])
                    bytes_scheduled += coglobs.CONFIG['lora']['payload_size']
                    
                    if balance_energy:
                        data = _balance_slots(dc_balanced_list_of_devs, True)
                    else:
                        for x in dev_ids[:dev_per_slot]:
                            dev_stats[x]['c'] += 1
                            dev_stats[x]['b'] += coglobs.CONFIG['lora']['payload_size']
                    dc_slots = _count_slots(dc_slots, slots_to_schedule, data)
                    dev_ids = [int(x) for x in data.split(',')]
                    data_str = f'{data}|{dev_ids[0]}|{max(dev_ids)}'
                    bitmap = bytes_from_bits_little_endian(Node._convert_ids_to_bitmap(dev_ids, max(dev_ids)))
                    data =  struct.pack(f'<{len(bitmap)}sBB', bitmap, dev_ids[0], max(dev_ids))
                    slots_to_schedule -= 1
                    dc_count += 1
                    dc_total_count += 1
                else:
                    current_cmd = CMD_BEACON
                    data = current_delay.to_bytes(2, byteorder='little') + current_delay.to_bytes(2, byteorder='little')
                    data_str = f'{current_delay}|{current_delay}'
                    sync_free_slots.append(count)

                if len(data_str) == 0:
                    data_str = data

                schedule[count] = {'seq': seq, 'cmd': current_cmd, 'nr_of_ret': 0, 'mm_part': 0, 'mm_count': 0, 'data': data, 'data_str': data_str}
                previous_cmd = current_cmd
                count += 1
                seq += 1
                data_str = ''

                if seq == seq_max:
                    seq = 0

        # for id in dev_stats:
        #     print(f'[{id}]: {dev_stats[id]} -> {bytes_to_send}')

        shuffle(sync_free_slots)
        dcr_left = 0
        for slot in dc_slots:
            dcr_left += dcr_packets_count - dc_slots[slot]['count']
            dc_slots[slot]['dcr_left'] = dcr_packets_count - dc_slots[slot]['count']

        if dcr_left <= len(sync_free_slots) and dcr_left > 0:
            for slot in dc_slots:
                dcr_left = dc_slots[slot]['dcr_left']
                for x in range(0, dcr_left):
                    dc_slots[slot]['count'] += 1
                    cmd_nr = sync_free_slots.pop()
                    data = dc_slots[slot]['devs']
                    if balance_energy:
                        data = _balance_slots(dc_balanced_list_of_devs, True)
                    else:
                        for x in dev_ids[:dev_per_slot]:
                            dev_stats[x]['c'] += 1
                            dev_stats[x]['b'] += coglobs.CONFIG['lora']['payload_size']
                    dev_ids = [int(x) for x in data.split(',')]
                    data_str = f'{data}|{dev_ids[0]}|{max(dev_ids)}'
                    bitmap = bytes_from_bits_little_endian(Node._convert_ids_to_bitmap(dev_ids, max(dev_ids)))
                    data =  struct.pack(f'<{len(bitmap)}sBB', bitmap, dev_ids[0], max(dev_ids))
                    schedule[cmd_nr] = {'seq': cmd_nr, 'cmd': CMD_DATA_COLLECTION, 'nr_of_ret': 0, 'mm_part': 0, 'mm_count': 0, 'data': data, 'data_str': data_str}
                
                dc_slots[slot]['dcr_left'] = 0

        if coglobs.CONFIG['general']['save_schedule_to_file']:
            file_name = f'{coglobs.CONFIG["general"]["data_dir_path"]}/schedule.txt'
            f = open(file_name, 'a')

            count = 0
            for cmd_nr in schedule:
                if cmd_nr == 0:
                    f.write(f'Day: {count}\n')
                    count += 1

                if cmd_nr - 1 in days_separator:
                    f.write(f'\nDay: {count}\n')
                    count += 1
                packet = schedule[cmd_nr]
                info = f'[{schedule[cmd_nr]["seq"]:3}]: {packet["cmd"]} | {current_delay} | {packet["nr_of_ret"]:1} | {packet["mm_part"]:1} | {packet["mm_count"]:1} | {packet["data_str"]:30}'
                f.write(f'{info}\n')

            f.close()

        print(f'[SYNC]: {days + len(sync_free_slots)}')

        if len(d_slots) == 0:
            raise RuntimeError(f'Problem with DISC schedule: not a single DISC scheduled!')

        for slot in d_slots:
            print(f'[DISC][{d_slots[slot]["devs"]:30}]: {d_slots[slot]["count"]} | {days}')
            if d_slots[slot]['count'] != days:
                raise RuntimeError(f'Problem with DISC schedule: [{d_slots[slot]["devs"]}][{d_slots[slot]["count"]}] vs {days}')

        if len(dc_slots) == 0:
            raise RuntimeError(f'Problem with DC schedule: not a single DC scheduled!')

        # for slot in dc_slots:
        #     print(f'[DCOL][{dc_slots[slot]["devs"]:30}]: {dc_slots[slot]["count"]} | {dcr_packets_count} | {dc_slots[slot]["count"] * globals.CONFIG["lora"]["payload_size"]}B')
        #     if dc_slots[slot]['count'] != dcr_packets_count:
        #         raise RuntimeError(f'Problem with DC schedule: [{dc_slots[slot]["devs"]}][{dc_slots[slot]["count"]}] vs {dcr_packets_count}')

        for id in dev_stats:
            print(f'[DCOL][{id}]: {dev_stats[id]["c"]} | {dcr_packets_count} || {dev_stats[id]["b"]} -> {bytes_to_send}')
            if dev_stats[id]['b'] < bytes_to_send or dev_stats[id]['c'] != dcr_packets_count:
                raise RuntimeError(f'Problem with DC schedule: [{id}][{dev_stats[id]["c"]}] vs {dcr_packets_count}')

        # for id in dev_stats:
        #     print(f'[{id}]: {dev_stats[id]} -> {bytes_to_send}')

        return schedule

    def get_longest_possible_interval_for_lwan(self, sim_seconds: int, bytes_to_send: int) -> int:
        if bytes_to_send > 0:
            paktes_count = math.floor(bytes_to_send / coglobs.CONFIG['lora']['payload_size'])
            toa_s = TOA.get_time_on_air(coglobs.CONFIG['lora']['payload_size'])
            toa_ms = toa_s * coglobs.CONFIG['general']['second_in_unit']
            delay_ms = math.ceil(toa_ms / self.subbands[self.tx_params['band']][2])
            nr_pkts = math.ceil(sim_seconds * coglobs.CONFIG['general']['second_in_unit'] / delay_ms)

            if paktes_count > nr_pkts:
                raise RuntimeError('Defined bytes_to_send impossible to transmit within a given amount of time')

            if paktes_count < nr_pkts:
                delay_ms = math.floor(sim_seconds * coglobs.CONFIG['general']['second_in_unit'] / (paktes_count + 1))

            delay_s = math.ceil(delay_ms / coglobs.CONFIG['general']['second_in_unit'])
        else:
            delay_s = coglobs.CONFIG['lwaned']['send_interval_s']

        return delay_s

    def generate_schedule_for_lwan(self, dev: LoRaWANEndDevice, sim_seconds: int, bytes_to_send: int) -> Tuple[int, Dict[int, Dict[int, str]]]:
        schedule = {}

        payload = ''.join(choice(ascii_uppercase) for i in range(coglobs.CONFIG['lora']['payload_size']))
        if bytes_to_send > 0:
            paktes_count = math.ceil(bytes_to_send / coglobs.CONFIG['lora']['payload_size'])
            toa_s = TOA.get_time_on_air(coglobs.CONFIG['lora']['payload_size'])
            toa_ms = toa_s * coglobs.CONFIG['general']['second_in_unit']
            delay_ms = math.ceil(toa_ms / dev.lora_band.duty_cycle)
            nr_pkts = math.ceil(sim_seconds * coglobs.CONFIG['general']['second_in_unit'] / delay_ms)

            if paktes_count > nr_pkts:
                raise RuntimeError('Defined bytes_to_send impossible to transmit within a given amount of time')

            if paktes_count < nr_pkts:
                delay_ms = math.floor(sim_seconds * coglobs.CONFIG['general']['second_in_unit'] / (paktes_count + 1))

            print(f'Calculated delay for the specified amount ({bytes_to_send}B) of data: {delay_ms}s!')
        else:
            delay_ms = coglobs.CONFIG['lwaned']['send_interval_s'] * coglobs.CONFIG['general']['second_in_unit']
            paktes_count = math.ceil(sim_seconds * coglobs.CONFIG['general']['second_in_unit'] / delay_ms)

        if coglobs.CONFIG['general']['save_schedule_to_file']:
            file_name = f'{coglobs.CONFIG["general"]["data_dir_path"]}/schedule_ed_{dev.id}.txt'
            f = open(file_name, 'a')

        delay_s = math.ceil(delay_ms / coglobs.CONFIG["general"]["second_in_unit"])
        total_bytes = 0
        scheduled_bytes = 0
        for i in range(0, paktes_count):
            tmp_payload = payload
            total_bytes += len(tmp_payload)

            if bytes_to_send > 0 and total_bytes > bytes_to_send:
                diff = total_bytes - bytes_to_send
                tmp_payload = ''.join(choice(ascii_uppercase) for i in range(coglobs.CONFIG['lora']['payload_size'] - diff))

            info = f'[{i:3}]: {delay_s} | {payload:15}'
            if coglobs.CONFIG['general']['save_schedule_to_file']:
                f.write(f'{info}\n')
            schedule[i] = {'seq': i, 'data': tmp_payload}
            scheduled_bytes += len(tmp_payload)

        if coglobs.CONFIG['general']['save_schedule_to_file']:
            f.close()

        print(f'[LWANED_{dev.id}]: scheduled {scheduled_bytes}B to send')

        return delay_s, schedule

    def generate_schedule_for_lwan_new(self, dev: LoRaWANEndDevice, sim_seconds: int, bytes_to_send: int) -> Tuple[int, Dict[int, Dict[int, str]]]:
        schedule = {}
        seq_max = 2**16 - 1
        predefined_frame_size = MHDR_SIZE + FHDR_SIZE + FPORT_SIZE + MIC_SIZE + coglobs.CONFIG['lora']['crc_bytes']
        frmpayload_size = coglobs.CONFIG['lora']['payload_size'] - predefined_frame_size

        payload = SAMPLE_DATA[:frmpayload_size]
        if bytes_to_send > 0:
            paktes_count = math.ceil(bytes_to_send / coglobs.CONFIG['lora']['payload_size'])
            toa_s = TOA.get_time_on_air(coglobs.CONFIG['lora']['payload_size'])
            toa_ms = toa_s * coglobs.SIU
            delay_ms = math.ceil(toa_ms / dev.lora_band.duty_cycle)
            nr_pkts = math.ceil(sim_seconds * coglobs.SIU / delay_ms)

            if paktes_count > nr_pkts:
                raise RuntimeError('Defined bytes_to_send impossible to transmit within a given amount of time')

            if paktes_count < nr_pkts:
                delay_s = math.floor(sim_seconds / (paktes_count + 1))
                # delay_ms = math.floor(sim_seconds * coglobs.SIU / (paktes_count + 1))

            print(f'Calculated delay for the specified amount ({bytes_to_send}B) of data: {delay_ms}s!')
        else:
            # delay_ms = coglobs.CONFIG['lwaned']['send_interval_s'] * coglobs.SIU
            # paktes_count = math.ceil(sim_seconds * coglobs.SIU / delay_ms)
            delay_s = coglobs.CONFIG['lwaned']['send_interval_s']
            paktes_count = math.ceil(sim_seconds / delay_s)

        if coglobs.CONFIG['general']['save_schedule_to_file']:
            file_name = f'{coglobs.CONFIG["general"]["data_dir_path"]}/schedule_ed_{dev.id}.txt'
            f = open(file_name, 'a')

        # delay_s = math.ceil(delay_ms / coglobs.SIU)
        total_bytes = 0
        scheduled_bytes = 0
        f_count = 0
        for i in range(0, paktes_count):
            tmp_payload = payload
            total_bytes += len(tmp_payload) + predefined_frame_size

            if bytes_to_send > 0 and total_bytes > bytes_to_send:
                diff = total_bytes - bytes_to_send
                tmp_payload = SAMPLE_DATA[:coglobs.CONFIG['lora']['payload_size'] - predefined_frame_size - diff]

            packet_before_mic = struct.pack(f'<BIBHB{len(tmp_payload)}s', MHDR, dev.id, FCTRL, f_count, FPORT, tmp_payload.encode())
            mic = coglobs.CRC32(packet_before_mic)
            packet_before_crc = struct.pack(f'<BIBHB{len(tmp_payload)}sL', MHDR, dev.id, FCTRL, f_count, FPORT, tmp_payload.encode(), mic)
            crc = coglobs.CRC16(packet_before_crc)
            packet = struct.pack(f'<BIBHB{len(tmp_payload)}sLH', MHDR, dev.id, FCTRL, f_count, FPORT, tmp_payload.encode(), mic, crc)
            packet_s = packet.decode('iso-8859-1')
            # tmp_packet = struct.pack(f'<BIBHB{len(tmp_payload)}sIH', MHDR, dev.id, FCTRL, f_count, FPORT, tmp_payload, )
            info = f'[{i:3}]: {delay_s} | {packet_s:51}'
            if coglobs.CONFIG['general']['save_schedule_to_file']:
                f.write(f'{info}\n')
            schedule[i] = {'seq': i, 'data': packet}
            scheduled_bytes += len(tmp_payload)
            f_count += 1

            if f_count == seq_max:
                f_count = 0

        if coglobs.CONFIG['general']['save_schedule_to_file']:
            f.close()

        print(f'[LWANED_{dev.id}]: scheduled {scheduled_bytes}B to send')

        return delay_s, schedule