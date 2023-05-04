from __future__ import annotations
from typing import TYPE_CHECKING
from loralite.simulator.globals import LIST_OF_NODES
from random import randint, random
from loralite.simulator.utils import round2

if TYPE_CHECKING:
    from loralite.simulator.node import Node

CURRENT_PN: int = -1

def set_packet_loss_modulo(node_id: int, plm: int) -> None:
    node: Node = LIST_OF_NODES[node_id]
    node.simulation_params['selected_for_pl'] = True
    node.simulation_params['plm'] = plm
    node.simulation_params['plm_res'] = randint(0, plm)
    node.simulation_params['based_on_modulo'] = True
    node.simulation_params['based_on_probability'] = False

def set_packet_loss_probability(node_id: int, probability: float) -> None:
    node: Node = LIST_OF_NODES[node_id]
    node.simulation_params['selected_for_pl'] = True
    node.simulation_params['plp'] = probability
    node.simulation_params['based_on_probability'] = True
    node.simulation_params['based_on_modulo'] = False

def make_decision_based_on_modulo(pkt_seq: int, plm: int, plm_res: int) -> bool:
    if pkt_seq % plm == plm_res:
        return False

    return True

def make_decition_based_on_probability(probability: float) -> bool:
    return random() < probability

def set_nr_of_packets_to_lose_in_a_row(node_id: int, pkts_to_lose: int, pkts_starting_seq: int = -1, pkts_from_pn: bool = False) -> None:
    node: Node = LIST_OF_NODES[node_id]
    node.simulation_params['selected_for_pl'] = True
    node.simulation_params['pkts_to_lose'] = pkts_to_lose
    node.simulation_params['pkts_starting_seq'] = pkts_starting_seq
    node.simulation_params['pkts_from_pn'] = pkts_from_pn

# Pacet Receive Ratio
def calculate_prr(received_count: int, should_receive: int) -> float:
    if should_receive == 0:
        return 0
    return round2((received_count / should_receive) * 100)