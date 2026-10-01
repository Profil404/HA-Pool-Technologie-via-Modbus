from .const import CONF_REGULATION_ORP, CONF_SONDE_PH


def get_option(config_entry, key, default):
    """Les options (modifiables après coup) priment sur les données d'installation."""
    return config_entry.options.get(key, config_entry.data.get(key, default))


def has_ph_probe(config_entry):
    # Défaut True : les installations existantes (sans cette option) ne changent pas.
    return get_option(config_entry, CONF_SONDE_PH, True)


def has_orp_probe(config_entry):
    return get_option(config_entry, CONF_REGULATION_ORP, False)
