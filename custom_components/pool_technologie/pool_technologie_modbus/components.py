"""Les sous-systèmes de l'électrolyseur, un ``Component`` par fonction.

Chaque champ porte son adresse, son unité et la plage hors de laquelle une
lecture est ignorée. Les registres utiles sont séparés par des adresses que
l'appareil n'implémente pas : chaque composant déclare donc une plage lisible
d'un seul registre par champ, pour qu'aucune lecture groupée ne traverse ces
trous (voir le README).
"""

from __future__ import annotations

from modbus_connection.model import Component

from .fields import register

# pH, consignes pH : brut / 2560
PH_SETPOINT_SCALE = 0.000390625


class Measurements(Component):
    """Mesures de l'eau."""

    register_ranges = ((259, 259), (260, 260), (261, 261), (262, 262))

    ph = register(259, scale=0.001, precision=1, valid=(0, 14), unit="pH")
    water_temperature = register(260, scale=0.1, precision=1, valid=(-10, 60), unit="°C")
    salt = register(261, scale=0.1, precision=1, valid=(0, 20), unit="g/L")
    orp = register(262, valid=(0, 1200), unit="mV")


class ReportedSetpoints(Component):
    """Consignes telles que l'appareil les rapporte, bornes physiques.

    Mêmes registres que ``Setpoints``, avec les bornes et l'arrondi d'un
    affichage en lecture seule. Lus ensemble, ils ne coûtent qu'une requête
    par adresse.
    """

    register_ranges = ((4111, 4111), (4207, 4207), (4235, 4235))

    reported_pool_volume = register(4111, unit="m³")
    reported_ph_setpoint = register(
        4207, scale=PH_SETPOINT_SCALE, precision=1, valid=(0, 14), unit="pH"
    )
    reported_orp_setpoint = register(4235, valid=(0, 1200), unit="mV")


class Setpoints(Component):
    """Consignes réglables, bornées à la plage de réglage."""

    register_ranges = ((4111, 4111), (4168, 4168), (4207, 4207), (4208, 4208), (4235, 4235))

    ph_setpoint = register(
        4207,
        scale=PH_SETPOINT_SCALE,
        precision=2,
        valid=(6.0, 8.5),
        unit="pH",
        writable=True,
        tolerance=1,
    )
    orp_setpoint = register(4235, valid=(400, 900), unit="mV", writable=True, rounding="truncate")
    electrolysis_setpoint = register(
        4168, valid=(10, 100), unit="%", writable=True, rounding="truncate"
    )
    ph_corrector_concentration = register(4208, valid=(5, 50), unit="%", writable=True)
    pool_volume = register(4111, valid=(1, 250), unit="m³", writable=True)


class Controls(Component):
    """État et commandes : mode boost, régulation pH automatique."""

    register_ranges = ((4182, 4182), (4188, 4188), (4200, 4200))

    # Minutes de boost restantes (0 = arrêté) : le registre qui commande le boost.
    boost_remaining = register(4188, unit="min", writable=True)
    # Drapeau d'activation du boost (256), écrit à l'activation et jamais lu. Il
    # retombe à 0 de lui-même quand 4188 revient à 0 (observé sur un Just Salt Pro).
    boost_flag = register(4182, writable=True)
    ph_regulation = register(4200, writable=True)


class Cell(Component):
    """Cellule d'électrolyse : diagnostics et inversion de polarité."""

    register_ranges = (
        (1061, 1061),
        (1062, 1062),
        (1063, 1063),
        (2050, 2050),
        (2051, 2051),
        (4170, 4170),
        (4463, 4463),
    )

    cell_voltage = register(1061, valid=(0, 30000), unit="mV")
    cell_current = register(1062, valid=(0, 50000), unit="mA")
    cell_power = register(1063, valid=(0, 5000), unit="W")
    uv_ratio = register(2050, scale=0.125, valid=(0, 100), unit="%")
    electrolysis_ratio = register(2051, scale=0.125, valid=(0, 100), unit="%")
    operating_hours = register(4463, valid=(0, 100000), unit="h")
    cell_inversion_interval = register(4170, valid=(1, 24), unit="h", writable=True)
