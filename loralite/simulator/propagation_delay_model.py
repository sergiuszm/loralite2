from __future__ import annotations
from typing import TYPE_CHECKING
from loralite.simulator.mobility import get_distance

if TYPE_CHECKING:
    from loralite.simulator.definitions import DeviceType


class ConstantSpeedPropagationDelayModel:

    # The default value is the propagation speed of light in the vacuum.
    def __init__(self, speed: int = 299792458):
        self.speed = speed

    def get_delay(self, node1: DeviceType, node2: DeviceType) -> float:
        distance = get_distance(node1, node2)

        return float(distance) / float(self.speed)

DELAY_MODEL = ConstantSpeedPropagationDelayModel()