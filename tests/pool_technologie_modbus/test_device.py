"""L'objet appareil sur l'unité en mémoire de modbus-connection."""

from __future__ import annotations

from modbus_connection import (
    IllegalDataAddressError,
    ModbusConnectionError,
    ModbusError,
    ModbusTimeoutError,
)
from modbus_connection.mock import MockModbusUnit, ReadEvent, WriteEvent
from modbus_connection.model import ComponentGroup
import pytest

from custom_components.pool_technologie.pool_technologie_modbus import (
    BOOST_FLAG_ON,
    BOOST_MINUTES,
    POLL_ORDER,
    WRITE_SETTLE,
    Cell,
    Controls,
    Measurements,
    PoolTechnologieDevice,
    PoolTechnologieError,
    ReportedSetpoints,
    Setpoints,
    WriteNotConfirmedError,
)

HOLDING = {
    259: 7234,  # pH 7,2
    260: 245,  # 24,5 °C
    261: 41,  # 4,1 g/L
    262: 700,  # 700 mV
    1061: 5000,
    1062: 3200,
    1063: 16,
    2050: 400,  # 50 %
    2051: 600,  # 75 %
    4111: 45,
    4168: 20,
    4170: 4,
    4182: 0,
    4188: 0,
    4200: 1,
    4207: 18432,  # pH 7,2
    4208: 15,
    4235: 650,
    4463: 1234,
}


@pytest.fixture
def unit(mock_modbus_unit: MockModbusUnit) -> MockModbusUnit:
    mock_modbus_unit.holding.update(HOLDING)
    return mock_modbus_unit


@pytest.fixture
def device(unit: MockModbusUnit) -> PoolTechnologieDevice:
    device = PoolTechnologieDevice(unit)
    device.write_settle = 0
    return device


def blocks(unit: MockModbusUnit) -> list[tuple[int, int]]:
    return [(event.address, event.count) for event in unit.read_events]


async def test_reads_one_register_per_address_in_historical_order(
    device: PoolTechnologieDevice, unit: MockModbusUnit
) -> None:
    device.select(device.field_names)
    report = await device.async_update()

    # Une requête FC03 d'un seul registre par adresse, jamais de bloc qui
    # traverserait une adresse non implémentée ; 4182 (drapeau du boost) n'est
    # dans l'ordre historique que parce qu'il est sélectionné ici.
    assert blocks(unit) == [(address, 1) for address in (*POLL_ORDER, 4182)]
    assert all(event.register_type == "holding" for event in unit.read_events)
    assert report.complete
    assert report.updated == {f"address_{a}" for a in (*POLL_ORDER, 4182)}


async def test_values(device: PoolTechnologieDevice) -> None:
    device.select(device.field_names)
    await device.async_update()

    assert dict(device.values) == {
        "ph": 7.2,
        "water_temperature": 24.5,
        "salt": 4.1,
        "orp": 700,
        "reported_pool_volume": 45,
        "reported_ph_setpoint": 7.2,
        "reported_orp_setpoint": 650,
        "ph_setpoint": 7.2,
        "orp_setpoint": 650,
        "electrolysis_setpoint": 20,
        "ph_corrector_concentration": 15,
        "pool_volume": 45,
        "boost_remaining": 0,
        "boost_flag": 0,
        "ph_regulation": 1,
        "cell_voltage": 5000,
        "cell_current": 3200,
        "cell_power": 16,
        "uv_ratio": 50.0,
        "electrolysis_ratio": 75.0,
        "operating_hours": 1234,
        "cell_inversion_interval": 4,
    }
    assert device.boost_active is False
    assert device.ph_regulation_active is True


async def test_shared_address_is_read_once(
    device: PoolTechnologieDevice, unit: MockModbusUnit
) -> None:
    # Le capteur et le réglage de la consigne pH lisent le même registre.
    device.select(["reported_ph_setpoint", "ph_setpoint"])
    assert isinstance(device.address_4207, ComponentGroup)  # type: ignore[attr-defined]
    await device.async_update()

    assert blocks(unit) == [(4207, 1)]
    assert device.values == {"reported_ph_setpoint": 7.2, "ph_setpoint": 7.2}


async def test_only_selected_fields_are_read(
    device: PoolTechnologieDevice, unit: MockModbusUnit
) -> None:
    device.select(["orp", "ph"])
    await device.async_update()
    assert blocks(unit) == [(259, 1), (262, 1)]

    unit.read_events.clear()
    device.select(["ph"])
    await device.async_update()
    assert blocks(unit) == [(259, 1)]
    assert dict(device.values) == {"ph": 7.2}

    unit.read_events.clear()
    device.select([])
    report = await device.async_update()
    assert blocks(unit) == []
    assert not report.updated


def test_select_rejects_an_unknown_field(device: PoolTechnologieDevice) -> None:
    with pytest.raises(KeyError):
        device.select(["filtration"])


async def test_out_of_range_reads_as_none(
    device: PoolTechnologieDevice, unit: MockModbusUnit
) -> None:
    device.select(["ph", "orp_setpoint", "reported_orp_setpoint"])
    unit.holding[259] = 14100  # pH 14,1
    unit.holding[4235] = 1000  # hors réglage (400-900), dans la plage physique
    await device.async_update()

    assert device.values == {"ph": None, "orp_setpoint": None, "reported_orp_setpoint": 1000}


async def test_missing_optional_register(
    device: PoolTechnologieDevice, unit: MockModbusUnit
) -> None:
    """Un registre que le modèle n'implémente pas n'empêche pas les autres."""
    device.select(["ph", "cell_voltage", "cell_current"])
    unit.fail_read(1061, IllegalDataAddressError())
    report = await device.async_update()

    assert set(report.failed) == {"address_1061"}
    assert isinstance(report.failed["address_1061"], IllegalDataAddressError)
    assert report.updated == {"address_259", "address_1062"}
    assert dict(device.values) == {"ph": 7.2, "cell_current": 3200}


async def test_failed_read_keeps_previous_value(
    device: PoolTechnologieDevice, unit: MockModbusUnit
) -> None:
    device.select(["ph", "salt"])
    await device.async_update()
    unit.holding[259] = 7500
    unit.holding[261] = 45
    unit.fail_read(259, IllegalDataAddressError())
    await device.async_update()

    assert dict(device.values) == {"ph": 7.2, "salt": 4.5}


async def test_dead_link_raises(device: PoolTechnologieDevice, unit: MockModbusUnit) -> None:
    device.select(["ph", "salt"])
    unit.fail_requests(ModbusConnectionError("liaison coupée"))
    with pytest.raises(ModbusConnectionError):
        await device.async_update()
    # La première lecture a échoué : on n'insiste pas sur les suivantes.
    assert blocks(unit) == [(259, 1)]


async def test_timeout_before_anything_answered_raises(
    device: PoolTechnologieDevice, unit: MockModbusUnit
) -> None:
    device.select(["ph", "salt"])
    unit.fail_read(259, ModbusTimeoutError())
    with pytest.raises(ModbusTimeoutError):
        await device.async_update()


@pytest.mark.parametrize("error", [ModbusTimeoutError(), ModbusConnectionError("coupée")])
async def test_device_gone_mid_cycle_stops_the_cycle(
    device: PoolTechnologieDevice, unit: MockModbusUnit, error: Exception
) -> None:
    """Appareil éteint en cours de cycle : pas un délai par adresse restante."""
    device.select(["ph", "salt", "orp"])
    unit.fail_read(261, error)
    with pytest.raises(type(error)):
        await device.async_update()

    assert blocks(unit) == [(259, 1), (261, 1)]  # 262 n'est pas tenté
    assert dict(device.values) == {"ph": 7.2}  # lu avant l'arrêt, acquis


async def test_validate(device: PoolTechnologieDevice, unit: MockModbusUnit) -> None:
    await device.async_validate()
    assert blocks(unit) == [(260, 1)]

    unit.fail_requests(ModbusConnectionError("injoignable"))
    with pytest.raises(ModbusConnectionError):
        await device.async_validate()


def test_field_and_address(device: PoolTechnologieDevice) -> None:
    assert device.address("boost_flag") == 4182
    assert device.field("ph_setpoint").tolerance == 1
    assert device.field("ph").unit == "pH"
    with pytest.raises(KeyError):
        device.address("filtration")


@pytest.mark.parametrize(
    "component",
    [Measurements, ReportedSetpoints, Setpoints, Controls, Cell],
)
async def test_full_component_read_never_merges_blocks(
    unit: MockModbusUnit, component: type[Measurements]
) -> None:
    """Même lu d'un bloc, un composant fait une requête par registre."""
    await component(unit).async_update()
    addresses = sorted({field.address for field in component.declared_fields.values()})  # type: ignore[union-attr]
    assert sorted(blocks(unit)) == [(address, 1) for address in addresses]


# -- écritures ----------------------------------------------------------------


async def test_write_confirms_by_reading_back(
    device: PoolTechnologieDevice, unit: MockModbusUnit
) -> None:
    writes: list[WriteEvent] = []
    unit.on_write(writes.append)
    await device.async_write("orp_setpoint", 700)

    assert writes == [WriteEvent("holding", 4235, [700], 0x06)]
    assert unit.read_events == [ReadEvent("holding", 4235, 1)]
    assert unit.holding[4235] == 700


async def test_write_waits_before_reading_back(
    device: PoolTechnologieDevice, unit: MockModbusUnit, monkeypatch: pytest.MonkeyPatch
) -> None:
    pauses: list[float] = []

    async def sleep(seconds: float) -> None:
        pauses.append(seconds)

    monkeypatch.setattr(
        "custom_components.pool_technologie.pool_technologie_modbus.device.asyncio.sleep", sleep
    )
    device.write_settle = WRITE_SETTLE
    await device.async_write("pool_volume", 32)
    assert pauses == [WRITE_SETTLE] == [0.5]


async def test_write_not_confirmed(device: PoolTechnologieDevice, unit: MockModbusUnit) -> None:
    # L'appareil accepte l'écriture mais garde son ancienne valeur.
    unit.on_write(lambda event: unit.holding.__setitem__(4168, 20))
    with pytest.raises(WriteNotConfirmedError) as err:
        await device.async_write("electrolysis_setpoint", 55)

    assert (err.value.field, err.value.address, err.value.expected, err.value.read) == (
        "electrolysis_setpoint",
        4168,
        55,
        20,
    )
    assert isinstance(err.value, PoolTechnologieError)
    assert isinstance(err.value, ModbusError)


async def test_ph_setpoint_accepts_one_lsb_difference(
    device: PoolTechnologieDevice, unit: MockModbusUnit
) -> None:
    unit.on_write(lambda event: unit.holding.__setitem__(4207, event.values[0] + 1))
    await device.async_write("ph_setpoint", 7.3)

    unit.on_write(lambda event: unit.holding.__setitem__(4207, event.values[0] + 2))
    with pytest.raises(WriteNotConfirmedError):
        await device.async_write("ph_setpoint", 7.4)


async def test_write_failure_propagates(
    device: PoolTechnologieDevice, unit: MockModbusUnit
) -> None:
    unit.fail_write(4208, ModbusConnectionError("liaison coupée"))
    with pytest.raises(ModbusConnectionError):
        await device.async_write("ph_corrector_concentration", 20)
    assert unit.read_events == []


async def test_write_read_only_field(device: PoolTechnologieDevice) -> None:
    with pytest.raises(AttributeError):
        await device.async_write("ph", 7)


async def test_boost_on_writes_duration_then_flag(
    device: PoolTechnologieDevice, unit: MockModbusUnit
) -> None:
    writes: list[WriteEvent] = []
    unit.on_write(writes.append)
    await device.async_set_boost(True)

    assert writes == [
        WriteEvent("holding", 4188, [BOOST_MINUTES], 0x06),
        WriteEvent("holding", 4182, [BOOST_FLAG_ON], 0x06),
    ]
    assert (BOOST_MINUTES, BOOST_FLAG_ON) == (1440, 256)
    assert unit.read_events == [ReadEvent("holding", 4188, 1)]


async def test_boost_off_leaves_the_flag(
    device: PoolTechnologieDevice, unit: MockModbusUnit
) -> None:
    unit.holding.update({4188: 1440, 4182: 256})
    writes: list[WriteEvent] = []
    unit.on_write(writes.append)
    await device.async_set_boost(False)

    assert writes == [WriteEvent("holding", 4188, [0], 0x06)]
    assert unit.holding[4182] == 256


async def test_boost_not_confirmed(device: PoolTechnologieDevice, unit: MockModbusUnit) -> None:
    unit.on_write(lambda event: unit.holding.__setitem__(4188, 0))
    with pytest.raises(WriteNotConfirmedError):
        await device.async_set_boost(True)


async def test_ph_regulation(device: PoolTechnologieDevice, unit: MockModbusUnit) -> None:
    await device.async_set_ph_regulation(False)
    assert unit.holding[4200] == 0
    await device.async_set_ph_regulation(True)
    assert unit.holding[4200] == 1


async def test_flags_unknown_before_first_read(device: PoolTechnologieDevice) -> None:
    assert device.boost_active is None
    assert device.ph_regulation_active is None


async def test_select_during_update(device: PoolTechnologieDevice, unit: MockModbusUnit) -> None:
    """Une entité retirée pendant un cycle ne fait pas échouer ce cycle."""
    device.select(["ph", "salt", "orp"])

    def ph_then_deselect() -> int:
        device.select(["ph"])
        return 7234

    unit.holding[259] = ph_then_deselect
    report = await device.async_update()

    assert report.updated == {"address_259"}
    assert not report.failed
    assert dict(device.values) == {"ph": 7.2}
