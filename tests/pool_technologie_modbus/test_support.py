"""Statut confirmé, non testé ou non fonctionnel, repris de models.py v261029."""

from __future__ import annotations

import pytest

from custom_components.pool_technologie.pool_technologie_modbus import (
    MODEL_NAMES,
    Model,
    PoolTechnologieDevice,
    Support,
    support,
)

C, U, X = Support.CONFIRMED, Support.UNTESTED, Support.UNSUPPORTED
ORDER = ("ibasel_duo", "waterair_salt_gold_duo", "poolsquad_uv", "just_salt_pro", "racer")

# Une ligne par champ, une colonne par modèle dans l'ordre ci-dessus.
EXPECTED = {
    "ph": (C, C, C, C, C),
    "water_temperature": (C, C, C, C, C),
    "salt": (C, C, C, C, C),
    "orp": (C, C, C, C, C),
    "reported_pool_volume": (C, C, C, C, C),
    "reported_ph_setpoint": (C, C, C, C, C),
    "reported_orp_setpoint": (C, C, C, C, C),
    "cell_voltage": (X, U, C, U, C),
    "cell_current": (U, U, C, U, C),
    "cell_power": (U, U, C, U, C),
    "electrolysis_ratio": (U, U, C, U, U),
    "uv_ratio": (U, U, C, U, U),
    "operating_hours": (X, U, C, C, U),
    "ph_setpoint": (C, C, C, C, C),
    "orp_setpoint": (C, C, C, C, C),
    "ph_corrector_concentration": (C, C, C, C, C),
    "electrolysis_setpoint": (X, U, C, U, C),
    "pool_volume": (U, U, C, C, U),
    "cell_inversion_interval": (X, U, C, C, U),
    "boost_remaining": (C, C, C, C, C),
    "boost_flag": (C, C, C, C, C),
    "ph_regulation": (C, C, C, C, C),
}


def test_models() -> None:
    assert [model.value for model in Model] == list(ORDER)
    assert list(MODEL_NAMES.values()) == [
        "Ibiza iBasel Duo",
        "WaterAir Salt Gold Duo",
        "Poolsquad UV",
        "Just Salt Pro",
        "Racer",
    ]


@pytest.mark.parametrize("field", sorted(EXPECTED))
def test_support(field: str) -> None:
    assert tuple(support(model, field) for model in ORDER) == EXPECTED[field]


def test_every_device_field_has_a_status(mock_modbus_unit) -> None:
    assert set(PoolTechnologieDevice(mock_modbus_unit).field_names) == set(EXPECTED)


def test_unknown_model_or_field() -> None:
    with pytest.raises(ValueError):
        support("neopool", "ph")
    with pytest.raises(KeyError):
        support("racer", "filtration")
