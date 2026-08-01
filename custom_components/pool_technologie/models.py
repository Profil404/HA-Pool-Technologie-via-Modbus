
# Aucune différence de mapping Modbus signalée entre ces appareils sur le forum HACF
# (https://forum.hacf.fr/t/electrolyseur-pool-technologie-via-le-port-rs485-justsalt-ibaregul-duo/) :
# même liste de registres pour les trois modèles, seul le nom affiché change.
_COMMON_SENSORS = [
    {
        "name": "Taille du bassin",
        "translation_key": "taille_bassin",
        "unique_id": "taille_bassin",
        "address": 4111,
        "unit": "m³",
        "scale": 1,
        "precision": 0,
        "icon": "mdi:texture-box"
    },
    {
        "name": "pH",
        "translation_key": "ph",
        "unique_id": "ph",
        "address": 259,
        "unit": "pH",
        "scale": 0.001,
        "precision": 1,
        "icon": "mdi:test-tube",
        "min_valid": 0,
        "max_valid": 14
    },
    {
        "name": "Température de l'eau",
        "translation_key": "temperature_eau",
        "unique_id": "temperature_eau",
        "address": 260,
        "unit": "°C",
        "scale": 0.1,
        "precision": 1,
        "icon": "mdi:thermometer-water",
        "device_class": "temperature",
        "min_valid": -10,
        "max_valid": 60
    },
    {
        "name": "Taux de sel",
        "translation_key": "taux_sel",
        "unique_id": "taux_sel",
        "address": 261,
        "unit": "g/L",
        "scale": 0.1,
        "precision": 1,
        "icon": "mdi:shaker-outline",
        "min_valid": 0,
        "max_valid": 20
    },
    {
        "name": "ORP",
        "translation_key": "orp",
        "unique_id": "orp",
        "address": 262,
        "unit": "mV",
        "scale": 1,
        "precision": 0,
        "icon": "mdi:lightning-bolt",
        "min_valid": 0,
        "max_valid": 1200
    },
    {
        "name": "Consigne pH",
        "translation_key": "consigne_ph",
        "unique_id": "consigne_ph",
        "address": 4207,
        "unit": "pH",
        "scale": 0.000390625,
        "precision": 1,
        "icon": "mdi:cog",
        "min_valid": 0,
        "max_valid": 14
    },
    {
        "name": "Consigne ORP",
        "translation_key": "consigne_orp",
        "unique_id": "consigne_orp",
        "address": 4235,
        "unit": "mV",
        "scale": 1,
        "precision": 0,
        "icon": "mdi:cog",
        "min_valid": 0,
        "max_valid": 1200
    }
]

# Non disponible sur l'Ibiza iBasel Duo : l'iBaRegul Duo (boîtier de régulation, expose le
# Modbus) ne communique pas cette donnée depuis l'iBaSel (boîtier séparé qui pilote la
# cellule) — le registre y lit 0 en permanence, confirmé par test. Inclus pour les autres
# modèles où la régulation et le pilotage de cellule sont dans le même boîtier, non testé.
_TENSION_CELLULE = {
    "name": "Tension cellule",
    "translation_key": "tension_cellule",
    "unique_id": "tension_cellule",
    "address": 1061,
    "unit": "mV",
    "scale": 1,
    "precision": 0,
    "icon": "mdi:sine-wave",
    "entity_category": "diagnostic",
    "min_valid": 0,
    "max_valid": 30000
}

MODELS = {
    "ibasel_duo": {
        "name": "Ibiza iBasel Duo",
        "sensors": _COMMON_SENSORS
    },
    "waterair_salt_gold_duo": {
        "name": "WaterAir Salt Gold Duo",
        "sensors": _COMMON_SENSORS + [_TENSION_CELLULE]
    },
    "poolsquad_uv": {
        "name": "Poolsquad UV",
        "sensors": _COMMON_SENSORS + [_TENSION_CELLULE],
        # Consigne électrolyse (registre 4168) confirmée fonctionnelle sur ce modèle par un
        # utilisateur HACS (Pierre_Brdn) sans sonde ORP. Non confirmée sur les autres modèles.
        "supports_electrolysis_setpoint": True
    },
    "just_salt_pro": {
        "name": "Just Salt Pro",
        "sensors": _COMMON_SENSORS + [_TENSION_CELLULE]
    }
}
