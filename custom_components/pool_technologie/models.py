# Statut de chaque entité par modèle, d'après le statut de son champ dans la
# bibliothèque (pool_technologie_modbus/support.py), utilisé pour décider si une
# entité est créée, et si elle est activée par défaut :
#   - champ confirmé sur le modèle     -> entité créée et activée
#   - champ non fonctionnel (unsupported) -> entité non créée
#   - sinon (non testé)                -> entité créée mais DÉSACTIVÉE par défaut :
#     l'utilisateur peut l'activer en un clic depuis la page de l'appareil pour
#     essayer, et nous faire un retour. Une entité désactivée ne coûte aucune
#     lecture Modbus.
# Le même principe s'applique aux réglages modifiables (number) et aux
# interrupteurs (switch).

from .pool_technologie_modbus import MODEL_NAMES, Support, support

MODELS = {model.value: {"name": name} for model, name in MODEL_NAMES.items()}

# Clés des capteurs qui n'ont de sens qu'avec la sonde correspondante installée
PH_SENSOR_KEYS = {"ph", "consigne_ph"}
ORP_SENSOR_KEYS = {"orp", "consigne_orp"}

SENSORS = [
    {
        "translation_key": "taille_bassin",
        "unique_id": "taille_bassin",
        "field": "reported_pool_volume",
        "icon": "mdi:texture-box",
    },
    {
        "translation_key": "ph",
        "unique_id": "ph",
        "field": "ph",
        "icon": "mdi:test-tube",
    },
    {
        "translation_key": "temperature_eau",
        "unique_id": "temperature_eau",
        "field": "water_temperature",
        "icon": "mdi:thermometer-water",
        "device_class": "temperature",
    },
    {
        "translation_key": "taux_sel",
        "unique_id": "taux_sel",
        "field": "salt",
        "icon": "mdi:shaker-outline",
    },
    {
        "translation_key": "orp",
        "unique_id": "orp",
        "field": "orp",
        "icon": "mdi:lightning-bolt",
    },
    {
        "translation_key": "consigne_ph",
        "unique_id": "consigne_ph",
        "field": "reported_ph_setpoint",
        "icon": "mdi:cog",
    },
    {
        "translation_key": "consigne_orp",
        "unique_id": "consigne_orp",
        "field": "reported_orp_setpoint",
        "icon": "mdi:cog",
    },
    {
        "translation_key": "tension_cellule",
        "unique_id": "tension_cellule",
        "field": "cell_voltage",
        "icon": "mdi:sine-wave",
        "entity_category": "diagnostic",
    },
    {
        "translation_key": "courant_cellule",
        "unique_id": "courant_cellule",
        "field": "cell_current",
        "icon": "mdi:current-dc",
        "entity_category": "diagnostic",
    },
    {
        "translation_key": "puissance_cellule",
        "unique_id": "puissance_cellule",
        "field": "cell_power",
        "icon": "mdi:flash",
        "device_class": "power",
        "entity_category": "diagnostic",
    },
    {
        "translation_key": "ratio_electrolyse",
        "unique_id": "ratio_electrolyse",
        "field": "electrolysis_ratio",
        "icon": "mdi:percent",
        "entity_category": "diagnostic",
    },
    {
        "translation_key": "ratio_uv",
        "unique_id": "ratio_uv",
        "field": "uv_ratio",
        "icon": "mdi:percent",
        "entity_category": "diagnostic",
    },
    {
        "translation_key": "heures_fonctionnement",
        "unique_id": "heures_fonctionnement",
        "field": "operating_hours",
        "icon": "mdi:timer-outline",
        "entity_category": "diagnostic",
    },
]


def entity_status(field, model_key):
    """Retourne (créer, activée_par_défaut) pour l'entité d'un champ sur un modèle."""
    status = support(model_key, field)
    if status is Support.UNSUPPORTED:
        return False, False
    return True, status is Support.CONFIRMED
