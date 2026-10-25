from homeassistant.components.modbus import async_get_unit
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError
from modbus_connection import ModbusTcpParams

from .const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL, CONF_UNIT_ID, DOMAIN, SCAN_INTERVAL
from .coordinator import PoolTechnologieConfigEntry, PoolTechnologieCoordinator
from .options_helper import get_option
from .pool_technologie_modbus import PoolTechnologieDevice

PLATFORMS = ["sensor", "number", "binary_sensor", "switch"]


async def async_setup_entry(hass: HomeAssistant, entry: PoolTechnologieConfigEntry) -> bool:
    # La connexion appartient au modbus de Home Assistant, partagée avec tout ce
    # qui joint la même passerelle par lui ; il la rouvre à la requête suivante
    # quand elle tombe, et la ferme quand le dernier détenteur se décharge.
    try:
        unit = async_get_unit(
            hass,
            entry,
            ModbusTcpParams(host=entry.data[CONF_HOST], port=entry.data[CONF_PORT]),
            entry.data[CONF_UNIT_ID],
        )
    except HomeAssistantError as err:
        # La passerelle est déjà utilisée avec d'autres paramètres de liaison.
        raise ConfigEntryNotReady(str(err)) from err

    scan_interval = get_option(entry, CONF_SCAN_INTERVAL, SCAN_INTERVAL)
    coordinator = PoolTechnologieCoordinator(
        hass, entry, PoolTechnologieDevice(unit), scan_interval
    )
    entry.runtime_data = coordinator

    # Les entités déclarent leurs champs en s'ajoutant : la première lecture
    # vient après, en arrière-plan. Électrolyseur injoignable (pompe coupée la
    # nuit), le démarrage de Home Assistant n'attend pas son délai de connexion.
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_create_background_task(
        hass, coordinator.async_refresh(), f"{DOMAIN} première lecture"
    )

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: PoolTechnologieConfigEntry) -> None:
    """Recharge l'intégration quand les options changent (ex: régulation ORP)."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: PoolTechnologieConfigEntry) -> bool:
    # Rien à fermer : le modbus de Home Assistant libère la connexion.
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
