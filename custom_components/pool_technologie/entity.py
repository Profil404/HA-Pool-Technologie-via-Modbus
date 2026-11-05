"""Base commune des entités de l'électrolyseur."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PoolTechnologieCoordinator
from .models import MODELS


class PoolTechnologieEntity(CoordinatorEntity[PoolTechnologieCoordinator]):
    """Une entité rafraîchie par le coordinator, liée à un champ de l'appareil.

    Le champ n'est lu que tant que l'entité est ajoutée à Home Assistant.
    """

    _attr_has_entity_name = True

    def __init__(self, coordinator: PoolTechnologieCoordinator, field: str | None) -> None:
        super().__init__(coordinator)
        self._field = field
        model_label = MODELS[coordinator.config_entry.data["model"]]["name"]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            name=model_label,
            manufacturer="Pool Technologie",
            model=model_label,
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self._field is None:
            return None
        return {"modbus_address": self.coordinator.device.address(self._field)}

    @property
    def _value(self) -> float | None:
        """La dernière valeur valide lue, ou None (hors plage, jamais lue)."""
        assert self._field is not None
        return self.coordinator.device.values.get(self._field)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self._field is not None:
            self.async_on_remove(self.coordinator.async_add_field(self._field))
