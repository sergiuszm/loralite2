import time
import subprocess
import select
import os
import argparse
import shlex
import json
import math
from pathlib import Path
from loralite.simulator.utils import natural_keys


def read_status(path, filename, sim_time, new_format=True):
    sim_time = int(sim_time) * 1000
    formated_sim_time = f'{int((sim_time - sim_time % 1000) / 1000):,}.{sim_time % 1000:03d}s'

    args = shlex.split(f"grep '{formated_sim_time}' {path}/{filename}")

    lines = None
    with subprocess.Popen(args, stdout=subprocess.PIPE) as proc:
        lines = proc.stdout.read()
    
    to_clean = ['\t', '\x1b[95m', '\x1b[4m', '\x1b[0m', '\x1b[1m', '\x1b[32m', '\x1b[42m', '\x1b[92m', '\x1b[94m', '\x1b[96m', formated_sim_time]
    lines = lines.decode('utf-8')
    for p in to_clean:
        lines = lines.replace(p, '')

    lines = lines.split('\n')
    lines = lines[1:]

    stats_path = f'{path}/stats.txt'
    first_line = True
    with open(stats_path, 'w') as f:
        for line in lines:
            if line.find('Stats for dev_') >= 0 or line.find('Energy usage for dev_') >= 0 or line.find('Execution time') >= 0:
                f.write(f'{"" if first_line else chr(10)}{line}\n')
                first_line = False
                continue
            f.write(f'\t{line}\n')

    energy = {}
    stats = {}
    dev_nr = -1
    energy_brackets = False
    stats_brackets = False
    stats_count = 0
    s_path = f'{path}/summary.txt'
    if new_format: s_path = f'{path}/summary_new.txt'
    with open(s_path, 'w') as f:
        for line in lines:
            if line.find('Stats for dev_') >= 0:
                line = line.replace('Stats for dev_', '').replace(' [END_DEV]', '').replace(' [GW]', '').replace(' [PARENT]', '').replace(' [CHILD]', '')
                dev_nr = int(line)
                stats_brackets = True
                tmp_stats = []
                continue

            if stats_brackets and line.find('[Packets sent]') >= 0:
                line = line.replace('[Packets sent]', '').replace('\t', '').replace(' ', '').replace(':', '')
                tmp_stats.append(int(line))
                continue

            if stats_brackets and line.find('[Bytes sent]') >= 0:
                line = line.replace('[Bytes sent]', '').replace('\t', '').replace(' ', '').replace(':', '').replace(',', '')
                tmp_stats.append(int(line))
                continue

            if stats_brackets and line.find('[Packets received]') >= 0:
                line = line.replace('[Packets received]', '').replace('\t', '').replace(' ', '').replace(':', '')
                tmp_stats.append(int(line))
                continue

            if stats_brackets and line.find('[Bytes received]') >= 0:
                line = line.replace('[Bytes received]', '').replace('\t', '').replace(' ', '').replace(':', '').replace(',', '')
                tmp_stats.append(int(line))
                stats_brackets = False
                stats[dev_nr] = tmp_stats
                tmp_stats = []
                continue

            if stats_brackets and line.find('[DCR Bytes sent]') >= 0:
                line = line.replace('[DCR Bytes sent]', '').replace('\t', '').replace(' ', '').replace(':', '').replace(',', '')
                tmp_stats.append(int(line))
                continue

            if stats_brackets and line.find('[D received]') >= 0:
                line = line.replace('[D received]', '').replace('\t', '').replace(' ', '').replace(':', '').replace(',', '')
                tmp_stats.append(int(line))
                continue

            if stats_brackets and line.find('[DC received]') >= 0:
                line = line.replace('[DC received]', '').replace('\t', '').replace(' ', '').replace(':', '').replace(',', '')
                tmp_stats.append(int(line))
                stats_brackets = False
                stats[dev_nr] = tmp_stats
                tmp_stats = []
                continue

            if line.find('Energy usage for dev_') >= 0:
                line = line.replace('Energy usage for dev_', '')
                # line = line.replace(' [GW]')
                # line = line.replace('')
                dev_nr = int(line)
                energy_brackets = True

                # print(dev_nr)

            if energy_brackets and line.find('TOTAL ENERGY USED: ') >= 0:
                line = line.replace('TOTAL ENERGY USED: ', '')
                e = line.split(' => ')
                j = round(float(e[0].replace('J', '')), 2)
                wh = round(float(e[1].replace('Wh', '')), 2)
                tmp_mah = e[2].split(' @ ')
                mah = round(float(tmp_mah[0].replace('mAh', '')), 2)
                energy[dev_nr] = [j, wh, mah]
                ts = ','.join(str(x) for x in stats[dev_nr])
                f.write(f'{dev_nr},{j},{wh},{mah},{ts}\n')

    return energy, stats

def extract_data(dir, new_format=True, force_rebuild=False):
    energy = {}
    stats = {}
    info = {}

    def _exctract(st):
        path = f'{dir}/{p}/summary.txt'
        if new_format: path = f'{dir}/{p}/summary_new.txt'
        if os.path.isfile(path) and not force_rebuild:
            energy[p] = {}
            stats[p] = {}
            with open(path) as f:
                lines = f.readlines()
                for line in lines:
                    data = line.replace('\n', '').split(',')
                    data = [float(x) for x in data]
                    energy[p][int(data[0])] = data[1:4]
                    stats[p][int(data[0])] = data[4:]
        else:
            energy[p], stats[p] = read_status(f'{dir}/{p}', 'log.txt', st, new_format)

    for p in os.listdir(dir):
        lwan = False
        # tmp = p.split('_')
        # if nr_of_dev > 0 and int(tmp[0]) == nr_of_dev:
        #     _exctract()
        # else:
        with open(f'{dir}/{p}/config.json', 'r') as f:
            config = json.load(f)
        _exctract(config['general']['sim_duration_s'])
        if new_format:
            delay = config['wcm']['send_interval_s']
            dw = config['wcm']['disc_window_s']
            dcw = config['wcm']['dc_window_s']
            bytes_to_send = config['lora']['bytes_to_send']
            if p.find('lorawan') >= 0:
                with open(f'{dir}/{p}/schedule_ed_1.txt', 'r') as f:
                    line = f.readline()
                delay = math.floor(float(line.split(':')[1].split('|')[0].replace(' ', '')))
                lwan = True
                # delay = config['lwaned']['send_interval_s']
                dw = dcw = 0
            info[p] = {'lwan': lwan, 'delay': delay, 'dw': dw, 'dcw': dcw, 'bytes': bytes_to_send}

    if new_format:
        return energy, stats, info
    return energy, stats


def get_keys(dir, prefix, max_nr_of_devs=0, devs_step=5, starting_dev=1, seq=[]):
    keys, devs = [], []
    for path in Path(dir).rglob('config.json'):
        if path._str.find(prefix) >= 0:
            keys.append(''.join(x for x in path.parts if x.startswith(prefix)))

    # dirs = [x for x in dirs if x.startswith(prefix)]
    if len(seq) > 0:
        prefixes = []
        for x in seq:
            prefixes.append(f'{prefix}_{x}_')
            devs.append(str(x))

    elif max_nr_of_devs > 0:
        prefixes = []
        if starting_dev == 1:
            prefixes.append(f'{prefix}_1_')
            devs.append('1')
        
        for nr_devs in range(starting_dev if starting_dev > 1 else 5, max_nr_of_devs + devs_step, devs_step):
            prefixes.append(f'{prefix}_{nr_devs}_')
            devs.append(str(nr_devs))

    if len(prefixes) > 0:
        keys = [x for x in keys if x.startswith(tuple(prefixes))]
    
    # keys = []
    # for file_name in dirs:
    #     file_name_parts = file_name.split('/')
    #     for part in file_name_parts:
    #         if part.find(prefix) >= 0:
    #             keys.append(part)

    keys.sort(key=natural_keys)
    devs.sort(key=natural_keys)
    if len(devs) == 0:
        devs.append(0)

    return keys, devs


# get_keys('data/latest_sbs/sx1262_dcw2', 'loralite_128_20', max_nr_of_devs=0, devs_step=10, starting_dev=10)