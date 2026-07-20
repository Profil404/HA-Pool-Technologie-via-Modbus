
MODELS = {
    "ibasel_duo": {
        "name": "Ibiza iBasel Duo",
        "sensors": [
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
    }
}

