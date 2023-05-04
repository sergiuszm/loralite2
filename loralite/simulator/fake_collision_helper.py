from __future__ import annotations
from typing import List, Dict
import uuid
from sortedcontainers import SortedDict
from loralite.simulator.definitions import BufferedPacket
import math
from loralite.simulator.toa import TOA

class FakeInTheAir:
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
        self.transmissions: Dict[int, FakeInTheAir.PacketHelper] = SortedDict()
        self.pdt = math.ceil(TOA.get_symbols_time() * siu)
        self.band = band
        self.siu = siu

    def register_packet(self, packet: BufferedPacket) -> int:
        packet2_id = uuid.uuid1().int
        packet2 = FakeInTheAir.PacketHelper(packet)
        self.transmissions[packet2_id] = packet2

        return packet2_id
    
    # Based on: https://github.com/signetlabdei/lorawan/blob/develop/model/lora-interference-helper.cc
    # by Davide Magrin <magrinda@dei.unipd.it>
    def is_destroyed_by_interference(self, packet_id: int) -> None:
        if self.transmissions[packet_id].is_destroyed_by_interference:
            return

        self.transmissions[packet_id].is_destroyed_by_interference = False
