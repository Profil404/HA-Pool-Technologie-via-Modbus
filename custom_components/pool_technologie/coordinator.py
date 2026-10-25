"""Rafraîchissement périodique de l'électrolyseur."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from modbus_connection import ModbusError
from modbus_connection.model import UpdateReport

from .pool_technologie_modbus import PoolTechnologieDevice

_LOGGER = logging.getLogger(__name__)

# Cycles ratés d'affilée avant que le capteur de communication passe à "off" :
# un cycle isolé en échec n'est pas une déconnexion. Les entités, elles, gardent
# leur dernière valeur pendant toute la coupure (pompe arrêtée la nuit).
FAILED_CYCLES_THRESHOLD = 3

type PoolTechnologieConfigEntry = ConfigEntry[PoolTechnologieCoordinator]


class PoolTechnologieCoordinator(DataUpdateCoordinator[UpdateReport]):
    """Lit l'électrolyseur à l'intervalle des options.

    Seuls les champs des entités ajoutées à Home Assistant sont lus : une
    entité désactivée ne coûte aucune lecture Modbus.

    Un cycle raté ne fait jamais échouer la mise à jour : les entités restent
    disponibles sur leur dernière valeur, et seul ``modbus_ok`` rend compte de
    la coupure.
    """

    config_entry: PoolTechnologieConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: PoolTechnologieConfigEntry,
        device: PoolTechnologieDevice,
        scan_interval: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=entry.title,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.device = device
        self._fields: Counter[str] = Counter()
        self._failed_cycles = 0
        self._ever_succeeded = False

    @property
    def modbus_ok(self) -> bool:
        """La communication est établie : un cycle a réussi depuis le
        démarrage, et le seuil de cycles ratés n'est pas atteint."""
        return self._ever_succeeded and self._failed_cycles < FAILED_CYCLES_THRESHOLD

    @callback
    def async_add_field(self, name: str) -> Callable[[], None]:
        """Ajoute un champ aux lectures ; retourne de quoi le retirer."""
        self._fields[name] += 1
        self.device.select(self._fields)

        @callback
        def remove() -> None:
            self._fields[name] -= 1
            if not self._fields[name]:
                del self._fields[name]
            self.device.select(self._fields)

        return remove

    async def _async_update_data(self) -> UpdateReport:
        try:
            report = await self.device.async_update()
        except ModbusError as err:
            return self._failed_cycle(err)
        if not report.updated:
            # Aucune lecture du cycle n'a abouti : même traitement qu'une
            # liaison coupée.
            return self._failed_cycle(
                ExceptionGroup("aucune lecture n'a abouti", list(report.failed.values()))
                if report.failed
                else None
            )
        for name, error in report.failed.items():
            _LOGGER.debug("Lecture Modbus en échec (%s) : %s", name, error)
        if self._failed_cycles >= FAILED_CYCLES_THRESHOLD:
            _LOGGER.info("Communication Modbus rétablie avec %s", self.name)
        self._failed_cycles = 0
        self._ever_succeeded = True
        return report

    def _failed_cycle(self, err: Exception | None) -> UpdateReport:
        self._failed_cycles += 1
        if self._failed_cycles == FAILED_CYCLES_THRESHOLD:
            # Une fois par coupure, pas à chaque cycle d'une nuit pompe arrêtée.
            _LOGGER.warning(
                "%s injoignable depuis %d cycles, dernières valeurs conservées : %s",
                self.name,
                FAILED_CYCLES_THRESHOLD,
                err,
            )
        else:
            _LOGGER.debug(
                "Cycle Modbus en échec (%d), dernières valeurs conservées : %s",
                self._failed_cycles,
                err,
            )
        return UpdateReport()
