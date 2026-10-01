# Statut de chaque registre par modèle, utilisé pour décider si une entité est
# créée, et si elle est activée par défaut :
#   - modèle dans "confirmed"   -> entité créée et activée
#   - modèle dans "unsupported" -> entité non créée (confirmé non fonctionnel)
#   - sinon (non testé)         -> entité créée mais DÉSACTIVÉE par défaut :
#     l'utilisateur peut l'activer en un clic depuis la page de l'appareil pour
#     essayer, et nous faire un retour. Une entité désactivée ne coûte aucune
#     lecture Modbus.
# Seuls les registres en LECTURE SEULE suivent ce principe. Les réglages
# modifiables (number) restent réservés aux modèles confirmés : pas d'écriture
# à l'aveugle dans l'électrolyseur.
#
# Mapping Modbus identique d'un modèle à l'autre d'après le forum HACF
# (https://forum.hacf.fr/t/electrolyseur-pool-technologie-via-le-port-rs485-justsalt-ibaregul-duo/).

MODELS = {
    "ibasel_duo": {"name": "Ibiza iBasel Duo"},
    "waterair_salt_gold_duo": {"name": "WaterAir Salt Gold Duo"},
    "poolsquad_uv": {
        "name": "Poolsquad UV",
        # Consigne électrolyse (registre 4168) confirmée fonctionnelle sur ce modèle par un
        # utilisateur HACS (Pierre_Brdn) sans sonde ORP. Non confirmée sur les autres modèles.
        "supports_electrolysis_setpoint": True,
    },
    "just_salt_pro": {"name": "Just Salt Pro"},
}

ALL_MODELS = frozenset(MODELS)

# Clés des capteurs qui n'ont de sens qu'avec la sonde correspondante installée
PH_SENSOR_KEYS = {"ph", "consigne_ph"}
ORP_SENSOR_KEYS = {"orp", "consigne_orp"}

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
        "confirmed": {"poolsquad_uv"},
        # L'iBaRegul Duo (boîtier de régulation, expose le Modbus) ne communique pas cette
        # donnée depuis l'iBaSel (boîtier séparé qui pilote la cellule) : registre à 0 en
        # permanence, confirmé par test.
        "unsupported": {"ibasel_duo"},
    },
]


def entity_status(conf, model_key):
    """Retourne (créer, activée_par_défaut) pour une entité donnée sur un modèle."""
    if model_key in conf.get("unsupported", ()):
        return False, False
    return True, model_key in conf.get("confirmed", ())
