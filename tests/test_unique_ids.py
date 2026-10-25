"""Non-régression : les entités créées sont exactement celles de la v261029.

``fixtures/entities_v261029.json`` a été relevé en faisant tourner le code de
la v261029 sous Home Assistant 2026.10.1 (pymodbus simulé), pour chaque modèle,
avec la sonde pH déclarée, non déclarée ou absente de la configuration (entrées
créées avant la v261001), et avec ou sans sonde ORP.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.pool_technologie.const import DOMAIN

from .conftest import ENTRY_ID, FakeModbus, entry_data

REFERENCE: dict[str, list[dict[str, Any]]] = json.loads(
    (Path(__file__).parent / "fixtures/entities_v261029.json").read_text(encoding="utf-8")
)


def dump(hass: HomeAssistant, entry: MockConfigEntry) -> list[dict[str, Any]]:
    registry = er.async_get(hass)
    rows = []
    for e in er.async_entries_for_config_entry(registry, entry.entry_id):
        state = hass.states.get(e.entity_id)
        rows.append(
            {
                "domain": e.domain,
                "unique_id": e.unique_id.replace(entry.entry_id, "{entry_id}"),
                "entity_id": e.entity_id,
                "disabled_by": e.disabled_by,
                "entity_category": e.entity_category,
                "original_icon": e.original_icon,
                "original_device_class": e.original_device_class,
                "unit_of_measurement": e.unit_of_measurement,
                "translation_key": e.translation_key,
                "has_entity_name": e.has_entity_name,
                "attributes": None
                if state is None
                else {k: v for k, v in state.attributes.items() if k != "friendly_name"},
            }
        )
    return sorted(rows, key=lambda r: (r["domain"], r["unique_id"]))


def test_reference_covers_every_combination() -> None:
    assert len(REFERENCE) == 5 * 3 * 2


@pytest.mark.parametrize("key", sorted(REFERENCE))
async def test_entities_match_v261029(
    hass: HomeAssistant, fake_modbus: FakeModbus, key: str
) -> None:
    model, ph, orp = (part.split("=")[-1] for part in key.split("|"))
    data = entry_data(model=model, regulation_orp=orp == "True")
    if ph == "absent":
        del data["sonde_ph"]
    else:
        data["sonde_ph"] = ph == "True"
    entry = MockConfigEntry(domain=DOMAIN, data=data, entry_id=ENTRY_ID, title=model)
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert dump(hass, entry) == REFERENCE[key]
