import math
import loralite.simulator.globals as coglobs
from loralite.simulator.logger import logger
from loralite.simulator.lora_phy import TX_PARAMS, DR_PAYLOAD_SIZE
from sortedcontainers import SortedDict

class ToA:
    def __init__(
        self,
        sf: float,
        bw: int,
        preamble: int,
        cr: int,
        ldro: int,
        crc: int,
        hd: int,
        dr: int,
        fake_logger: bool = False,
    ):
        self.sf = sf
        self.bw = bw
        self.preamble = preamble
        self.cr = cr
        self.ldro = ldro
        self.crc = crc
        self.hd = hd
        self.dr = dr
        self.logger = logger
        self.calculated_toa = SortedDict()

        for pkt_size in range(1, DR_PAYLOAD_SIZE[self.dr] + 1):
            self.calculated_toa[pkt_size] = self.calculate_time_on_air(pkt_size, True)

        if fake_logger:
            self.logger._fake_logger = True

    def get_symbols_time(self, symbols: int = 5) -> float:
        # symbol duration
        t_symbol = math.pow(2, int(self.sf)) / self.bw

        # preamble duration
        t_preamble = (symbols + 4.25) * t_symbol

        return t_preamble

    def get_time_on_air(self, pkt_size: int) -> float:
        return float(self.calculated_toa[pkt_size])

    def calculate_time_on_air(self, pkt_size: int, on_init: bool = False) -> float:
        # symbol duration
        t_symbol = math.pow(2, int(self.sf)) / self.bw

        # preamble duration
        t_preamble = (self.preamble + 4.25) * t_symbol

        # low data rate optimization enabled if t_symbol > 16ms
        # read more: https://www.thethingsnetwork.org/forum/t/a-point-to-note-lora-low-data-rate-optimisation-flag/12007
        ldro = self.ldro
        if t_symbol > 0.016:
            ldro = 1

        # numerator and denominator of the time on air formula
        num = 8 * pkt_size - 4 * self.sf + 28 + 16 * self.crc - 20 * self.hd
        den = 4 * (self.sf - 2 * ldro)
        payload_symbol_count = 8 + max(math.ceil(num / den) * (self.cr + 4), 0)

        # payload duration
        t_payload = payload_symbol_count * t_symbol

        if not on_init:
            self.logger.debug(
                coglobs.SIM_TIME,
                f"SF: {self.sf}, headerDisabled: {self.hd}, codingRate: {self.cr}, "
                f"bandwidthHz: {self.bw}, nPreamble: {self.preamble}, crcEnabled: {self.crc}, "
                f"lowDataRateOptimizationEnabled: {ldro}",
            )
            self.logger.debug(coglobs.SIM_TIME, f"Packet of size {pkt_size} bytes")
            self.logger.debug(
                coglobs.SIM_TIME,
                f"Time computation: num = {num}, den = {den}, payloadSymbNb = {payload_symbol_count}, tSym = {t_symbol}",
            )
            self.logger.debug(coglobs.SIM_TIME, f"\ttPreamble = {t_preamble}")
            self.logger.debug(coglobs.SIM_TIME, f"\ttPayload = {t_payload}")
            self.logger.debug(coglobs.SIM_TIME, f"\tTotal time = {t_preamble + t_payload}")

        return t_preamble + t_payload


TOA = ToA(
    TX_PARAMS['sf'],
    TX_PARAMS['bw'],
    TX_PARAMS['preamble'],
    TX_PARAMS['cr'],
    TX_PARAMS['ldro'],
    TX_PARAMS['crc'],
    TX_PARAMS['hd'],
    TX_PARAMS['dr']
)
