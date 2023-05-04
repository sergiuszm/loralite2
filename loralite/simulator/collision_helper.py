from __future__ import annotations
from typing import List, Dict, TYPE_CHECKING
import uuid
from sortedcontainers import SortedDict
from loralite.simulator.definitions import BufferedPacket
import math
from loralite.simulator.toa import TOA
from loralite.simulator.lora_phy import TX_PARAMS, SUBBANDS
from loralite.simulator.event import add_detached_event
from loralite.simulator.utils import round2

COLLISION_SNIR_GOURSAUD = [
  # SF7  SF8  SF9 SF10 SF11 SF12
    [6, -16, -18, -19, -19, -20], # SF7
    [-24, 6, -20, -22, -22, -22], # SF8
    [-27, -27, 6, -23, -25, -25], # SF9
    [-30, -30, -30, 6, -26, -28], # SF10
    [-33, -33, -33, -33, 6, -29], # SF11
    [-36, -36, -36, -36, -36, 6]  # SF12
]

DEREGISTER_OFFSET = 10

class InTheAir:
    class PacketHelper:
        def __init__(self, packet: BufferedPacket):
            self.t_start = packet['t_start']
            self.t_end = packet['t_end']
            self.packet = packet
            self.c_detected = False
            # TODO: implement c_before_preamble_detected
            self.c_before_preamble_detected = False
            self.is_destroyed_by_interference = False
            self.c_start = -1
            self.c_end = -1
            self.interfering_packets: List[int] = []
            self.culmulative_interference_energy = 0.0
            self.snir = 0.0
            self.snir_isolation = 0

    def __init__(self, band:float, siu: int) -> None:
        self.transmissions: Dict[int, InTheAir.PacketHelper] = SortedDict()
        self.pdt = math.ceil(TOA.get_symbols_time() * siu)
        self.band = band
        self.siu = siu

    def register_packet(self, packet: BufferedPacket) -> int:
        packet2_id = uuid.uuid1().int
        packet2 = InTheAir.PacketHelper(packet)
        self.transmissions[packet2_id] = packet2
        add_detached_event(packet2.t_end + DEREGISTER_OFFSET, self.deregister_packet, packet2_id)
        for packet1_id in self.transmissions:
            if packet1_id == packet2_id:
                continue
            packet1 = self.transmissions[packet1_id]
            
            if packet2.t_start > packet1.t_end:
                continue

            if packet1.t_start <= packet2.t_start <= packet1.t_start + self.pdt:
                packet1.c_before_preamble_detected = True
                packet2.c_before_preamble_detected = True

            p1 = range(packet1.t_start, packet1.t_end + 1)
            p2 = range(packet2.t_start, packet2.t_end + 1)
            p1s = set(p1)
            t_intersection = len(p1s.intersection(p2))

            if t_intersection > 0:
                packet1.c_detected = True
                packet2.c_detected = True
                if packet2_id not in packet1.interfering_packets:
                    packet1.interfering_packets.append(packet2_id)
                    self.calculate_interference_energy(packet1_id, t_intersection)
                    self.is_destroyed_by_interference(packet1_id)

                if packet1_id not in packet2.interfering_packets:
                    packet2.interfering_packets.append(packet1_id)
                    self.calculate_interference_energy(packet2_id, t_intersection)
                    self.is_destroyed_by_interference(packet2_id)

        return packet2_id

    def deregister_packet(self, packet_id: int) -> None:
        del self.transmissions[packet_id]

    # Based on: https://github.com/signetlabdei/lorawan/blob/develop/model/lora-interference-helper.cc
    # by Davide Magrin <magrinda@dei.unipd.it>
    def calculate_interference_energy(self, packet_id: int, t_interference: int) -> None:
        interferer_power = SUBBANDS[self.band][3]
        interferer_power_w = math.pow(10, interferer_power / 10) / 1000
        interference_energy = (t_interference / self.siu) * interferer_power_w
        self.transmissions[packet_id].culmulative_interference_energy += interference_energy
    
    # Based on: https://github.com/signetlabdei/lorawan/blob/develop/model/lora-interference-helper.cc
    # by Davide Magrin <magrinda@dei.unipd.it>
    def is_destroyed_by_interference(self, packet_id: int) -> None:
        if self.transmissions[packet_id].is_destroyed_by_interference:
            return

        duration = (self.transmissions[packet_id].t_end - self.transmissions[packet_id].t_start) / self.siu
        signal_power = SUBBANDS[self.band][3]
        signal_sf = TX_PARAMS['sf']
        signal_power_w = math.pow(10, signal_power / 10) / 1000
        signal_energy = duration * signal_power_w

        snir = 10 * math.log10(signal_energy / self.transmissions[packet_id].culmulative_interference_energy)
        self.transmissions[packet_id].snir = round2(snir)
        snir_isolation = COLLISION_SNIR_GOURSAUD[signal_sf - 7][signal_sf - 7]
        self.transmissions[packet_id].snir_isolation = snir_isolation

        if snir < float(snir_isolation):
            self.transmissions[packet_id].is_destroyed_by_interference = True
