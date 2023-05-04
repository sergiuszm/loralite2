from __future__ import annotations
from typing import TYPE_CHECKING, Tuple
import math
from loralite.simulator.mobility import get_distance
from numpy import random, ndarray, lib, full
from loralite.simulator.globals import LIST_OF_NODES
from loralite.simulator.utils import round2

if TYPE_CHECKING:
    from loralite.simulator.definitions import DeviceType

RX_POWER_TABLE: ndarray = full((0, 0), 1.0)

class LogDistancePropagationLossModel:

    def __init__(self, exponent: float, ref_distance: int, ref_loss: float, sigma: float = 0.0):
        self.exponent = exponent
        self.ref_distance = ref_distance
        self.ref_loss = ref_loss
        self.sigma = sigma

    def get_rx_power(self, lou_a: DeviceType, lou_b: DeviceType, tx_power_dbm: int) -> Tuple[float, str]:
        global RX_POWER_TABLE
        log = ''
        distance = get_distance(lou_a, lou_b)

        if distance <= self.ref_distance:
            return tx_power_dbm - self.ref_loss, log

        if self.sigma == 0.0:
            try:
                rxc = RX_POWER_TABLE.item(lou_a.id, lou_b.id)
                if rxc >= 0.0:
                    rxc = self.calculate_rx_power(distance)
                    RX_POWER_TABLE[lou_a.id][lou_b.id] = rxc
            except IndexError:
                d_size = LIST_OF_NODES.peekitem(-1)[0] + 1
                if len(RX_POWER_TABLE) == 0:
                    RX_POWER_TABLE = full((d_size, d_size), 1.0)
                else:
                    current_shape = RX_POWER_TABLE.shape
                    pad_size = d_size - current_shape[0]
                    RX_POWER_TABLE = lib.pad(RX_POWER_TABLE, ((0, pad_size), (0, pad_size)), 'constant', constant_values=(1))
                rxc = self.calculate_rx_power(distance)
                RX_POWER_TABLE[lou_a.id][lou_b.id] = rxc
        else:
            rxc = self.calculate_rx_power(distance)
        
        log = f'distance={distance}m, reference-attenuation={-self.ref_loss}db, attenuation coefficient={rxc}db'

        return round2(tx_power_dbm + rxc), log
        # return round(tx_power_dbm + rxc, 2), log

    def calculate_rx_power(self, distance: float) -> float:
        path_loss_db = 10 * self.exponent * math.log10(distance / self.ref_distance) + random.normal(0.0, self.sigma)
        rxc = -self.ref_loss - path_loss_db

        return rxc

    # def get_rx_power(self, lou_a: DeviceType, lou_b: DeviceType, tx_power_dbm: int) -> Tuple[float, str]:
    #     distance = get_distance(lou_a, lou_b)

    #     log = ''
    #     if distance <= self.ref_distance:
    #         return tx_power_dbm - self.ref_loss, log

    #     path_loss_db = 10 * self.exponent * math.log10(distance / self.ref_distance) + random.normal(0.0, self.sigma)
    #     rxc = -self.ref_loss - path_loss_db

    #     log = f'distance={distance}m, reference-attenuation={-self.ref_loss}db, attenuation coefficient={rxc}db'

    #     return int((tx_power_dbm + rxc)*(10**2)+0.5)/(10**2), log

    def calculate_max_distance(self, tx_power_dbm: int, max_sensitivity: int) -> float:
        distance, sensitivity = [self.ref_distance, 0.0]
        while sensitivity > max_sensitivity:
            distance += 1
            if distance <= self.ref_distance:
                return tx_power_dbm - self.ref_loss

            path_loss_db = 10 * self.exponent * math.log10(distance / self.ref_distance) + random.normal(0.0, self.sigma)
            rxc = -self.ref_loss - path_loss_db
            sensitivity = round2(float(tx_power_dbm) + rxc)

        return distance

PROPAGATION_MODEL = LogDistancePropagationLossModel(2.9, 5, 55.75)

# "Characterization of LoRa Point-to-Point Path Loss: Measurement Campaigns and Modeling Considering Censored Data"
# https://doi.org/10.1109/JIOT.2019.2953804
# PROPAGATION_MODEL = LogDistancePropagationLossModel(2.0, 1, 95.5)

# PROPAGATION_MODEL = LogDistancePropagationLossModel(2.0, 1, 91.1)
