from .controller import PoolController
from .const import DOMAIN, SCAN_INTERVAL, CONF_SCAN_INTERVAL
from .modbus_handler import ModbusHandler

PLATFORMS = ["sensor", "number", "binary_sensor", "switch"]

async def async_setup_entry(hass, entry):
    hass.data.setdefault(DOMAIN, {})

    data = dict(entry.data)

    host = data["host"]
    port = data["port"]
    unit_id = data["unit_id"]
    handler = ModbusHandler(host, port, unit_id)

    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, data.get(CONF_SCAN_INTERVAL, SCAN_INTERVAL))
    controller = PoolController(hass, lambda now: None, scan_interval, handler)

    hass.data[DOMAIN][entry.entry_id] = {
        **data,
        "controller": controller,
        "scan_interval": scan_interval,
    }

    await controller.start()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True

async def _async_update_listener(hass, entry):
    """Recharge l'intégration quand les options changent (ex: régulation ORP)."""
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass, entry):
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        controller = hass.data[DOMAIN][entry.entry_id]["controller"]
        await controller.stop()
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded
