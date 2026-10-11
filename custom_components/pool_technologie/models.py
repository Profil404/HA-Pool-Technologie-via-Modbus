# Statut de chaque registre par modèle, utilisé pour décider si une entité est
# créée, et si elle est activée par défaut :
#   - modèle dans "confirmed"   -> entité créée et activée
#   - modèle dans "unsupported" -> entité non créée (confirmé non fonctionnel)
#   - sinon (non testé)         -> entité créée mais DÉSACTIVÉE par défaut :
#     l'utilisateur peut l'activer en un clic depuis la page de l'appareil pour
#     essayer, et nous faire un retour. Une entité désactivée ne coûte aucune
#     lecture Modbus.
# Le même principe confirmed/unsupported/non-testé s'applique aussi aux réglages
# modifiables (number) : une entité non confirmée est créée désactivée plutôt que
# pas créée du tout, l'utilisateur garde la main pour l'activer et tester à ses
# risques. Voir ELECTROLYSIS_SETPOINT, POOL_SIZE_SETPOINT, CELL_INVERSION_HOURS.
#
# Mapping Modbus identique d'un modèle à l'autre d'après le forum HACF
# (https://forum.hacf.fr/t/electrolyseur-pool-technologie-via-le-port-rs485-justsalt-ibaregul-duo/).

MODELS = {
    "ibasel_duo": {"name": "Ibiza iBasel Duo"},
    "waterair_salt_gold_duo": {"name": "WaterAir Salt Gold Duo"},
    "poolsquad_uv": {"name": "Poolsquad UV"},
    "just_salt_pro": {"name": "Just Salt Pro"},
    "racer": {"name": "Racer"},
}

ALL_MODELS = frozenset(MODELS)

# Clés des capteurs qui n'ont de sens qu'avec la sonde correspondante installée
PH_SENSOR_KEYS = {"ph", "consigne_ph"}
ORP_SENSOR_KEYS = {"orp", "consigne_orp"}

# Diagnostics cellule (alarmes 4172, heures de fonctionnement 4463, inversion 4170).
# L'iBasel Duo est exclu : l'iBaRegul (boîtier de régulation) ne remonte pas ces
# données depuis l'iBaSel (boîtier séparé qui pilote la cellule) — cf. tension_cellule.
CELL_DIAGNOSTICS_CONFIRMED = {"poolsquad_uv", "just_salt_pro"}
CELL_DIAGNOSTICS_UNSUPPORTED = {"ibasel_duo"}

SENSORS = [
    {
        "translation_key": "taille_bassin",
        "unique_id": "taille_bassin",
        "address": 4111,
        "unit": "m³",
        "scale": 1,
        "precision": 0,
        "icon": "mdi:texture-box",
        "confirmed": ALL_MODELS,
    },
    {
        "translation_key": "ph",
        "unique_id": "ph",
        "address": 259,
        "unit": "pH",
        "scale": 0.001,
        "precision": 1,
        "icon": "mdi:test-tube",
        "min_valid": 0,
        "max_valid": 14,
        "confirmed": ALL_MODELS,
    },
    {
        "translation_key": "temperature_eau",
        "unique_id": "temperature_eau",
        "address": 260,
        "unit": "°C",
        "scale": 0.1,
        "precision": 1,
        "icon": "mdi:thermometer-water",
        "device_class": "temperature",
        "min_valid": -10,
        "max_valid": 60,
        "confirmed": ALL_MODELS,
    },
    {
        "translation_key": "taux_sel",
        "unique_id": "taux_sel",
        "address": 261,
        "unit": "g/L",
        "scale": 0.1,
        "precision": 1,
        "icon": "mdi:shaker-outline",
        "min_valid": 0,
        "max_valid": 20,
        "confirmed": ALL_MODELS,
    },
    {
        "translation_key": "orp",
        "unique_id": "orp",
        "address": 262,
        "unit": "mV",
        "scale": 1,
        "precision": 0,
        "icon": "mdi:lightning-bolt",
        "min_valid": 0,
        "max_valid": 1200,
        "confirmed": ALL_MODELS,
    },
    {
        "translation_key": "consigne_ph",
        "unique_id": "consigne_ph",
        "address": 4207,
        "unit": "pH",
        "scale": 0.000390625,
        "precision": 1,
        "icon": "mdi:cog",
        "min_valid": 0,
        "max_valid": 14,
        "confirmed": ALL_MODELS,
    },
    {
        "translation_key": "consigne_orp",
        "unique_id": "consigne_orp",
        "address": 4235,
        "unit": "mV",
        "scale": 1,
        "precision": 0,
        "icon": "mdi:cog",
        "min_valid": 0,
        "max_valid": 1200,
        "confirmed": ALL_MODELS,
    },
    {
        "translation_key": "tension_cellule",
        "unique_id": "tension_cellule",
        "address": 1061,
        "unit": "mV",
        "scale": 1,
        "precision": 0,
        "icon": "mdi:sine-wave",
        "entity_category": "diagnostic",
        "min_valid": 0,
        "max_valid": 30000,
        # Confirmée sur Poolsquad UV (Pierre_Brdn) et Racer (nadlio, issue #4).
        "confirmed": {"poolsquad_uv", "racer"},
        # L'iBaRegul Duo (boîtier de régulation, expose le Modbus) ne communique pas cette
        # donnée depuis l'iBaSel (boîtier séparé qui pilote la cellule) : registre à 0 en
        # permanence, confirmé par test.
        "unsupported": {"ibasel_duo"},
    },
    {
        "translation_key": "courant_cellule",
        "unique_id": "courant_cellule",
        "address": 1062,
        "unit": "mA",
        "scale": 1,
        "precision": 0,
        "icon": "mdi:current-dc",
        "entity_category": "diagnostic",
        "min_valid": 0,
        "max_valid": 50000,
        # Confirmée sur Racer (nadlio, issue #4), même registre que tension_cellule (1061).
        "confirmed": {"racer"},
    },
    {
        "translation_key": "puissance_cellule",
        "unique_id": "puissance_cellule",
        "address": 1063,
        "unit": "W",
        "scale": 1,
        "precision": 0,
        "icon": "mdi:flash",
        "device_class": "power",
        "entity_category": "diagnostic",
        "min_valid": 0,
        "max_valid": 5000,
        # Confirmée explicitement par nadlio (issue #4) : "la puissance de la cellule du
        # racer, propre au module racer, valeur juste".
        "confirmed": {"racer"},
    },
    {
        "translation_key": "heures_fonctionnement",
        "unique_id": "heures_fonctionnement",
        "address": 4463,
        "unit": "h",
        "scale": 1,
        "precision": 0,
        "icon": "mdi:timer-outline",
        "entity_category": "diagnostic",
        "min_valid": 0,
        "max_valid": 100000,
        "confirmed": CELL_DIAGNOSTICS_CONFIRMED,
        "unsupported": CELL_DIAGNOSTICS_UNSUPPORTED,
    },
]

# Réglages modifiables (number.py), gérés avec le même principe confirmed/unsupported
# que les capteurs ci-dessus (via entity_status()).
ELECTROLYSIS_SETPOINT = {
    # Confirmée sur Poolsquad UV (Pierre_Brdn) et Racer (nadlio, issue #4).
    "confirmed": {"poolsquad_uv", "racer"},
    # Confirmée NON fonctionnelle sur Ibiza iBasel Duo par test direct : le registre reste
    # figé quelle que soit la valeur écrite ou la consommation réelle de l'électrolyseur
    # (l'iBaRegul Duo ne communique pas avec l'iBaSel qui pilote réellement la cellule).
    "unsupported": {"ibasel_duo"},
}

# Confirmée sur Just Salt Pro (Locodice67, PR #5).
POOL_SIZE_SETPOINT = {
    "confirmed": {"just_salt_pro"},
}

CELL_INVERSION_HOURS = {
    "confirmed": CELL_DIAGNOSTICS_CONFIRMED,
    "unsupported": CELL_DIAGNOSTICS_UNSUPPORTED,
}


def entity_status(conf, model_key):
    """Retourne (créer, activée_par_défaut) pour une entité donnée sur un modèle."""
    if model_key in conf.get("unsupported", ()):
        return False, False
    return True, model_key in conf.get("confirmed", ())
