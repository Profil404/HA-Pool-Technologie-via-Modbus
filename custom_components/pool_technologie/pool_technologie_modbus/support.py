"""Modèles connus et statut de chaque champ par modèle.

Le mapping Modbus est le même d'un modèle à l'autre d'après le forum HACF
(https://forum.hacf.fr/t/electrolyseur-pool-technologie-via-le-port-rs485-justsalt-ibaregul-duo/),
mais tous les registres n'ont pas été vérifiés sur tous les modèles :

- ``CONFIRMED`` : vérifié sur ce modèle ;
- ``UNSUPPORTED`` : vérifié non fonctionnel sur ce modèle ;
- ``UNTESTED`` : pas encore vérifié (le cas par défaut).
"""

from __future__ import annotations

from enum import Enum, StrEnum


class Model(StrEnum):
    """Les modèles connus ; la valeur est la clé enregistrée en configuration."""

    IBASEL_DUO = "ibasel_duo"
    WATERAIR_SALT_GOLD_DUO = "waterair_salt_gold_duo"
    POOLSQUAD_UV = "poolsquad_uv"
    JUST_SALT_PRO = "just_salt_pro"
    RACER = "racer"


MODEL_NAMES: dict[Model, str] = {
    Model.IBASEL_DUO: "Ibiza iBasel Duo",
    Model.WATERAIR_SALT_GOLD_DUO: "WaterAir Salt Gold Duo",
    Model.POOLSQUAD_UV: "Poolsquad UV",
    Model.JUST_SALT_PRO: "Just Salt Pro",
    Model.RACER: "Racer",
}


class Support(Enum):
    """Le statut d'un champ sur un modèle."""

    CONFIRMED = "confirmed"
    UNTESTED = "untested"
    UNSUPPORTED = "unsupported"


ALL_MODELS = frozenset(Model)

# Diagnostics cellule (heures de fonctionnement 4463, inversion 4170).
# L'iBasel Duo est exclu : l'iBaRegul (boîtier de régulation) ne remonte pas ces
# données depuis l'iBaSel (boîtier séparé qui pilote la cellule).
_CELL_DIAGNOSTICS_CONFIRMED = frozenset({Model.POOLSQUAD_UV, Model.JUST_SALT_PRO})
_CELL_DIAGNOSTICS_UNSUPPORTED = frozenset({Model.IBASEL_DUO})

_CONFIRMED: dict[str, frozenset[Model]] = {
    "ph": ALL_MODELS,
    "water_temperature": ALL_MODELS,
    "salt": ALL_MODELS,
    "orp": ALL_MODELS,
    "reported_pool_volume": ALL_MODELS,
    "reported_ph_setpoint": ALL_MODELS,
    "reported_orp_setpoint": ALL_MODELS,
    "ph_setpoint": ALL_MODELS,
    "orp_setpoint": ALL_MODELS,
    # Même mapping que la consigne pH, confirmé sur tous les modèles.
    "ph_corrector_concentration": ALL_MODELS,
    "boost_remaining": ALL_MODELS,
    "boost_flag": ALL_MODELS,
    "ph_regulation": ALL_MODELS,
    # Poolsquad UV (Pierre_Brdn) et Racer (nadlio, issue #4).
    "cell_voltage": frozenset({Model.POOLSQUAD_UV, Model.RACER}),
    # Racer (nadlio, issue #4) et Poolsquad UV (pierrebaridon63, issue #8).
    "cell_current": frozenset({Model.POOLSQUAD_UV, Model.RACER}),
    "cell_power": frozenset({Model.POOLSQUAD_UV, Model.RACER}),
    # Poolsquad UV (pierrebaridon63, issue #9), valeurs identiques à l'appli.
    "electrolysis_ratio": frozenset({Model.POOLSQUAD_UV}),
    "uv_ratio": frozenset({Model.POOLSQUAD_UV}),
    "operating_hours": _CELL_DIAGNOSTICS_CONFIRMED,
    "cell_inversion_interval": _CELL_DIAGNOSTICS_CONFIRMED,
    # Poolsquad UV (Pierre_Brdn) et Racer (nadlio, issue #4).
    "electrolysis_setpoint": frozenset({Model.POOLSQUAD_UV, Model.RACER}),
    # Just Salt Pro (Locodice67, PR #5) et Poolsquad UV en écriture
    # (pierrebaridon63, issue #8).
    "pool_volume": frozenset({Model.POOLSQUAD_UV, Model.JUST_SALT_PRO}),
}

_UNSUPPORTED: dict[str, frozenset[Model]] = {
    # L'iBaRegul Duo ne communique pas cette donnée depuis l'iBaSel : registre
    # à 0 en permanence, confirmé par test.
    "cell_voltage": frozenset({Model.IBASEL_DUO}),
    "operating_hours": _CELL_DIAGNOSTICS_UNSUPPORTED,
    "cell_inversion_interval": _CELL_DIAGNOSTICS_UNSUPPORTED,
    # Registre figé quelle que soit la valeur écrite sur l'iBasel Duo, confirmé
    # par test direct.
    "electrolysis_setpoint": frozenset({Model.IBASEL_DUO}),
}


def support(model: str, field: str) -> Support:
    """Le statut de ``field`` sur ``model``.

    Lève ``ValueError`` pour un modèle inconnu et ``KeyError`` pour un champ
    inconnu.
    """
    known = Model(model)
    if field not in _CONFIRMED:
        raise KeyError(field)
    if known in _UNSUPPORTED.get(field, ()):
        return Support.UNSUPPORTED
    if known in _CONFIRMED[field]:
        return Support.CONFIRMED
    return Support.UNTESTED
