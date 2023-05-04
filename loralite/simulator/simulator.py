from __future__ import annotations

from typing import Dict
from sortedcontainers import SortedDict
from loralite.simulator import _DATA, _ROOT
from loralite.simulator.collision_helper import InTheAir
from loralite.simulator.event import add_new_node_event, add_detached_event
from loralite.simulator.exceptions import ClockDriftException, ClockDriftIssue
import loralite.simulator.globals as coglobs
import math
from loralite.simulator.logger import CRUCIAL, logger
from loralite.simulator.mobility import calculate_distance_matrix, generate_coordinates, plot_coordinates, plot_coordinates_for_scenarios, calculate_distance_simple
from loralite.simulator.node import Node
from loralite.simulator.schedule import Scheduler
import json
import argparse
from datetime import datetime
import traceback
from loralite.simulator.definitions import *
from loralite.simulator.config import load_config, save_config
from loralite.simulator.device import *
from loralite.simulator.lora_phy import *
from loralite.simulator.propagation_loss_model import PROPAGATION_MODEL
from loralite.simulator.toa import TOA
from random import randint
from oslo_concurrency import lockutils
from loralite.simulator.utils import round1, round2
from loralite.simulator.packet_loss_helper import set_packet_loss_modulo, set_packet_loss_probability, calculate_prr, set_nr_of_packets_to_lose_in_a_row

# sys.stdout = open('data/cw.log','a')w
lockutils.set_defaults(f'{_DATA}')

def log_exception(data_dir: str, e: Exception, tb: str) -> None:
    with open(f'{data_dir}/error.log', 'a') as outfile:
        from datetime import datetime
        dt = datetime.fromtimestamp(time())
        date = dt.strftime('%Y-%m-%d %H:%M:%S')
        outfile.write(f'[{date}]: {coglobs.COMMAND_LINE}\n')
        outfile.write(f'{e}\n')
        outfile.write(f'{tb}\n\n')

def log_drift_failure(case: int) -> None:
    with open(f'data/drift_case.log', 'a') as outfile:
        outfile.write(f'{coglobs.CONFIG["general"]["cdppm"],coglobs.CONFIG["child"]["guard_time_ms"],coglobs.CONFIG["parent"]["send_interval_s"],case}\n')

def log_drift_issue(node_id: int, timestamp: int) -> None:
    with open(f'data/drift_issue.log', 'a') as outfile:
        outfile.write(f'{coglobs.COMMAND_LINE}\n')
        outfile.write(f'[{node_id}]: {format_ms(timestamp, coglobs.SIU)}\n\n')

def set_clock_drift_direction(pcd: bool, cdp: bool, cdc: bool) -> None:
    if pcd and (cdp or cdc):
        if cdp:
            parent_cd_negative = True
            child_cd_negative = False
        elif cdc:
            parent_cd_negative = False
            child_cd_negative = True
        for id in coglobs.LIST_OF_NODES:
            node = coglobs.LIST_OF_NODES[id]
            node.cd_negative = parent_cd_negative if node.type is NODE_TYPE.PARENT else child_cd_negative

def set_specific_clock_drift_direction(node_id: int, negative: bool = True) -> None:
    coglobs.LIST_OF_NODES[node_id].cd_negative = negative

def save_execution_command(path: str, with_date: bool = True) -> None:
    with open(path, 'a') as outfile:
        from datetime import datetime
        dt = datetime.fromtimestamp(time())
        date = dt.strftime('%Y-%m-%d %H:%M:%S')
        if with_date:
            outfile.write(f'[{date}]: {coglobs.COMMAND_LINE}\n')
        else:
            outfile.write(f'{coglobs.COMMAND_LINE}\n')            

@lockutils.synchronized('scenario_info', external=True)
def save_scenario_info(energy_per_node: Dict[int, Dict[NODE_TYPE, float]], duration_per_node: Dict[int, Dict[str, int]], scenario: str, nr_of_nodes: int) -> None:
    try:
        with open(f'{data_dir}/scenario.json', "r", encoding='utf-8') as f:
            scenario_info = json.load(f)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        scenario_info = {}

    try:
        with open(f'{data_dir}/mapping.json', "r", encoding='utf-8') as f:
            mapping = json.load(f)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        mapping = {}

    cmd_interval = coglobs.CONFIG['parent']['send_interval_s']
    tni = coglobs.CONFIG['parent']['network_info_send_interval_s']
    sim_time = coglobs.CONFIG['general']['sim_duration_s']
    en = coglobs.CONFIG['general']['number_of_expected_nodes']
    # unp = coglobs.CONFIG['parent']['unknown_nodes_portion']
    di = coglobs.CONFIG['scenarios']['scenario_ge_4']['deployment_interval_s']
    ndm = coglobs.CONFIG['scenarios']['scenario_ge_4']['network_detection_multipler']
    dpe = '' if not coglobs.CONFIG['scenarios']['scenario_ge_4']['parent_election_disabled'] else '_dpe'
    json_key = f'{nr_of_nodes}_{en}_{cmd_interval}_{ndm}_{tni}_{di}_{sim_time}{dpe}'

    first_node = True
    for node_id in energy_per_node:
        if scenario not in scenario_info:
            scenario_info[scenario] = {}

        if first_node:
            scenario_info[scenario][json_key] = {}
            scenario_info[scenario][json_key]['mapping_time_s'] = float(coglobs.ALL_NODES_DISCOVERED_IN) / coglobs.SIU
            scenario_info[scenario][json_key]['deployment_interval_s'] = coglobs.CONFIG['scenarios']['scenario_ge_4']['deployment_interval_s']
            scenario_info[scenario][json_key]['nr_of_collisions'] = coglobs.NUMBER_OF_COLLISIONS
            scenario_info[scenario][json_key]['nodes'] = {} 
            first_node = False

        scenario_info[scenario][json_key]['nodes'][node_id] = {
            'energy': round2(sum([energy_per_node[node_id][node_type] for node_type in energy_per_node[node_id]])),
            'rx_s': round2(duration_per_node[node_id]['RX'] / coglobs.SIU),
            'tx_s': round2(duration_per_node[node_id]['TX'] / coglobs.SIU),
            'deployed_at_s': math.ceil(coglobs.LIST_OF_NODES[node_id].new_node_runtime_params['deployed_at'] / coglobs.SIU),
            'map': ','.join([str(x) for x in coglobs.LIST_OF_NODES[node_id].known_nodes])
        }
        
    import re
    with open(f'{data_dir}/scenario.json', "w", encoding='utf-8') as outfile:
        scenario_info = {key: val for key, val in sorted(scenario_info.items(), key = lambda ele: natural_keys(ele[0]))}
        scenario_info[scenario] = {key: val for key, val in sorted(scenario_info[scenario].items(), key = lambda ele: natural_keys(ele[0]))}
        # outfile.write(json.dumps(scenario_info, indent=2))
        output_to_write = json.dumps(scenario_info, indent=2)
        output_to_write = re.sub('\s+(\"mapping_time_s\":\s\d+.\d+,)', r'\1', output_to_write)
        output_to_write = re.sub('\s+(\"deployment_interval_s\":\s\d+,)', r'\1', output_to_write)
        output_to_write = re.sub('\s+(\"nr_of_collisions\":\s\d+,)', r'\1', output_to_write)
        output_to_write = re.sub('\s+(\"map\":\s\".*\")\s+(},+)', r' \1\2', output_to_write)
        output_to_write = re.sub('\s+(\"map\":\s\".*\")\s+(})\s+(})', r' \1\2\3', output_to_write)
        output_to_write = re.sub('\s+(\"deployed\_at_s\":\s\d+,)', r' \1', output_to_write)
        output_to_write = re.sub('\s+(\"tx_s\":\s.*)', r' \1', output_to_write)
        output_to_write = re.sub('\s+(\"rx_s\":\s.*)', r' \1', output_to_write)
        output_to_write = re.sub('\s+(\"energy\":\s.*)', r'\1', output_to_write)
        outfile.write(output_to_write)

    if len(coglobs.DISCOVERY_STATUS) > 0:
        json_key = f'{scenario}_{json_key}'
        if json_key not in mapping:
            mapping[json_key] = {}

        for timestamp in coglobs.DISCOVERY_STATUS:
            ts = str(round2(timestamp / coglobs.SIU))
            if ts not in mapping[json_key]:
                mapping[json_key][f'{ts}_{coglobs.DISCOVERY_SEQ[str(timestamp)]}'] = {}

            for node_id in coglobs.DISCOVERY_STATUS[timestamp]:
                node: Node = coglobs.LIST_OF_NODES[node_id]
                mapping[json_key][f'{ts}_{coglobs.DISCOVERY_SEQ[str(timestamp)]}'][node_id] = {
                    'known_nodes': f'[{", ".join([str(x) for x in coglobs.DISCOVERY_STATUS[timestamp][node_id]])}]',
                    'dp_at': round2(node.new_node_runtime_params['deployed_at'] / coglobs.SIU),
                    'nn_until': round2(node.new_node_runtime_params['new_node_until'] / coglobs.SIU),
                    'jn_until': round2(node.new_node_runtime_params['joining_node_until'] / coglobs.SIU)
                }

        mapping = {key: val for key, val in sorted(mapping.items(), key = lambda ele: natural_keys(ele[0]))}

        with open(f'{data_dir}/mapping.json', "w", encoding='utf-8') as outfile:
            outfile.write('{\n')
            last_key = next(reversed(mapping.keys()))
            for json_key in mapping:
                outfile.write(f'\t"{json_key}": {{\n')
                mapping[json_key] = {key: val for key, val in sorted(mapping[json_key].items(), key = lambda ele: natural_keys(ele[0]))}

                last_timestamp = next(reversed(mapping[json_key].keys()))
                # last_timestamp = f'{last_timestamp}_{coglobs.DISCOVERY_SEQ[last_timestamp]}'
                for timestamp in mapping[json_key]:
                    outfile.write(f'\t\t"{timestamp}": {{\n')
                    last_node_id = next(reversed(mapping[json_key][timestamp].keys()))
                    for node_id in mapping[json_key][timestamp]:
                        if node_id == last_node_id:
                            outfile.write(
                                f'\t\t\t"{node_id}": {{ "known_nodes": {mapping[json_key][timestamp][node_id]["known_nodes"]},' \
                                    f' "dp_at": {mapping[json_key][timestamp][node_id]["dp_at"]}, "nn_until": {mapping[json_key][timestamp][node_id]["nn_until"]},' \
                                    f' "jn_until": {mapping[json_key][timestamp][node_id]["jn_until"]} }}\n')
                        else:
                            outfile.write(
                                f'\t\t\t"{node_id}": {{ "known_nodes": {mapping[json_key][timestamp][node_id]["known_nodes"]},' \
                                    f' "dp_at": {mapping[json_key][timestamp][node_id]["dp_at"]}, "nn_until": {mapping[json_key][timestamp][node_id]["nn_until"]},' \
                                    f' "jn_until": {mapping[json_key][timestamp][node_id]["jn_until"]} }},\n')
                    if f'{timestamp}' == last_timestamp:
                        outfile.write('\t\t}\n')
                    else:
                        outfile.write('\t\t},\n')
                if json_key == last_key:
                    outfile.write('\t}\n')
                else:
                    outfile.write('\t},\n')
            outfile.write('}\n')

@lockutils.synchronized('energy_lock', external=True)
def save_energy_usage(energy_per_node: Dict[int, Dict[NODE_TYPE, float]], scenario: str, ini_nt: NETWORK_STATE, nr_of_nodes: int) -> None:
    try:
        with open(f'{data_dir}/energy.json', "r", encoding='utf-8') as f:
            energy_json = json.load(f)
    except FileNotFoundError:
        energy_json = {}

    first_node = True
    for node_id in energy_per_node:
        cmd_interval = coglobs.CONFIG['parent']['send_interval_s']
        tni = coglobs.CONFIG['parent']['network_info_send_interval_s']
        sim_time = coglobs.CONFIG['general']['sim_duration_s']
        en = coglobs.CONFIG['general']['number_of_expected_nodes'] - 1
        # unp = coglobs.CONFIG['parent']['unknown_nodes_portion']
        json_key = f'{nr_of_nodes}_{en}_{cmd_interval}_{tni}_{sim_time}'

        if scenario not in energy_json:
            energy_json[scenario] = {}

        if ini_nt not in energy_json[scenario]:
            energy_json[scenario][ini_nt] = {}

        if first_node:
            energy_json[scenario][ini_nt][json_key] = []
            first_node = False

        energy_json[scenario][ini_nt][json_key].append([energy_per_node[node_id][node_type] for node_type in energy_per_node[node_id]])

    with open(f'{data_dir}/energy.json', "w", encoding='utf-8') as outfile:
        energy_json[scenario][ini_nt] = {key: val for key, val in sorted(energy_json[scenario][ini_nt].items(), key = lambda ele: natural_keys(ele[0]))}
        outfile.write(json.dumps(energy_json, indent=2))

# @utils.synchronized('energy_lock', external=True)
def save_energy_usage_to_db(energy_per_node: Dict[int, Dict[NODE_TYPE, float]], scenario: int, ini_nt: NETWORK_STATE, nr_of_nodes: int) -> None:
    from mysql.connector import connect, Error
    from contextlib import closing

    with connect(
        host=coglobs.CONFIG['mariadb']['host'],
        port=coglobs.CONFIG['mariadb']['port'],
        user=coglobs.CONFIG['mariadb']['user'], 
        password=coglobs.CONFIG['mariadb']['passwd'],
        database=coglobs.CONFIG['mariadb']['db']) as connection:

        query = 'REPLACE INTO energy (json_key, scenario, nt, non, enon, unp, cmd_interval, sim_time, n_new, n_joining, n_child, n_parent, n_total, n_id) VALUES '
        # energy_json = {}

        query_values = []
        # first_node = True
        for node_id in energy_per_node:
            cmd_interval = coglobs.CONFIG['parent']['send_interval_s']
            sim_time = coglobs.CONFIG['general']['sim_duration_s']
            en = coglobs.CONFIG['general']['number_of_expected_nodes'] - 1
            # unp = coglobs.CONFIG['parent']['unknown_nodes_portion']
            json_key = f'{nr_of_nodes}_{en}_{cmd_interval}_{sim_time}'
            total_j = energy_per_node[node_id][NODE_TYPE.NEW] + energy_per_node[node_id][NODE_TYPE.JOINING] + energy_per_node[node_id][NODE_TYPE.CHILD] + energy_per_node[node_id][NODE_TYPE.PARENT]

            query_values.append(f'("{json_key}", {scenario}, "{ini_nt}", {nr_of_nodes}, {en}, 0, {cmd_interval}, {sim_time}, {energy_per_node[node_id][NODE_TYPE.NEW]}, {energy_per_node[node_id][NODE_TYPE.JOINING]}, {energy_per_node[node_id][NODE_TYPE.CHILD]}, {energy_per_node[node_id][NODE_TYPE.PARENT]}, {total_j}, {node_id})')

        query += ', '.join(query_values)

        print(query)

        with connection.cursor() as cursor:
            cursor.execute(query)
            connection.commit()

def save_status() -> None:
    timestamp = int(time())
    status = {'t': timestamp, 'p': 0.0}
    with open(f'{coglobs.OUTPUT_DIR}/status.json', 'w') as outfile:
        outfile.write(json.dumps(status, indent=4))

def save_new_status(status_info: Literal['ok', 'interrupted', 'error', 'finished'], started_at: int|None = None) -> None:
    def _write_and_schedule_new_save() -> None:
        with open(f'{coglobs.OUTPUT_DIR}/status_new.json', 'w') as outfile:
            outfile.write(json.dumps(status, indent=4))

        if status['lst'] < coglobs.CONFIG['general']['sim_duration_s'] * coglobs.SIU:
            add_detached_event(status['lst'], save_new_status, 'ok')

    try:
        with open(f'{coglobs.OUTPUT_DIR}/status_new.json', "r", encoding='utf-8') as f:
            status = json.load(f)
    except FileNotFoundError:
        started_at = started_at if started_at is not None else int(time())
        status = {
            't': started_at,
            'ct': started_at,
            'st': coglobs.CONFIG['general']['sim_duration_s'],
            'cst': coglobs.SIM_TIME,
            'lst': 0,
            'p': 0.0,
            'cp': 0.0,
            'eta': -1,
            'cnt': 0,
            'status': status_info
        }

        _write_and_schedule_new_save()
        return
    
    status['cst'] = coglobs.SIM_TIME
    status['ct'] = int(time())
    status['status'] = status_info

    percent = round1(100 * (int(coglobs.SIM_TIME) / float(sim_seconds * coglobs.SIU)))
    status['cp'] = percent
    seconds = status['ct'] - status['t']
    percent_diff = percent - status['p']
    if percent_diff > 0.0:
        ratio = round1(seconds / percent_diff * 0.1)
        percent_to_finish = 100.0 - percent
        status['eta'] = round(percent_to_finish * 10 * ratio, 0)
    else:
        status['eta'] = -1

    if status['lst'] == 0 and status['cnt'] < 1:
        status['lst'] = coglobs.SIM_TIME
    else:
        status['lst'] += 10**5 * coglobs.SIU

    status['cnt'] += 1
    _write_and_schedule_new_save()

if __name__ == '__main__':
    # globals.init()
    parser = argparse.ArgumentParser('LoRa scenario simulator for DAO')
    parser.add_argument('config', help='Specify config file for the simulator')
    parser.add_argument('-o', help='Output directory name', default=None)
    parser.add_argument('-f', help='Force removal of the previous results for the same configuration?', action='store_true')
    parser.add_argument('-l', help='Simple LoRaWAN simulation', action='store_true')
    parser.add_argument('-c', help='Run data-oriented simulation', action='store_true')
    parser.add_argument('-td', help='Set send_interval_s', type=int, default=-1)
    parser.add_argument('-tmd', help='Set max_send_interval_s', type=int, default=-1)
    parser.add_argument('-tni', help='Set network_info_interval_s', type=int, default=-1)
    parser.add_argument('-u', help='If run with -c or -l: update send_interval_s to the longest possible', action='store_true')
    parser.add_argument('-d', help='Sets dw and cw to the recommended values', action='store_true')
    parser.add_argument('-nbs', help='If run with -c: do not balance energy for End-Devices', action='store_true')
    parser.add_argument('-b', help='If run with -c or -l: update number_of_bytes to the specified value', type=int, default=-1)
    parser.add_argument('-dw', help='Discovery window size in seconds', type=int, default=-1)
    parser.add_argument('-cw', help='Collection window size in seconds', type=int, default=-1)
    parser.add_argument('-nn', help='Number of nodes. Does not apply to scenarios!', type=int, default=-1)
    parser.add_argument('-en', help='Number of expected nodes', type=int, default=-1)
    parser.add_argument('-siui', help='If unknown send interval sleep for min duty cycle period determined by toa of the received packet', action='store_true')
    # parser.add_argument('-unp', help='Portion of expected but unknown nodes used in Discovery command: 1 - all, 2 - hald, 3 - 1/3 third, etc.', type=int, default=1)
    parser.add_argument('-radio', help='Radio type for energy estimation: sx1262, sx1276', default='sx1262')
    parser.add_argument('-gwradio', help='Sets LoRaWAN GW radio', default='ic880a_4paths')
    parser.add_argument('-s', help='Only generate schedule for the simulation', action='store_true')
    parser.add_argument('-st', help='Simulation time in seconds', type=int, default=-1)
    parser.add_argument('-gc', help='Generates new coordinates for child nodes for given x, y, and range', type=int, nargs=3)
    parser.add_argument('-cf', help='Shows node coordinates on a figure.', action='store_true')
    parser.add_argument('-plc', help='Plots node coordinates on a figure and saves to a file', action='store_true')
    parser.add_argument('-sbs', help='Let a child node sleep instead of waiting for the assigned response slot', action='store_true')
    parser.add_argument('-gt', help='Guard Time in ms', type=float, default=-1)
    parser.add_argument('-gto', help='Sets minimal working Guard Time with relation to clock drift of a given ppm accuracy', action='store_true')
    parser.add_argument('-ne', help='Is network already established and stable?', action='store_true')
    parser.add_argument('-nt', help='Network state: UNKNOWN, WARMUP, DATA-ORIENTED', choices=NETWORK_STATE._member_names_, default=NETWORK_STATE.DATA_ORIENTED.name)
    parser.add_argument('-di', help='Nodes deployment interval in seconds', type=int, default=1200)
    parser.add_argument('-ribbtp', help='Use random interval (0 <-> max_send_interval_s) before becoming the TMP_PARENT?.', action='store_true')
    parser.add_argument('-sibbtp', help='Interval before becoming the TMP_PARENT', type=int, default=-1)
    parser.add_argument('-ndm', help='Network detection multipler', type=int, default=2)
    parser.add_argument('-pem', help='Parent election multipler', type=int, default=2)
    parser.add_argument('-dpe', help='Disable Parent Election for scenarios 4+', action='store_true')
    parser.add_argument('-fpc', help='Force Parent Node change for the election process', action='store_true')
    parser.add_argument('-cdppm', help='Clock drift in ppm', type=int, default=-1)
    parser.add_argument('-pcd', help='Perform clock drift', action='store_true')
    parser.add_argument('-cdp', help='Clock drift: Parent node always before the schedule by cdppm.', action='store_true')
    parser.add_argument('-cdc', help='Clock drift: Child nodes always before the schedule by cdppm.', action='store_true')
    parser.add_argument('-qof', help='Abort the simulation on failure (clock drift | lost packet)', action='store_true')
    parser.add_argument('-qonmc', help='Finish the simulation when neighborhood mapping is complete', action='store_true')
    parser.add_argument('-qwpe', help='Finish the simulation when parent election is complete', action='store_true')
    parser.add_argument('-sstf', help='Save states to a file', action='store_true')
    parser.add_argument('-logc', help='Log only crucial information', action='store_true')
    parser.add_argument('-ssch', help='Enables secondary scheme with JOIN_INFO_BEACON.', action='store_true')
    parser.add_argument('-jbi', help='JOIN_INFO_BEACON interval in seconds', type=int, default=-1)
    parser.add_argument('-scenario', help='For testing scenarios', type=int, default=0)
    # parser.add_argument('-unod', help='Only unknown nodes included in a DISCOVERY command', action='store_true')
    parser.add_argument('-etj', help='Save energy to json for a given scenario', action='store_true')
    parser.add_argument('-npe', help='Do not print energy usage at the end of the simulation', action='store_false')
    parser.add_argument('-npns', help='Do not print node stats at the end of the simulation', action='store_true')
    parser.add_argument('-pen', help='Print extended neighborhood info', action='store_true')
    parser.add_argument('-fcrc', help='Use fake crc16 function to speed up simulation', action='store_true')
    parser.add_argument('-pln', help='List of node ids that will experience packet loss', metavar='N', type=int, nargs='+')
    parser.add_argument('-plm', help='Packet loss modulo', type=int)
    parser.add_argument('-plp', help='Packet loss probability', type=float)
    args = parser.parse_args()

    import os
    from time import time
    import shutil
    started = time()

    # commandline = 'python3 -m loralite.simulator.simulator '
    for k in args.__dict__:
        if getattr(args, k) is None:
            continue
        if getattr(args, k) is False:
            continue
        if type(getattr(args, k)) is int and getattr(args, k) < 0:
            continue

        if getattr(args, k) is True:
            coglobs.COMMAND_LINE += f'-{k} '
        elif k == 'config':
            coglobs.COMMAND_LINE += f'{getattr(args, k)} '
        elif type(getattr(args, k)) is list:
            coglobs.COMMAND_LINE += f'-{k} {" ".join([str(x) for x in getattr(args, k)])} '
        else:
            coglobs.COMMAND_LINE += f'-{k} {getattr(args, k)} '

    # print(_ROOT)
    # if not os.path.isfile(args.config):
    #     print('Configuration file does not exist!')
    #     exit()

    load_config(f'{_ROOT}/{args.config}')
    data_dir = _DATA
    save_execution_command(f'{data_dir}/run.log')

    try:
        coglobs.SIU = coglobs.CONFIG['general']['second_in_unit']
        coglobs.IN_THE_AIR[LORA_MAIN_BAND] = InTheAir(LORA_MAIN_BAND, coglobs.SIU)
        coglobs.IN_THE_AIR[LORA_SECONDARY_BAND] = InTheAir(LORA_SECONDARY_BAND, coglobs.SIU)
        # coglobs.CHANNEL_ACTIVE[LORA_MAIN_BAND] = Channel()
        # coglobs.CHANNEL_ACTIVE[LORA_SECONDARY_BAND] = Channel()

        if args.fcrc:
            coglobs.CRC16 = lambda a: 54783
            coglobs.CRC32 = lambda a: 13254783
        else:
            coglobs.CRC16 = crc16
            coglobs.CRC32 = crc32

        if args.fpc:
            coglobs.CONFIG['general']['force_parent_node_change'] = True

        if args.gt > -1 and args.gto:
            raise RuntimeError('You can either use -gt or -gto!')       
        
        if args.gt > -1:
            coglobs.CONFIG['child']['guard_time_ms'] = args.gt

        if args.st > 0:
            coglobs.CONFIG['general']['sim_duration_s'] = args.st

        if args.cdppm > -1:
            coglobs.CONFIG['general']['cdppm'] = args.cdppm

        if args.qof:
            coglobs.CONFIG['general']['quit_on_failure'] = True

        if args.qonmc:
            coglobs.CONFIG['general']['quit_on_neighborhood_mapping_complete'] = True

        if args.qwpe:
            coglobs.CONFIG['general']['quit_when_parent_node_elected'] = True

        if args.siui:
            coglobs.CONFIG['child']['sleep_if_unknown_interval'] = True

        if args.sstf:
            coglobs.SAVE_STATE_TO_FILE = True

        if args.ssch:
            coglobs.CONFIG['parent']['secondary_schedule'] = True

        if args.jbi > -1:
            coglobs.CONFIG['parent']['join_beacon_interval_s'] = args.jbi

        if args.tni > -1:
            coglobs.CONFIG['parent']['network_info_send_interval_s'] = args.tni

        if args.plm and args.plp:
            raise RuntimeError('You can either use -plm [int] or -plp [float]<0.0 - 1.0>')

        if args.plp and not 0.0 <= args.plp <= 1.0:
            raise RuntimeError('-plp has to be between 0.0 and 1.0')

        if args.plm and args.plm < 2:
            raise RuntimeError('-plm has to be greater or equal to 2')

        # coglobs.CONFIG['parent']['unknown_nodes_portion'] = args.unp

        if args.scenario > 0 and args.scenario >= 4:
            coglobs.LORALITE_STATE = NETWORK_STATE.UNKNOWN
        else:
            coglobs.LORALITE_STATE = NETWORK_STATE[args.nt]

        sim_seconds = coglobs.CONFIG['general']['sim_duration_s']
        coglobs.SIM_DURATION_MS = sim_seconds * coglobs.SIU
        logger.set_sim_time(coglobs.SIM_DURATION_MS)
        coglobs.CONFIG['parent']['radio_type'] = args.radio
        coglobs.CONFIG['child']['radio_type'] = args.radio
        coglobs.CONFIG['lwaned']['radio_type'] = args.radio
        coglobs.CONFIG['lwangw']['radio_type'] = args.gwradio

        if args.td > 0 and args.u:
            raise RuntimeError('You can either use -td or -u!')

        if (args.cdp or args.cdc) and not args.pcd:
            raise RuntimeError('You need -pcd to use -cdp or -cdc!')

        if args.cdp and args.cdc:
            raise RuntimeError('You can either use -cdp or -cdc!')

        if args.pcd:
            coglobs.CONFIG['general']['perform_clock_drift'] = True

        if args.td > 0:
            # change payload size here
            min_delay_s = math.ceil(TOA.get_time_on_air(coglobs.CONFIG['lora']['payload_size']) / SUBBANDS[TX_PARAMS['band']][2])
            # min_delay_s = math.ceil(get_time_on_air(TX_PARAMS['max_payload']) / SUBBANDS[TX_PARAMS['band']][2])
            if args.td < min_delay_s:
                raise RuntimeError(f'Minimum allowed send_interval_s: {min_delay_s}s')
            coglobs.CONFIG['parent']['send_interval_s'] = args.td
            coglobs.CONFIG['lwaned']['send_interval_s'] = args.td

        if args.tmd > 0 and coglobs.CONFIG['parent']['send_interval_s'] > args.tmd:
            raise RuntimeError(f'max_send_interval_s: {args.tmd}s can not be smaller than send_interval_s: {coglobs.CONFIG["parent"]["send_interval_s"]}s!')

        if args.tmd > 0:
            coglobs.CONFIG['parent']['max_send_interval_s'] = args.tmd

        # if args.nn > 0 and args.scenario > 0:
        #     raise RuntimeError('You can either use -n [number_of_nodes] or -scenario [scenario_nr]!')

        if args.scenario > 0 and (args.c or args.u or args.d):
            raise RuntimeError('You can either use -scenario [scenario_nr] or a combination of -c, -d, -u!')

        if args.nn > 0:
            number_of_nodes = args.nn + 1
            coglobs.CONFIG['general']['number_of_nodes'] = args.nn + 1
            coglobs.CONFIG['general']['number_of_expected_nodes'] = args.nn + 1

        if args.en > 0 and args.scenario >= 4:
            number_of_expected_nodes = args.en
            coglobs.CONFIG['general']['number_of_expected_nodes'] = args.en
        # elif args.en > 0:
        #     number_of_expected_nodes = args.en + 1
        #     coglobs.CONFIG['general']['number_of_expected_nodes'] = args.en + 1
        # else:
        #     coglobs.CONFIG['general']['number_of_expected_nodes'] = coglobs.CONFIG['general']['number_of_nodes'] + 1

        if args.scenario == 0 and coglobs.CONFIG['general']['number_of_nodes'] > coglobs.CONFIG['general']['number_of_expected_nodes']:
            raise RuntimeError('Number of actually deployed nodes (number_of_nodes) can not be larger than the number of expected nodes in the network!')

        distance_warning = None
        if args.scenario <= 0:
            number_of_nodes = coglobs.CONFIG['general']['number_of_nodes']
            coordinates = []
            xc, yc, lrange = [0, 0, 0]
            max_lrange = PROPAGATION_MODEL.calculate_max_distance(SUBBANDS[LORA_BAND_48][3], RX_SENSITIVITY[SF_12])
            if args.gc:
                xc, yc, lrange = args.gc
                if lrange > max_lrange:
                    distance_warning = f'Specified in -gc range: {lrange}m is higher than the maximum possible: {max_lrange}m for the selected propagation settings!'
                coordinates = generate_coordinates(xc, yc, lrange, number_of_nodes - 1)
                config_coordinates = []
                config_coordinates.append([xc, yc, 0])
                for x, y in coordinates:
                    config_coordinates.append([x, y, 0])
                coglobs.CONFIG['locations'] = config_coordinates
        else:
            coordinates = coglobs.CONFIG['locations']

        if args.dw > 0:
            coglobs.CONFIG['parent']['disc_window_s'] = args.dw

        if args.cw > 0:
            coglobs.CONFIG['parent']['collect_window_s'] = args.cw

        if args.b > -1:
            bytes_to_send = args.b
            coglobs.CONFIG['lora']['bytes_to_send'] = bytes_to_send

        if args.di:
            coglobs.CONFIG['scenarios']['scenario_ge_4']['deployment_interval_s'] = args.di

        if args.ndm <= 0:
            raise RuntimeError('Network detection multipler has to be greater than 0!')

        if args.ndm > 0:
            coglobs.CONFIG['scenarios']['scenario_ge_4']['network_detection_multipler'] = args.ndm

        if args.pem <= 0:
            raise RuntimeError('Parent election multipler has to be greater than 0!')

        if args.pem > 0:
            coglobs.CONFIG['scenarios']['scenario_ge_4']['parent_election_multipler'] = args.pem

        if args.sibbtp >= 0 and args.ribbtp:
            raise RuntimeError('You can either use -ribbtp or -sibbtp [seconds]!')

        if args.sibbtp >= 0:
            coglobs.CONFIG['parent']['t_before_becoming_tmp_parent'] = args.sibbtp
            coglobs.CONFIG['parent']['random_t_before_becoming_tmp_parent'] = False

        if args.ribbtp:
            coglobs.CONFIG['parent']['random_t_before_becoming_tmp_parent'] = True
            coglobs.CONFIG['parent']['t_before_becoming_tmp_parent'] = -1

        if args.dpe:
            coglobs.CONFIG['scenarios']['scenario_ge_4']['parent_election_disabled'] = True

        if CRC_ENABLED:
            coglobs.CONFIG['lora']['crc_bytes'] = CRC_SIZE
        else:
            coglobs.CONFIG['lora']['crc_bytes'] = 0

        scheduler = Scheduler(TX_PARAMS, RX_SENSITIVITY[TX_PARAMS['sf']], SUBBANDS)
        if args.scenario <= 0 and args.d:
            dw, cw = scheduler.get_recommended_dw_cw(number_of_nodes)
            coglobs.CONFIG['parent']['disc_window_s'] = dw
            coglobs.CONFIG['parent']['collect_window_s'] = cw

        if args.c and args.u:
            try:
                delay_s = scheduler.get_longest_possible_interval(sim_seconds, number_of_nodes, coglobs.CONFIG['lora']['bytes_to_send'])
            except RuntimeError:
                cw, error = scheduler.find_smallest_cw(sim_seconds, number_of_nodes, bytes_to_send)
                if error is not None:
                    raise error
            coglobs.CONFIG['parent']['send_interval_s'] = delay_s

        if args.gto:
            gt = (math.ceil(coglobs.CONFIG['parent']['send_interval_s'] * coglobs.SIU * (coglobs.CONFIG['general']['cdppm'] / coglobs.SIU ** 2)) * 4)
            if not gt % 2 == 0:
                gt += 1
            # gt = (math.ceil(coglobs.CONFIG['parent']['send_interval_s'] * coglobs.SIU * (coglobs.CONFIG['general']['cdppm'] / coglobs.SIU ** 2)) * 4) + 2
            # print(f'Minimal Guard Time of {gt} ms for the given clock drift of {coglobs.CONFIG["general"]["cdppm"]} ppm was set.')
            coglobs.CONFIG['child']['guard_time_ms'] = gt

        if args.l and args.u:
            delay_s = scheduler.get_longest_possible_interval_for_lwan(sim_seconds, coglobs.CONFIG['lora']['bytes_to_send'])
            coglobs.CONFIG['lwaned']['send_interval_s'] = delay_s

        # coglobs.OUTPUT_DIR = ''
        if args.o is not None:
            if args.scenario > 0:
                coglobs.OUTPUT_DIR = f'{data_dir}/{args.o}'
            else:
                coglobs.OUTPUT_DIR = f'{data_dir}/{args.o}_{number_of_nodes - 1}_{coglobs.CONFIG["parent"]["disc_window_s"]}_{coglobs.CONFIG["parent"]["collect_window_s"]}'
            if args.l:
                coglobs.OUTPUT_DIR = f'{data_dir}/{args.o}_{number_of_nodes - 1}'
        else:
            now = datetime.today().strftime('%Y%m%d_%H%M%S')
            coglobs.OUTPUT_DIR = f'{data_dir}/experiments/{now}_{randint(0, 999999)}'

        if os.path.isdir(coglobs.OUTPUT_DIR) and args.f:
            shutil.rmtree(coglobs.OUTPUT_DIR)
        elif os.path.isdir(coglobs.OUTPUT_DIR):
            print(f'{coglobs.OUTPUT_DIR} exists! Please use: --f True or remove the directory manually')
            exit()

        os.makedirs(coglobs.OUTPUT_DIR)
        if args.sstf:
            os.makedirs(f'{coglobs.OUTPUT_DIR}/state')
        logger.set_file(f'{coglobs.OUTPUT_DIR}/log.txt')
        if args.logc:
            logger.set_log_level(CRUCIAL)
        coglobs.CONFIG['general']['data_dir_path'] = coglobs.OUTPUT_DIR

        save_status()

        if len(coordinates) == 0:
            xc, yc, _ = coglobs.CONFIG['locations'][0]
            max_dist, max_dist_co = [0.0, None]
            for x, y, z in coglobs.CONFIG['locations'][1:number_of_nodes]:
                dist = calculate_distance_simple((xc, yc, 0), (x, y, z))
                if dist > max_dist:
                    max_dist = dist
                    max_dist_co = [x, y, z]
                coordinates.append([x, y])
            # lrange = PROPAGATION_MODEL.calculate_max_distance(SUBBANDS[LORA_BAND_868_0][3], RX_SENSITIVITY[SF_12])
            lrange = int(max_dist)
        
        if args.scenario <= 0 and len(coordinates) > 0 and len(coordinates) < number_of_nodes:
            is_lrange_set = "lrange" in locals()
            lrange = lrange if is_lrange_set else int(max_lrange)
            xc, yc, _ = coglobs.CONFIG['locations'][0]
            coordinates = generate_coordinates(xc, yc, lrange, number_of_nodes - 1, coordinates)
            config_coordinates = []
            config_coordinates.append([xc, yc, 0])
            for x, y in coordinates:
                config_coordinates.append([x, y, 0])
            coglobs.CONFIG['locations'] = config_coordinates

        if args.sbs:
            coglobs.CONFIG['child']['sleep_before_slot'] = args.sbs

        # if args.unod:
        #     coglobs.CONFIG['parent']['unknown_nodes_only'] = True

        save_config(f'{coglobs.OUTPUT_DIR}/config.json')
        save_execution_command(f'{coglobs.OUTPUT_DIR}/command.txt', False)

        if args.plc and len(coordinates) > 0:
            plot_coordinates(xc, yc, int(max_lrange), coordinates, coglobs.OUTPUT_DIR, lrange, args.cf)

        m_lou: DeviceType | None = None
        lou: DeviceType | None = None
        if not args.l:
            if args.scenario > 0:
                coglobs.SCENARIO = args.scenario
                match args.scenario:
                    # New node joins the established network
                    # Join Beacon on a secondary frequency (independent)
                    case 1:
                        coglobs.LIST_OF_NODES[0] = Node(0, coglobs.CONFIG['locations'][0], NODE_TYPE.PARENT)
                        coglobs.LIST_OF_NODES[1] = Node(1, coglobs.CONFIG['locations'][1], NODE_TYPE.CHILD)
                        calculate_distance_matrix(coglobs.LIST_OF_NODES)
                        new_node = Node(2, coglobs.CONFIG['locations'][2], NODE_TYPE.NEW)
                        new_node.lora_band = LoraBand(LORA_SECONDARY_BAND, SF_12)
                        coglobs.LIST_OF_NODES[2] = new_node
                    # New node joing the established network
                    # The node uses time between commands to determine the schedule or if it is lucky
                    # it gets information about the schedule from BEACON command
                    case 2:
                        coglobs.LIST_OF_NODES[0] = Node(0, coglobs.CONFIG['locations'][0], NODE_TYPE.PARENT)
                        coglobs.LIST_OF_NODES[1] = Node(1, coglobs.CONFIG['locations'][1], NODE_TYPE.CHILD)
                        calculate_distance_matrix(coglobs.LIST_OF_NODES)
                        new_node_ts = coglobs.CONFIG['parent']['send_interval_s'] * coglobs.SIU * 5
                        add_new_node_event(new_node_ts, Node, 2, coglobs.CONFIG['locations'][2], NODE_TYPE.NEW, new_node_ts)
                    # Verify packet collisions
                    case 3:
                        max_dist = PROPAGATION_MODEL.calculate_max_distance(SUBBANDS[LORA_BAND_48][3], RX_SENSITIVITY[SF_12])
                        # packet: Packet = {'seq': 0, 'cmd': CMD_NETWORK_INFO, 'nr_of_ret': 0, 'data': '600'}
                        add_new_node_event(1000, Node, 1, coglobs.CONFIG['locations'][1], NODE_TYPE.NEW, 1000, '_starting_schedule_scenario_3a')
                        add_new_node_event(2000, Node, 2, coglobs.CONFIG['locations'][2], NODE_TYPE.NEW, 1600, '_starting_schedule_scenario_3a')
                        add_new_node_event(900, Node, 5, coglobs.CONFIG['locations'][5], NODE_TYPE.NEW, 900, '_starting_schedule_scenario_3b')
                        add_new_node_event(900, Node, 7, coglobs.CONFIG['locations'][7], NODE_TYPE.NEW, 900, '_starting_schedule_scenario_3b')
                        if args.plc:
                            add_detached_event(2500, plot_coordinates_for_scenarios, max_dist, coglobs.OUTPUT_DIR, 2500)
                    # Parent node election (multiple variants)
                    # case 4 | 5 | 6 | 7 | 8:
                    case _ if args.scenario > 4:
                        deployment_interval = coglobs.CONFIG['scenarios']['scenario_ge_4']['deployment_interval_s'] * coglobs.SIU
                        deployment_ts = coglobs.SIU
                        node_id = coglobs.CONFIG['scenarios']['scenario_ge_4']['node_list'][str(coglobs.CONFIG['general']['number_of_expected_nodes'])]
                        potential_nr_of_parents = 1
                        for id in node_id:
                            add_new_node_event(deployment_ts, Node, id, coglobs.CONFIG['locations'][id], NODE_TYPE.NEW, deployment_ts, '_starting_schedule_scenario_ge_4')
                            # if id in [0, 1]:
                            #     add_detached_event(deployment_ts, set_specific_clock_drift_direction, id, False)
                            # else:
                            #     add_detached_event(deployment_ts, set_specific_clock_drift_direction, id)
                            if args.pln and args.plm and id in args.pln:
                                add_detached_event(deployment_ts, set_packet_loss_modulo, id, args.plm)
                            elif args.plp is not None and args.pln and id in args.pln:
                                add_detached_event(deployment_ts, set_packet_loss_probability, id, args.plp)
                            elif args.plp is not None and args.pln is None:
                                add_detached_event(deployment_ts, set_packet_loss_probability, id, args.plp)
                            deployment_ts += deployment_interval    
                        
                            if args.scenario == 20 and id == 2:
                                add_detached_event(deployment_ts, set_nr_of_packets_to_lose_in_a_row, id, 5, 30, True)   
                            if args.scenario == 21 and id != 3:
                                add_detached_event(deployment_ts, set_nr_of_packets_to_lose_in_a_row, id, 3, 16, True)
                            if args.scenario == 22:
                                if id != 3:
                                    add_detached_event(deployment_ts, set_nr_of_packets_to_lose_in_a_row, id, 3, 16, True)

                                if id != 0:
                                    add_detached_event(10900000, set_nr_of_packets_to_lose_in_a_row, id, 3, 6, True)

                        if args.plc:
                            max_dist = PROPAGATION_MODEL.calculate_max_distance(SUBBANDS[LORA_BAND_48][3], RX_SENSITIVITY[SF_12])
                            add_detached_event(deployment_ts + 10, plot_coordinates_for_scenarios, max_dist, coglobs.OUTPUT_DIR, deployment_ts)
                        coglobs.NR_OF_NODES_TO_DISCOVER = len(node_id) - potential_nr_of_parents

                set_clock_drift_direction(args.pcd, args.cdp, args.cdc)
            else:
                m_lou = Node(0, coglobs.CONFIG['locations'][0], NODE_TYPE.PARENT)
                coglobs.LIST_OF_NODES[0] = m_lou
                for i in range(1, number_of_nodes):
                    lou = Node(i, coglobs.CONFIG['locations'][i], NODE_TYPE.CHILD)
                    coglobs.LIST_OF_NODES[i] = lou

                set_clock_drift_direction(args.pcd, args.cdp, args.cdc)
                calculate_distance_matrix(coglobs.LIST_OF_NODES)
                
                if args.c:
                    balance_energy = True
                    if args.nbs:
                        balance_energy = False
                    m_lou.packet_schedule = scheduler.generate_schedule_for_parent_data(sim_seconds, number_of_nodes, coglobs.CONFIG['lora']['bytes_to_send'], balance_energy)

            if args.sstf:
                for id in coglobs.LIST_OF_NODES:
                    coglobs.STATE_FILE_COUNT[id] = 0
        else:
            m_lou = LoRaWANGateway(0, coglobs.CONFIG['locations'][0])
            
            coglobs.LIST_OF_NODES[0] = m_lou
            coglobs.LORAWAN_GW = m_lou
            for i in range(1, number_of_nodes):
                lou = LoRaWANEndDevice(i, coglobs.CONFIG['locations'][i])
                delay, lou.packet_schedule = scheduler.generate_schedule_for_lwan_new(lou, sim_seconds, coglobs.CONFIG['lora']['bytes_to_send'])
                lou.config['send_interval'] = delay * coglobs.SIU
                coglobs.LIST_OF_NODES[i] = lou

            calculate_distance_matrix(coglobs.LIST_OF_NODES)
    except Exception as e:
        log_exception(data_dir, e, traceback.format_exc())
        raise e

    if distance_warning is not None:
        logger.warning(coglobs.SIM_TIME, f'{bcolors.WARNING}{distance_warning}{bcolors.ENDC}\n')
        logger._flush()

    if args.s:
        from sys import exit
        exit(0)

    try:
        logger.crucial(coglobs.SIM_TIME, 'Simulation started!')
        add_detached_event(coglobs.CONFIG['child']['first_op_at_s'] * coglobs.SIU + 10**2, save_new_status, 'ok', int(started))
        while coglobs.SIM_TIME < coglobs.SIM_DURATION_MS:
            try:
                events = coglobs.EVENT_LIST.popitem(0)[1]
                for event in events:
                    event.execute()
            except KeyError as e:
                if e.args[0] == 'popitem(): dictionary is empty':
                    # end of simulation
                    log_exception(data_dir, e, traceback.format_exc())
                    coglobs.SIM_TIME = coglobs.SIM_DURATION_MS
                else:
                    raise e
            except ClockDriftException as e:
                if coglobs.CONFIG['general']['quit_on_failure'] and args.cdp:
                    log_drift_failure(1)
                    raise KeyboardInterrupt
                if coglobs.CONFIG['general']['quit_on_failure'] and args.cdc:
                    log_drift_failure(2)
                    raise KeyboardInterrupt
            except ClockDriftIssue as e:
                log_drift_issue(e.node_id, e.timestamp)
            except SimException as e:
                raise SimException(e)
            # except Exception as e:
            #     log_exception(data_dir, e, traceback.format_exc())



    except KeyboardInterrupt:
        logger._flush()
        logger.warning(coglobs.SIM_TIME, f'{bcolors.WARNING}Simulation interrupted!{bcolors.ENDC}\n')
        save_new_status('interrupted')
        logger._flush()
        exit(0)
    except Exception as e:
        logger._flush()
        log_exception(data_dir, e, traceback.format_exc())
        logger.error(coglobs.SIM_TIME, f'{bcolors.BRED}Simulation failed!{bcolors.ENDC}\n')
        save_new_status('error')
        logger._flush()
        raise e

    if args.scenario >= 4 and args.qonmc:
        sim_seconds = math.ceil(coglobs.SIM_TIME / coglobs.SIU)

    def _print_node_stats() -> None:
        info_length = 28
        known_nodes = SortedDict()
        if not args.l:
            nodes_packets_sent = sum([x.node_runtime_params["packets_sent"] for x in coglobs.LIST_OF_NODES.values() if x.type is not NODE_TYPE.PARENT])
        else:
            nodes_packets_sent = sum([x.packets_sent for x in coglobs.LIST_OF_NODES.values() if x.type is not LWAN_DEV_TYPE.GW])
        for node in coglobs.LIST_OF_NODES.values():
            logger.crucial(coglobs.SIM_TIME, f'{bcolors.UNDERLINE}Stats for node_{node.id} [{node.type.name}]{bcolors.ENDC}')
            if type(node) is Node and node.new_node_runtime_params['deployed_at'] > -1:
                new_node_for = node.new_node_runtime_params['new_node_until'] - node.new_node_runtime_params['deployed_at']
                joining_node_for = node.new_node_runtime_params['joining_node_until'] - node.new_node_runtime_params['joining_node_from']
                tmp_parent_for = node.new_node_runtime_params['tmp_parent_node_until'] - node.new_node_runtime_params['tmp_parent_from']

                new_node_for = new_node_for if new_node_for > 0 else 0
                joining_node_for = joining_node_for if joining_node_for > 0 else 0
                tmp_parent_for = tmp_parent_for if tmp_parent_for > 0 else 0
                if tmp_parent_for == 0 and node.new_node_runtime_params['tmp_parent_from'] > 0:
                    tmp_parent_for = coglobs.SIM_DURATION_MS - node.new_node_runtime_params['tmp_parent_from']

                logger.crucial(coglobs.SIM_TIME, f'\t{"[NEW for (ms)]":{info_length}s}: {format_ms(new_node_for, coglobs.SIU)}')
                logger.crucial(coglobs.SIM_TIME, f'\t{"[JOINING for (ms)]":{info_length}s}: {format_ms(joining_node_for, coglobs.SIU)}')
                logger.crucial(coglobs.SIM_TIME, f'\t{"[TMP_PARENT for (ms)]":{info_length}s}: {format_ms(tmp_parent_for, coglobs.SIU)}')
                logger.crucial(coglobs.SIM_TIME, f'\t{"[AVG discovery time(ms)]":{info_length}s}: {format_ms(node.node_runtime_params["avg_time_between_neighbor_node_discovery"], coglobs.SIU)}')
                logger.crucial(coglobs.SIM_TIME, f'\t{"[Discovery after(ms)]":{info_length}s}: {[format_ms(ts, coglobs.SIU) for ts in node.node_runtime_params["neighbor_node_discovered_after"]]}')
                # if args.scenario in [6, 7, 8]:
            if type(node) is Node and not args.l:
                known_nodes[node.id] = [x for x in node.known_nodes]
                logger.crucial(coglobs.SIM_TIME, f'\t{"[PARENT NODE_ID]":{info_length}s}: {node.node_runtime_params["parent_node"]}')
                logger.crucial(coglobs.SIM_TIME, f'\t{"[Known nodes short]":{info_length}s}: {known_nodes[node.id]}')
                if args.pen: logger.crucial(coglobs.SIM_TIME, f'\t{"[Known nodes]":{info_length}s}: [{node.known_nodes}]')
            if not args.l:
                logger.crucial(coglobs.SIM_TIME, f'\t{"[Packets sent]":{info_length}s}: {node.node_runtime_params["packets_sent"]}')
            else:
                logger.crucial(coglobs.SIM_TIME, f'\t{"[Packets sent]":{info_length}s}: {node.packets_sent}')
            if node.type == NODE_TYPE.PARENT:
                logger.crucial(coglobs.SIM_TIME, f'\t{"[JBI sent]":{info_length}s}: {node.parent_runtime_params["join_beacons_sent"]}')
            if not args.l:
                logger.crucial(coglobs.SIM_TIME, f'\t{"[Bytes sent]":{info_length}s}: {node.node_runtime_params["bytes_sent"]:,}')
            else:
                logger.crucial(coglobs.SIM_TIME, f'\t{"[Bytes sent]":{info_length}s}: {node.bytes_sent:,}')
            if node.type == NODE_TYPE.CHILD:
                logger.crucial(coglobs.SIM_TIME, f'\t{"[DCR Bytes sent]":{info_length}s}: {node.dc_bytes_sent:,}')
            if not args.l:
                logger.crucial(coglobs.SIM_TIME, f'\t{"[Packets received]":{info_length}s}: {node.node_runtime_params["packets_received"]}')
                logger.crucial(coglobs.SIM_TIME, f'\t{"[PRR][Packets received]":{info_length}s}: {node.simulation_params["received_count"]}')
                logger.crucial(coglobs.SIM_TIME, f'\t{"[PRR][Should receive]":{info_length}s}: {node.simulation_params["should_receive_count"]}')
                logger.crucial(coglobs.SIM_TIME, f'\t{"[PRR][Expected to receive]":{info_length}s}: {node.simulation_params["expected_to_receive_count"]}')
                logger.crucial(coglobs.SIM_TIME, f'\t{"[PRR]":{info_length}s}: {calculate_prr(node.simulation_params["received_count"], node.simulation_params["should_receive_count"])}%')
                logger.crucial(coglobs.SIM_TIME, f'\t{"[PLC]":{info_length}s}: {node.simulation_params["lost_due_to_pls"]}')
            else:
                logger.crucial(coglobs.SIM_TIME, f'\t{"[Packets received]":{info_length}s}: {node.packets_received}')
            if node.type is NODE_TYPE.PARENT:
                logger.crucial(coglobs.SIM_TIME, f'\t{"[Should receive]":{info_length}s}: {node.parent_runtime_params["total_expected_recv_count"]}')
                logger.crucial(coglobs.SIM_TIME, f'\t{"[Child nodes sent]":{info_length}s}: {nodes_packets_sent}')
            elif node.type is LWAN_DEV_TYPE.GW:
                logger.crucial(coglobs.SIM_TIME, f'\t{"[Should receive]":{info_length}s}: {nodes_packets_sent}')
            if node.type == NODE_TYPE.CHILD:
                logger.crucial(coglobs.SIM_TIME, f'\t{"[D received]":{info_length}s}: {node.d:,}')
                logger.crucial(coglobs.SIM_TIME, f'\t{"[DC received]":{info_length}s}: {node.dc:,}\n')
            elif args.l:
                logger.crucial(coglobs.SIM_TIME, f'\t{"[Bytes received]":{info_length}s}: {node.bytes_received:,}\n')
            else:
                logger.crucial(coglobs.SIM_TIME, f'\t{"[Bytes received]":{info_length}s}: {node.node_runtime_params["bytes_received"]:,}\n')

        if args.scenario >= 4:
            with open(f'{coglobs.OUTPUT_DIR}/neighborhood.json', "w", encoding='utf-8') as outfile:
                outfile.write('{\n')
                last = known_nodes.peekitem()
                for node_id in known_nodes:
                    if node_id != last[0]:
                        outfile.write(f'\t"{node_id}": [{", ".join([str(x) for x in known_nodes[node_id]])}],\n')
                    else:
                        outfile.write(f'\t"{node_id}": [{", ".join([str(x) for x in known_nodes[node_id]])}]\n')
                outfile.write('}\n')
    
    sim_msg = f'{bcolors.BGREEN}Simulation finished!{bcolors.ENDC}\n'
    time_color = bcolors.BGREEN
    # TODO: fix me!
    # if args.scenario > 0 and args.scenario not in [3] and type(coglobs.LIST_OF_NODES[0]) == LoRaLitEParentNode and coglobs.LIST_OF_NODES[0].packets_received < coglobs.LIST_OF_NODES[0].parent_runtime_params['total_expected_recv_count']:
    #     sim_msg = f'{bcolors.BRED}Simulation failed!{bcolors.ENDC}\n'
    #     time_color = bcolors.BRED

    logger.crucial(coglobs.SIM_TIME, sim_msg)

    if not args.npns:
        _print_node_stats()

    if args.scenario >= 4:
        if coglobs.ALL_NODES_DISCOVERED_IN < 0:
            logger.crucial(coglobs.SIM_TIME, f'[NEIGHBORHOOD MAPPED IN]: Not mapped!')
        else:
            logger.crucial(coglobs.SIM_TIME, f'[NEIGHBORHOOD MAPPED IN]: {format_ms(coglobs.ALL_NODES_DISCOVERED_IN, coglobs.SIU)}')
        logger.crucial(coglobs.SIM_TIME, f'[PE AT]: {[format_ms(ts, coglobs.SIU) for ts in coglobs.PE_ELECTION_AT]}')
        logger.crucial(coglobs.SIM_TIME, f'[PE FINISHED AT]: {[format_ms(ts, coglobs.SIU) for ts in coglobs.PE_FINISHED_AT]}')

    logger.crucial(coglobs.SIM_TIME, f'[NR OF COLLISIONS]: {coglobs.NUMBER_OF_COLLISIONS}')
    if not args.l:
        logger.crucial(coglobs.SIM_TIME, f'[BIGGEST DISC RESPONSE]: {coglobs.BIGGEST_DISC_RESPONSE}')
        logger.crucial(coglobs.SIM_TIME, f'[BIGGEST DISC REQUEST]: {coglobs.BIGGEST_DISC_REQUEST}')
        logger.crucial(coglobs.SIM_TIME, f'[BIGGEST COLL REQUEST]: {coglobs.BIGGEST_COLL_REQUEST}\n')

    if not args.l:
        energy_per_node: Dict[int, Dict[NODE_TYPE, float]] = {}
        duration_per_node: Dict[int, Dict[str, int]] = {}
        for node in coglobs.LIST_OF_NODES.values():
            if type(node) is Node:
                node._save_state(True)
            energy_per_node[node.id], duration_per_node[node.id] = node.energy.calculate_energy_usage(node.initial_state, node.state_table, node.id, sim_seconds, args.npe)
    else:
        for dev in coglobs.LIST_OF_NODES.values():
            dev.energy.calculate_energy_usage(dev.initial_state, dev.state_table, dev.id, sim_seconds)


    if args.etj and not args.l:
        try:
            # save_energy_usage_to_db(energy_per_node, args.scenario, args.nt, len(energy_per_node))
            save_energy_usage(energy_per_node, str(args.scenario), args.nt, len(energy_per_node))
            if args.scenario >= 4:
                save_scenario_info(energy_per_node, duration_per_node, str(args.scenario), len(energy_per_node))
        except Exception as e:
            log_exception(data_dir, e, traceback.format_exc())

    ended = time()
    save_new_status('finished')
    logger.crucial(coglobs.SIM_TIME, f'{bcolors.BGREEN}Execution time: {math.ceil(ended - started)}s.{bcolors.ENDC}\n')
