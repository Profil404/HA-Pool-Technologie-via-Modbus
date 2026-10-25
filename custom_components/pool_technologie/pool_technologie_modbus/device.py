"""L'objet appareil : un électrolyseur Pool Technologie derrière un ``ModbusUnit``."""

from __future__ import annotations

import asyncio
from collections.abc import Iterable, Mapping
from types import MappingProxyType
from typing import TYPE_CHECKING

from modbus_connection import ModbusConnectionError, ModbusError, ModbusTimeoutError
from modbus_connection.model import Component, ComponentGroup, Device, UpdateReport

from .components import Cell, Controls, Measurements, ReportedSetpoints, Setpoints
from .exceptions import WriteNotConfirmedError
from .fields import Register

if TYPE_CHECKING:
    from modbus_connection import ModbusUnit

# Ordre des lectures d'un cycle, une requête FC03 d'un registre par adresse.
# C'est l'ordre historique de l'intégration : capteurs, puis réglages et
# commandes. Une adresse absente de la liste est lue après, par ordre croissant.
POLL_ORDER: tuple[int, ...] = (
    4111, 259, 260, 261, 262, 4207, 4235, 1061, 1062, 1063, 2051, 2050, 4463,
    4168, 4208, 4170, 4188, 4200,
)  # fmt: skip

# Pause entre une écriture et sa relecture de confirmation : l'appareil a
# besoin d'un instant pour appliquer la valeur.
WRITE_SETTLE = 0.5

BOOST_MINUTES = 1440  # 24 h
BOOST_FLAG_ON = 256

_COMPONENTS: tuple[type[Component], ...] = (
    Measurements,
    ReportedSetpoints,
    Setpoints,
    Controls,
    Cell,
)


def _reader_name(address: int) -> str:
    return f"address_{address}"


class PoolTechnologieDevice(Device):
    """Un électrolyseur Pool Technologie.

    L'appareil ne lit que les champs choisis par ``select()``. Chaque adresse
    est lue par sa propre requête et forme son propre sous-système dans le
    rapport de ``async_update()`` : un registre refusé n'empêche pas les
    autres d'être lus.

    La bibliothèque n'ouvre ni ne ferme jamais la connexion : elle appartient
    à l'appelant.
    """

    write_settle: float = WRITE_SETTLE

    def __init__(self, unit: ModbusUnit) -> None:
        super().__init__(unit)
        self.measurements = Measurements(unit)
        self.reported_setpoints = ReportedSetpoints(unit)
        self.setpoints = Setpoints(unit)
        self.controls = Controls(unit)
        self.cell = Cell(unit)
        self._fields: dict[str, tuple[Component, Register]] = {}
        for component in (
            self.measurements,
            self.reported_setpoints,
            self.setpoints,
            self.controls,
            self.cell,
        ):
            for name, field in component.declared_fields.items():
                assert isinstance(field, Register)
                self._fields[name] = (component, field)
        self._polled: list[str] = []
        self._reader_fields: dict[str, list[tuple[Component, str]]] = {}
        self._values: dict[str, float | None] = {}

    @property
    def field_names(self) -> tuple[str, ...]:
        """Tous les champs de l'appareil, dans l'ordre de déclaration."""
        return tuple(self._fields)

    @property
    def values(self) -> Mapping[str, float | None]:
        """La dernière valeur lue de chaque champ sélectionné.

        ``None`` pour une lecture hors plage. Un champ dont la lecture a
        échoué garde sa valeur précédente ; un champ jamais lu est absent.
        """
        return MappingProxyType(self._values)

    @property
    def boost_active(self) -> bool | None:
        """Si le mode boost est en cours (minutes restantes > 0)."""
        remaining = self._values.get("boost_remaining")
        return None if remaining is None else remaining > 0

    @property
    def ph_regulation_active(self) -> bool | None:
        """Si la régulation pH automatique est activée."""
        value = self._values.get("ph_regulation")
        return None if value is None else value > 0

    def field(self, name: str) -> Register:
        """Le champ ``name``. Lève ``KeyError`` pour un champ inconnu."""
        return self._fields[name][1]

    def address(self, name: str) -> int:
        """L'adresse Modbus du champ ``name``."""
        return self.field(name).address

    def select(self, names: Iterable[str]) -> None:
        """Choisit les champs que ``async_update()`` lit.

        Lève ``KeyError`` pour un champ inconnu.
        """
        by_address: dict[int, list[str]] = {}
        for name in dict.fromkeys(names):
            by_address.setdefault(self.address(name), []).append(name)
        # Un lecteur retiré passe à None plutôt que d'être supprimé : une mise à
        # jour en cours le saute.
        for reader in self._polled:
            setattr(self, reader, None)
        order = {address: index for index, address in enumerate(POLL_ORDER)}
        self._polled = []
        self._reader_fields = {}
        for address in sorted(by_address, key=lambda a: (order.get(a, len(order)), a)):
            members: list[Component] = []
            fields: list[tuple[Component, str]] = []
            for component_class in _COMPONENTS:
                wanted = [
                    name
                    for name in by_address[address]
                    if type(self._fields[name][0]) is component_class
                ]
                if not wanted:
                    continue
                member = component_class(self.modbus_unit)
                member.restrict_fields(wanted)
                members.append(member)
                fields.extend((member, name) for name in wanted)
            reader = _reader_name(address)
            setattr(
                self,
                reader,
                members[0] if len(members) == 1 else ComponentGroup(self.modbus_unit, members),
            )
            self._polled.append(reader)
            self._reader_fields[reader] = fields
        selected = {name for fields in by_address.values() for name in fields}
        self._values = {k: v for k, v in self._values.items() if k in selected}

    async def async_update(self) -> UpdateReport:
        """Lit les champs choisis, une requête par adresse.

        Le rapport nomme chaque adresse ``address_<n>``. Une erreur propre à
        une adresse (exception Modbus, réponse inutilisable) va dans
        ``report.failed`` sans arrêter les suivantes.

        Lève ``ModbusConnectionError`` si la liaison tombe et
        ``ModbusTimeoutError`` si l'appareil ne répond pas, dès la première
        adresse concernée : un appareil éteint en cours de cycle ferait sinon
        attendre son délai à chaque adresse restante. Les valeurs lues avant
        restent acquises.
        """
        # select() peut être appelé pendant la lecture : on garde le plan de
        # départ jusqu'au bout.
        polled, reader_fields = self._polled, self._reader_fields
        report = UpdateReport()
        try:
            for name in polled:
                reader = getattr(self, name)
                if reader is None:
                    continue  # retiré par select() pendant la lecture
                try:
                    await reader.async_update(notify=False)
                except (ModbusConnectionError, ModbusTimeoutError):
                    raise
                except ModbusError as err:
                    report.failed[name] = err
                else:
                    report.updated.add(name)
        finally:
            for reader in report.updated:
                for member, field in reader_fields[reader]:
                    self._values[field] = getattr(member, field)
        return report

    async def async_validate(self) -> None:
        """Vérifie que l'appareil répond, en lisant la température de l'eau.

        Lève ``ModbusError`` si la lecture échoue.
        """
        probe = Measurements(self.modbus_unit)
        probe.restrict_fields(["water_temperature"])
        await probe.async_update(notify=False)

    async def async_write(self, name: str, value: float) -> None:
        """Écrit ``value`` dans le champ ``name``, puis confirme par relecture.

        Lève ``ModbusError`` si l'écriture ou la relecture échoue,
        ``WriteNotConfirmedError`` si la valeur relue diffère,
        ``AttributeError`` pour un champ en lecture seule et ``ValueError``
        pour une valeur hors de 0-65535 une fois convertie.
        """
        component, field = self._fields[name]
        await component.write(name, value)
        await self._async_confirm(name, field.to_raw(value))

    async def async_set_boost(self, enabled: bool) -> None:
        """Active le boost pour 24 h, ou l'arrête.

        L'activation écrit la durée puis le drapeau ; l'arrêt remet la durée
        à zéro sans toucher au drapeau. Seule la durée est relue. Mêmes
        exceptions que ``async_write()``.
        """
        if enabled:
            await self.controls.write("boost_remaining", BOOST_MINUTES)
            await self.controls.write("boost_flag", BOOST_FLAG_ON)
            await self._async_confirm("boost_remaining", BOOST_MINUTES)
        else:
            await self.controls.write("boost_remaining", 0)
            await self._async_confirm("boost_remaining", 0)

    async def async_set_ph_regulation(self, enabled: bool) -> None:
        """Active ou désactive la régulation pH automatique."""
        await self.async_write("ph_regulation", 1 if enabled else 0)

    async def _async_confirm(self, name: str, expected: int) -> None:
        """Relit le champ après ``write_settle`` secondes et le compare."""
        field = self.field(name)
        await asyncio.sleep(self.write_settle)
        (word,) = await self.modbus_unit.read_holding_registers(field.address, 1)
        if abs(word - expected) > field.tolerance:
            raise WriteNotConfirmedError(name, field.address, expected, word)
