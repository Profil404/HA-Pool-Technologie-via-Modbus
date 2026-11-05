"""Champ registre des électrolyseurs Pool Technologie."""

from __future__ import annotations

from typing import Literal

from modbus_connection.model import RegisterField

Rounding = Literal["round", "truncate"]

# Plage valide (min, max) incluse, dans l'unité du champ.
ValidRange = tuple[float, float]


class Register(RegisterField[float]):
    """Un registre holding 16 bits non signé, mis à l'échelle et borné.

    Le décodage vaut ``round(brut * scale, precision)``. Une valeur hors de
    ``valid`` se lit ``None`` : l'appareil renvoie parfois des lectures
    aberrantes (électrolyseur qui démarre, sonde absente), qu'il vaut mieux
    ignorer que publier.

    ``tolerance`` est l'écart brut accepté par la relecture de confirmation
    après une écriture : une consigne mise à l'échelle peut s'arrondir au bit
    de poids faible près.
    """

    def __init__(
        self,
        address: int,
        *,
        scale: float = 1,
        precision: int = 0,
        valid: ValidRange | None = None,
        unit: str | None = None,
        writable: bool = False,
        rounding: Rounding = "round",
        tolerance: int = 0,
    ) -> None:
        super().__init__(address, unit=unit, writable=writable)
        self.scale = scale
        self.precision = precision
        self.valid = valid
        self.rounding = rounding
        self.tolerance = tolerance

    def decode(self, words: list[int], scale_exponent: int | None = None) -> float | None:
        """Décode le mot lu ; ``None`` s'il sort de la plage valide."""
        value: float = round(words[0] * self.scale, self.precision)
        if self.valid is not None and not self.valid[0] <= value <= self.valid[1]:
            return None
        return value

    def to_raw(self, value: float) -> int:
        """Le mot à écrire pour ``value``.

        Lève ``ValueError`` si ce mot ne tient pas sur 16 bits non signés.
        """
        if self.scale != 1:
            raw = int(round(value / self.scale))
        elif self.rounding == "truncate":
            raw = int(value)
        else:
            raw = int(round(value))
        if not 0 <= raw <= 0xFFFF:
            raise ValueError(f"{self.name}: {value} donne {raw}, hors de 0-65535")
        return raw

    def encode(self, value: float, scale_exponent: int | None = None) -> list[int]:
        """Encode ``value`` en un mot de registre."""
        return [self.to_raw(value)]


def register(
    address: int,
    *,
    scale: float = 1,
    precision: int = 0,
    valid: ValidRange | None = None,
    unit: str | None = None,
    writable: bool = False,
    rounding: Rounding = "round",
    tolerance: int = 0,
) -> Register:
    """Déclare un registre de l'électrolyseur."""
    return Register(
        address,
        scale=scale,
        precision=precision,
        valid=valid,
        unit=unit,
        writable=writable,
        rounding=rounding,
        tolerance=tolerance,
    )
