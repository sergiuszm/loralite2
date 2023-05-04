import os
import sys
import json
import loralite.simulator.globals as coglobs
from typing import TypeAlias, TypedDict, Dict, List, Literal, Final

SupportedPlatform = Literal['arthemis_nano']
SupportedRadio = Literal['sx1276', 'sx1262', 'ic880a_4paths', 'ic880a_10paths']


class GeneralConfig(TypedDict):
    number_of_nodes: int
    number_of_expected_nodes: int
    max_packet_nr: int
    sim_duration_s: int
    time_unit: str
    second_in_unit: int
    save_schedule_to_file: bool
    data_dir_path: str
    cdppm: int
    perform_clock_drift: bool
    quit_on_failure: bool
    quit_when_parent_node_elected: bool
    quit_on_neighborhood_mapping_complete: bool
    force_parent_node_change: bool

class NodeConfig(TypedDict):
    sch_on_duration_ms: int
    sch_off_duration_ms: int
    backoff_s: int

class RadioConfig(TypedDict):
    receive_call_interval_ms: int
    mode_change_ms: int

class LoRaConfig(TypedDict):
    bytes_to_send: int
    payload_size: int
    crc_bytes: int

class ParentConfig(TypedDict):
    platform: SupportedPlatform
    radio_type: SupportedRadio
    first_op_at_s: int
    send_interval_s: int
    network_info_send_interval_s: int
    max_send_interval_s: int
    disc_window_s: int
    collect_window_s: int
    network_info_window_s: int
    parent_election_window_s: int
    secondary_schedule: bool
    join_beacon_interval_s: int
    join_beacon_after_s: int
    # unknown_nodes_portion: int
    # unknown_nodes_only: bool
    random_t_before_becoming_tmp_parent: bool
    t_before_becoming_tmp_parent: int

class ChildConfig(TypedDict):
    platform: SupportedPlatform
    radio_type: SupportedRadio
    first_op_at_s: int
    guard_time_ms: int
    op_duration_ms: int
    reply_gt_ms: int
    sleep_before_slot: bool
    sleep_if_unknown_interval: bool

class ScenarioGe4Config(TypedDict):
    deployment_interval_s: int
    network_detection_multipler: int
    parent_election_multipler: int
    parent_election_disabled: bool
    node_list: Dict[str, list[int]]

class ScenariosConfig(TypedDict):
    scenario_ge_4: ScenarioGe4Config

class LoRaWANGWConfig(TypedDict):
    platform: SupportedPlatform
    radio_type: SupportedRadio
    first_op_at_s: int

class LoRaWANEndNodeConfig(TypedDict):
    platform: SupportedPlatform
    radio_type: SupportedRadio
    first_op_at_s: int
    separation_s: int
    send_delay_s: int
    send_interval_s: int

class MariaDBConfig(TypedDict):
    host: str
    port: int
    db: str
    user: str
    passwd: str

class NodeEnergyCharacteristic(TypedDict):
    sleep_a: float
    on_a: float
    op_a: float
    v: float

class RadioEnergyCharacteristic(TypedDict):
    sleep_a: float
    on_a: float
    rx_a: float
    tx_a: float
    v: float    

class EnergyConfig(TypedDict):
    save_to_file: bool
    debug: bool
    v_load_drop: float
    node: Dict[SupportedPlatform, NodeEnergyCharacteristic]
    radio: Dict[SupportedRadio, RadioEnergyCharacteristic]

class ConfigType(TypedDict):
    general: GeneralConfig
    node: NodeConfig
    radio: RadioConfig
    lora: LoRaConfig
    parent: ParentConfig
    child: ChildConfig
    scenarios: ScenariosConfig
    lwangw: LoRaWANGWConfig
    lwaned: LoRaWANEndNodeConfig
    mariadb: MariaDBConfig
    energy: EnergyConfig
    locations: list[list[int]]


def load_config(config_path: str) -> None:

    if not os.path.isfile(config_path):
        print("Configuration file does not exist!")
        sys.exit()

    with open(config_path, "r", encoding='utf-8') as f:
        coglobs.CONFIG = json.load(f)


def save_config(config_path: str) -> None:
    with open(config_path, "w", encoding='utf-8') as outfile:
        outfile.write(json.dumps(coglobs.CONFIG, indent=4))
