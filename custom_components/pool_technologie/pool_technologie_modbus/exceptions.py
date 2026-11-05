"""Les exceptions propres à la bibliothèque.

Toutes dérivent de ``modbus_connection.ModbusError`` : un appelant qui attrape
``ModbusError`` les attrape aussi.
"""

from __future__ import annotations

from modbus_connection import ModbusError


class PoolTechnologieError(ModbusError):
    """Erreur de base de la bibliothèque."""


class WriteNotConfirmedError(PoolTechnologieError):
    """L'appareil a accepté l'écriture, mais la relecture ne la confirme pas."""

    def __init__(self, field: str, address: int, expected: int, read: int) -> None:
        self.field = field
        self.address = address
        self.expected = expected
        self.read = read
        super().__init__(f"{field} (adresse {address}) : {expected} écrit, {read} relu")
