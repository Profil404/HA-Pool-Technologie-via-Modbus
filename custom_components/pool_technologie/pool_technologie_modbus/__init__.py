"""Lire et piloter les électrolyseurs Pool Technologie sur Modbus.

La bibliothèque reçoit un ``ModbusUnit`` de ``modbus-connection`` et n'ouvre
ni ne ferme jamais de connexion. Voir ``README.md``.
"""

from .components import Cell, Controls, Measurements, ReportedSetpoints, Setpoints
from .device import (
    BOOST_FLAG_ON,
    BOOST_MINUTES,
    POLL_ORDER,
    WRITE_SETTLE,
    PoolTechnologieDevice,
)
from .exceptions import PoolTechnologieError, WriteNotConfirmedError
from .fields import Register, register
from .support import MODEL_NAMES, Model, Support, support

__all__ = [
    "BOOST_FLAG_ON",
    "BOOST_MINUTES",
    "MODEL_NAMES",
    "POLL_ORDER",
    "Cell",
    "Controls",
    "Measurements",
    "Model",
    "PoolTechnologieDevice",
    "PoolTechnologieError",
    "Register",
    "ReportedSetpoints",
    "Setpoints",
    "Support",
    "WRITE_SETTLE",
    "WriteNotConfirmedError",
    "register",
    "support",
]
