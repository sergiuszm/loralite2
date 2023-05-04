from __future__ import annotations
from typing import TypedDict, TYPE_CHECKING

if TYPE_CHECKING:
    from loralite.simulator.definitions import DeviceType
from loralite.simulator.exceptions import SimException

import crcmod

# In Europe, duty cycles are regulated by section 7.2.3 of the ETSI EN300.220 standard.
# This standard defines the following sub-bands and their duty cycles:
#     g (863.0 – 868.0 MHz): 1%
#     g1 (868.0 – 868.6 MHz): 1%
#     g2 (868.7 – 869.2 MHz): 0.1%
#     g3 (869.4 – 869.65 MHz): 10%
#     g4 (869.7 – 870.0 MHz): 1%
# LORA_BAND_868_0 = 868.0
# LORA_BAND_868_7 = 868.7
# LORA_BAND_869_4 = 869.4

# Semtech document TN1300.01 about ETSI regulations:
# https://lora-developers.semtech.com/?ACT=72&fid=30&aid=48_0znCpZpvImL3agza59hG&board_id=1
LORA_BAND_47 = 865.0
LORA_BAND_48 = 868.0
LORA_BAND_56B = 869.7

LORA_MAIN_BAND = LORA_BAND_48
LORA_SECONDARY_BAND = LORA_BAND_56B

SUBBANDS = {
    # start, end, duty, max Tx_dBm
    LORA_BAND_47: (865.0, 868.0, 0.01, 14),
    LORA_BAND_48: (868.0, 868.6, 0.01, 14),
    LORA_BAND_56B: (869.7, 870.0, 0.01, 14)
}

# SUBBANDS = {
#     # start, end, duty, max Tx_dBm
#     LORA_BAND_868_0: (868, 868.6, 0.01, 14),
#     LORA_BAND_868_7: (868.7, 869.2, 0.001, 14),
#     LORA_BAND_869_4: (869.4, 869.65, 0.1, 27),
# }

SF_7: int = 7
SF_8: int = 8
SF_9: int = 9
SF_10: int = 10
SF_11: int = 11
SF_12: int = 12

CR_1 = 1  # 4/5
CR_2 = 2  # 4/6
CR_3 = 3  # 4/7
CR_4 = 4  # 4/8

RX_SENSITIVITY = {
    SF_7: -124,
    SF_8: -127,
    SF_9: -130,
    SF_10: -133,
    SF_11: -135,
    SF_12: -137,
}

# EU863-870
# source: https://lora-developers.semtech.com/documentation/tech-papers-and-guides/the-book/packet-size-considerations/
DR_PAYLOAD_SIZE = {0: 51, 1: 51, 2: 51, 3: 115, 4: 222, 5: 222}

crc16 = crcmod.mkCrcFun(0x13D65, 0xFFFF, True, 0xFFFF)
crc32 = crcmod.mkCrcFun(0x104c11db7, 0xFFFFFFFF, True, 0xFFFFFFFF)

CRC_ENABLED = 1

# LoRaLitE
LORALITE_HEADER_SIZE = 5
CRC_SIZE = 2
TDMA_SIZE = 2
BA_SIZE = 1
PE_CT_SIZE = 1
PE_SIZE = 3
I_SIZE = 2

# LoRaWAN
MHDR_SIZE = 1
FHDR_SIZE = 7
FPORT_SIZE = 1
DEV_ADDR_SIZE = 4
FCTRL_SIZE = 1
FCNT_SIZE = 2
FOPTS_SIZE = 0
MIC_SIZE = 4

MHDR = 2  # Ftype:010[7..5] RFU:000[4..2] Major:00[1..0] - Ftype 010 - unconfirmed data uplink, 01000000(bin) = 2(dec) 
FCTRL = 0 # ADR:0 ADRACKReq:0 ACK:0 ClassB:0 FOptslen[3..0]: 000
FPORT = 1 # Port nr 1

class Params(TypedDict):
    sf: int
    cr: int
    bw: int
    dr: int
    preamble: int
    crc: int
    hd: int
    ldro: int
    max_payload: int
    band: float


TX_PARAMS = Params(
    sf=SF_12,
    cr=CR_4,
    bw=125000,
    dr=0,
    preamble=8,
    crc=CRC_ENABLED,
    hd=1,
    ldro=1,
    max_payload=DR_PAYLOAD_SIZE[0], # +2 if CRC and LoRaLitE, +4 if CRC and LoRaWAN (MIC)
    band=LORA_BAND_48,
)

# TX_PARAMS = {
#     "sf": SF_12,  # spreading factor (12, 11, 10, 9, 8, 7)
#     "cr": CR_4,  # coding rate (1, 2, 3, 4)
#     "bw": 125000,  # bandwidth in HZ (125000, 250000)
#     "dr": 0,  # data rate index  (0, 1, 2, 3, 4, 5) - for each sf
#     "preamble": 8,  # preamble length
#     "crc": 1,  # crc enabled
#     "hd": 1,  # header disabled
#     "ldro": 1,  # low data rate optimization
#     "max_payload": DR_PAYLOAD_SIZE[0],  # max payload size in Bytes
#     "band": LORA_BAND_868_0,
# }


class LoraBand:
    def __init__(self, band: float, sf: int):
        params = SUBBANDS[band]
        self.band = params[0]
        self.duty_cycle = params[2]
        self.tx_dbm = params[3]
        self.sf = sf

class Channel:
    def __init__(self) -> None:
        self.is_active = False
        self.collision = False
        self._node: DeviceType | None = None

    def set_active(self, node: DeviceType) -> None:
        if self._node is not None and self._node != node:
            # raise SimException('Channel can not be activated by other node while it is already active!')
            self.collision = True
        
        self._node = node
        self.is_active = True

    def deactivate(self, node: DeviceType) -> None:
        # if self._node != node:
            # raise SimException('Channel can not be deactivated by other node!')

        self.collision = False
        self.is_active = False
        self._node = None