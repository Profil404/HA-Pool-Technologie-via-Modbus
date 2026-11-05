# pool_technologie_modbus

Petite bibliothèque Python pour lire et piloter les électrolyseurs Pool Technologie (Ibiza iBasel Duo, WaterAir Salt Gold Duo, Poolsquad UV, Just Salt Pro, Racer) par leur port RS485, à travers une passerelle Modbus TCP.

Elle est construite sur [modbus-connection](https://pypi.org/project/modbus-connection/) et intégrée (vendorisée) à l'intégration `pool_technologie`. Elle n'importe rien de l'intégration et peut en être extraite telle quelle.

## Principe

La bibliothèque reçoit un `ModbusUnit` et **n'ouvre ni ne ferme jamais de connexion** : la connexion appartient à l'appelant.

Exemple, la bibliothèque extraite du dépôt :

```python
from modbus_connection.tmodbus import ModbusConnection
from modbus_connection import ModbusTcpParams

from pool_technologie_modbus import PoolTechnologieDevice

connection = ModbusConnection(ModbusTcpParams(host="192.168.1.50", port=502))
device = PoolTechnologieDevice(connection.for_unit(1))

device.select(["ph", "water_temperature", "salt"])
report = await device.async_update()
print(device.values)  # {"ph": 7.2, "water_temperature": 24.5, "salt": 4.1}

await device.async_write("ph_setpoint", 7.3)  # écrit, puis relit pour confirmer
await device.async_set_boost(True)

await connection.close()
```

- `select(names)` choisit les champs lus par `async_update()`. Un champ non choisi ne coûte aucune requête.
- `async_update()` retourne un `UpdateReport` de modbus-connection : chaque adresse lue y est un sous-système `address_<n>`, dans `updated` ou dans `failed`. Si la liaison tombe ou que l'appareil ne répond plus (`ModbusConnectionError`, `ModbusTimeoutError`), le cycle s'arrête à la première adresse concernée et l'erreur est levée : un appareil éteint en cours de cycle ne fait pas attendre son délai à chaque adresse restante. Les valeurs déjà lues restent acquises.
- `values` donne la dernière valeur de chaque champ choisi. Une lecture hors plage se lit `None` ; une lecture en échec garde la valeur précédente.
- `async_validate()` lit une fois la température de l'eau, pour vérifier que l'appareil répond.
- Une seule méthode de mise à jour : tout est lu au même intervalle.

## Composants

| Composant | Champ | Adresse | Unité | Plage valide | Écriture |
|---|---|---:|---|---|---|
| `Measurements` | `ph` | 259 | pH (×0,001, 1 déc.) | 0 – 14 | |
| | `water_temperature` | 260 | °C (×0,1, 1 déc.) | −10 – 60 | |
| | `salt` | 261 | g/L (×0,1, 1 déc.) | 0 – 20 | |
| | `orp` | 262 | mV | 0 – 1200 | |
| `ReportedSetpoints` | `reported_pool_volume` | 4111 | m³ | — | |
| | `reported_ph_setpoint` | 4207 | pH (÷2560, 1 déc.) | 0 – 14 | |
| | `reported_orp_setpoint` | 4235 | mV | 0 – 1200 | |
| `Setpoints` | `ph_setpoint` | 4207 | pH (÷2560, 2 déc.) | 6,0 – 8,5 | oui, relecture à ±1 |
| | `orp_setpoint` | 4235 | mV | 400 – 900 | oui (tronqué) |
| | `electrolysis_setpoint` | 4168 | % | 10 – 100 | oui (tronqué) |
| | `ph_corrector_concentration` | 4208 | % | 5 – 50 | oui |
| | `pool_volume` | 4111 | m³ | 1 – 250 | oui |
| `Controls` | `boost_remaining` | 4188 | min | — | oui |
| | `boost_flag` | 4182 | — | — | oui, jamais lu |
| | `ph_regulation` | 4200 | — | — | oui |
| `Cell` | `cell_voltage` | 1061 | mV | 0 – 30000 | |
| | `cell_current` | 1062 | mA | 0 – 50000 | |
| | `cell_power` | 1063 | W | 0 – 5000 | |
| | `uv_ratio` | 2050 | % (×0,125) | 0 – 100 | |
| | `electrolysis_ratio` | 2051 | % (×0,125) | 0 – 100 | |
| | `operating_hours` | 4463 | h | 0 – 100000 | |
| | `cell_inversion_interval` | 4170 | h | 1 – 24 | oui |

Tous les registres sont des holding registers 16 bits **non signés** (FC03 en lecture, FC06 en écriture). Une valeur décodée vaut `round(brut × échelle, décimales)`, et sort en `None` hors de sa plage valide.

`ReportedSetpoints` et `Setpoints` décrivent les mêmes registres sous deux angles : la valeur rapportée avec ses bornes physiques, et le réglage avec ses bornes de réglage. Choisis ensemble, ils ne coûtent qu'une requête par adresse.

Le mode boost s'active en écrivant la durée (1440 min) puis le drapeau (256), et s'arrête en remettant la durée à 0 : le drapeau retombe alors à 0 de lui-même (observé sur un Just Salt Pro). Seule la durée est relue.

## Statut par modèle

`support(model, field)` retourne `Support.CONFIRMED`, `Support.UNTESTED` ou `Support.UNSUPPORTED` pour chaque champ, d'après les retours de la communauté (issues et fil HACF). La table vit dans `support.py`.

## Découpage des lectures

Chaque adresse est lue **par sa propre requête d'un seul registre**, dans cet ordre : 4111, 259, 260, 261, 262, 4207, 4235, 1061, 1062, 1063, 2051, 2050, 4463, 4168, 4208, 4170, 4188, 4200. C'est exactement le découpage historique de l'intégration.

Les registres utiles sont séparés par des adresses que l'appareil n'implémente pas, et une lecture groupée qui traverse l'une d'elles peut échouer ou rendre des valeurs fausses. Chaque composant déclare donc une plage lisible d'un seul registre par champ (`register_ranges`) : même un composant lu d'un bloc ne fusionne jamais deux adresses. `POLL_ORDER` fixe l'ordre.

### Regroupements à valider sur matériel

Ces regroupements réduiraient le nombre de requêtes par cycle (18 aujourd'hui avec tous les champs). Aucun n'a été essayé : chacun demande une validation sur un appareil réel, sur chaque modèle, avant d'élargir la plage déclarée.

| Regroupement | Requêtes | Ce qu'il faut vérifier |
|---|---|---|
| 259 – 262 (mesures) | 4 → 1 | adresses contiguës : bloc de 4 accepté par l'électrolyseur et la passerelle |
| 1061 – 1063 (cellule) | 3 → 1 | idem ; et sur l'iBasel Duo, où 1061 reste à 0 |
| 2050 – 2051 (ratios) | 2 → 1 | idem |
| 4207 – 4208 (consigne pH, concentration) | 2 → 1 | idem |
| 4168 – 4170 (consigne électrolyse, inversion) | 2 → 1 | traverse 4169, non documenté |
| 4182 – 4200 (boost, régulation pH) | 2 → 1 | traverse 4183 – 4187 et 4189 – 4199, non documentés |

Un relevé fait sur un seul Just Salt Pro ([fork de neopsyko](https://github.com/neopsyko/HA-Pool-Technologie-via-Modbus), `CLAUDE.md`) donne deux indices :

- seule la fonction FC03 est acceptée, FC01, FC02 et FC04 répondent « fonction illégale » ;
- les plages 0 – 49, 259 – 268, 512 – 527 et 4096 – 4270 répondent, ce qui rend plausibles les regroupements 259 – 262, 4168 – 4170, 4182 – 4200 et 4207 – 4208.

Ce relevé est incomplet : 1061 – 1063, 2050 – 2051 et 4463, confirmés sur d'autres modèles, n'y figurent pas. Il ne dispense donc pas des essais.

## Exceptions

Toutes les exceptions levées viennent de modbus-connection (`ModbusError` et ses sous-classes : `ModbusConnectionError`, `ModbusTimeoutError`, `ModbusExceptionError`…) ou de la bibliothèque, qui en dérivent :

- `PoolTechnologieError(ModbusError)` : base des erreurs de la bibliothèque ;
- `WriteNotConfirmedError(PoolTechnologieError)` : l'écriture a été acceptée, mais la relecture ne la confirme pas (`field`, `address`, `expected`, `read`).

Des erreurs de programmation restent possibles : `KeyError` pour un champ inconnu, `AttributeError` pour une écriture sur un champ en lecture seule, `ValueError` pour une valeur hors de 0 – 65535 une fois convertie.

## Tests

Les tests vivent dans `tests/pool_technologie_modbus/` à la racine du dépôt. Ils utilisent l'unité en mémoire du plugin pytest de modbus-connection (`mock_modbus_unit`), sans matériel : décodage de chaque champ sur les 65 536 valeurs brutes, filtrage hors plage, écritures avec relecture, registre manquant et découpage strict des lectures.
