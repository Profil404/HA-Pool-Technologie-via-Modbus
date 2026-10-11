# Pool Technologie – Intégration Home Assistant

Intégration personnalisée Home Assistant pour les électrolyseurs de la marque Pool Technologie via Modbus TCP.

## Fonctionnalités

Cette intégration permet de suivre et contrôler facilement les principaux paramètres de votre piscine :

| Entité | Type | Registre Modbus | Unité | Description |
|---|---|---|---|---|
| pH | Capteur | 259 | pH | Mesure du pH de l'eau |
| Température de l'eau | Capteur | 260 | °C | Mesure de la température de l'eau |
| Taux de sel | Capteur | 261 | g/L | Mesure du taux de sel |
| ORP | Capteur | 262 | mV | Mesure de l'ORP |
| Taille du bassin | Capteur | 4111 | m³ | Volume du bassin configuré sur l'appareil |
| Tension cellule | Capteur (diagnostic) | 1061 | mV | Tension aux bornes de la cellule d'électrolyse — non disponible sur tous les modèles, voir [Compatibilité par modèle](#compatibilité-par-modèle) |
| Courant cellule | Capteur (diagnostic) | 1062 | mA | Courant traversant la cellule d'électrolyse — non disponible sur tous les modèles, voir [Compatibilité par modèle](#compatibilité-par-modèle) |
| Puissance cellule | Capteur (diagnostic) | 1063 | W | Puissance consommée par la cellule d'électrolyse — non disponible sur tous les modèles, voir [Compatibilité par modèle](#compatibilité-par-modèle) |
| Heures de fonctionnement | Capteur (diagnostic) | 4463 | h | Heures de fonctionnement cumulées de la cellule — non disponible sur tous les modèles, voir [Compatibilité par modèle](#compatibilité-par-modèle) |
| Consigne pH | Réglage éditable | 4207 | pH | Valeur cible de régulation du pH |
| Concentration correcteur pH | Réglage éditable | 4208 | % | Concentration du produit correcteur de pH utilisé pour le dosage |
| Consigne ORP | Réglage éditable | 4235 | mV | Valeur cible de régulation de l'ORP |
| Consigne électrolyse | Réglage éditable | 4168 | % | Niveau de production de l'électrolyse en régulation manuelle |
| Réglage taille du bassin | Réglage éditable | 4111 | m³ | Modifie le volume du bassin configuré sur l'appareil |
| Heure inversion cellule | Réglage éditable | 4170 | h | Fréquence d'inversion de polarité de la cellule |
| Mode boost | Interrupteur | 4188 / 4182 | — | Active la production maximale pendant 24h |
| Régulation pH automatique | Interrupteur | 4200 | — | Active/désactive la régulation pH automatique |
| Alarmes cellule | Capteur binaire (diagnostic) | 4172 (bitmask) | — | Défaut cellule, manque de sel, trop de sel, sécurité eau froide — non disponibles sur tous les modèles, voir [Compatibilité par modèle](#compatibilité-par-modèle) |
| État de la communication Modbus | Diagnostic | — | — | Reflète l'état de la connexion, avec reprise automatique après une déconnexion |

### Compatibilité par modèle

**Entités en lecture**

| Entité | Ibiza iBasel Duo | WaterAir Salt Gold Duo | Poolsquad UV | Just Salt Pro | Racer |
|---|---|---|---|---|---|
| pH² | ✅ | ✅ | ✅ | ✅ | ✅ |
| Température de l'eau | ✅ | ✅ | ✅ | ✅ | ✅ |
| Taux de sel | ✅ | ✅ | ✅ | ✅ | ✅ |
| ORP¹ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Taille du bassin | ✅ | ✅ | ✅ | ✅ | ✅ |
| Consigne pH² | ✅ | ✅ | ✅ | ✅ | ✅ |
| Consigne ORP¹ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Tension cellule | ❌ | ❓ | ✅ | ❓ | ✅ |
| Courant cellule | ❓ | ❓ | ❓ | ❓ | ✅ |
| Puissance cellule | ❓ | ❓ | ❓ | ❓ | ✅ |
| Heures de fonctionnement | ❌ | ❓ | ✅ | ✅ | ❓ |
| Alarmes cellule | ❌ | ❓ | ✅ | ✅ | ❓ |
| État de la communication Modbus | ✅ | ✅ | ✅ | ✅ | ✅ |

**Entités en écriture**

| Entité | Ibiza iBasel Duo | WaterAir Salt Gold Duo | Poolsquad UV | Just Salt Pro | Racer |
|---|---|---|---|---|---|
| Consigne pH² | ✅ | ✅ | ✅ | ✅ | ✅ |
| Concentration correcteur pH² | ✅ | ✅ | ✅ | ✅ | ✅ |
| Consigne ORP¹ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Consigne électrolyse | ❌ | ❓ | ✅ | ❓ | ✅ |
| Réglage taille du bassin | ❓ | ❓ | ❓ | ✅ | ❓ |
| Heure inversion cellule | ❌ | ❓ | ✅ | ✅ | ❓ |
| Mode boost | ✅ | ✅ | ✅ | ✅ | ✅ |
| Régulation pH automatique² | ✅ | ✅ | ✅ | ✅ | ✅ |

✅ Confirmé fonctionnel, entité créée et activée &nbsp;&nbsp;❓ Non testé sur ce modèle, entité créée mais **désactivée par défaut** (activable en un clic depuis la page de l'appareil, aucune lecture/écriture Modbus tant qu'elle reste désactivée) &nbsp;&nbsp;❌ Confirmé non fonctionnel sur ce modèle, entité non créée

¹ Créée uniquement si une sonde ORP est déclarée dans la configuration.

² Créée uniquement si une sonde pH est déclarée dans la configuration.

### Vous avez un autre modèle, ou pouvez confirmer/infirmer une ligne ❓ ?

Cette intégration s'améliore grâce aux retours de la communauté. Si vous pouvez tester une entité marquée ❓ sur votre modèle (Tension cellule, Courant cellule, Puissance cellule, Heures de fonctionnement, Alarmes cellule, Consigne électrolyse, Réglage taille du bassin, Heure inversion cellule), ou si vous avez découvert un registre Modbus qui n'est pas encore documenté ici, [ouvrez une issue avec le template dédié](../../issues/new?template=contribution.yml) — même un simple "ça marche chez moi aussi" sur un modèle non confirmé est utile.

## Configuration

Lors de l'ajout de l'intégration, vous renseignez :

- L'adresse IP et le port de votre convertisseur Modbus TCP/IP
- L'adresse Modbus de l'électrolyseur
- Le modèle de votre électrolyseur (voir la liste ci-dessous)
- La présence ou non d'une sonde pH (masque les entités pH si absente)
- La présence ou non d'une sonde ORP (masque les entités ORP si absente)
- L'intervalle de rafraîchissement des données (en secondes)

La présence des sondes et l'intervalle restent modifiables après coup, sans réinstaller l'intégration, via **Paramètres** > **Appareils & services** > **Pool Technologie** > **Configurer**.

## Matériel nécessaire

Un convertisseur RS485 ↔ TCP/IP est indispensable pour connecter l'électrolyseur à votre réseau.

Exemple : [Waveshare Industrial Serial Server RS485 to RJ45 Ethernet TCP/IP to Serial Rail-Mount](https://amzn.to/3HeBeuT)

## Compatibilité

Testé et validé par des utilisateurs avec les modèles d'électrolyseurs suivants :

- [X] Ibiza iBasel Duo
- [X] WaterAir Salt Gold Duo
- [X] Poolsquad UV
- [X] Just Salt Pro
- [X] Racer (sans pH)

Il est toutefois fort probable que cela fonctionne également avec d'autres modèles Pool Technologie, le mapping Modbus étant identique d'un modèle à l'autre.

## Installation

### Via HACS (recommandé)

Une demande d'ajout au store officiel HACS est en cours de revue. En attendant, l'intégration s'installe dès maintenant en dépôt personnalisé :

1. Dans Home Assistant, ouvrez **HACS**
2. Cliquez sur les **⋮** (en haut à droite) > **Dépôts personnalisés**
3. Ajoutez l'URL de ce dépôt : `https://github.com/Profil404/HA-Pool-Technologie-via-Modbus`, catégorie **Intégration**
4. Recherchez **Pool Technologie** dans HACS et installez-la
5. Redémarrez Home Assistant
6. Ajoutez l'intégration via **Paramètres** > **Appareils & services** > **Ajouter une intégration**, recherchez **Pool Technologie**
7. Suivez les indications de configuration

### Manuellement

- [Télécharger la dernière version](../../releases/latest)
- Décompressez l'archive .zip
- Renommez le dossier extrait en **pool_technologie** s'il ne l'est pas déjà
- Copiez le dossier **pool_technologie** dans **config/custom_components/**
- Redémarrez Home Assistant
- Ajoutez l'intégration via **Paramètres** > **Appareils & services** > **Ajouter une intégration**
- Recherchez **Pool Technologie**
- Suivez les indications de configuration

## Aperçu

<img width="991" height="1093" alt="Aperçu de l'intégration Pool Technologie pour Home Assistant" src="https://github.com/user-attachments/assets/975f4e69-a7a8-40d3-a38b-c3d36238ce96" />

## Langues disponibles

🇫🇷 Français · 🇬🇧 English · 🇪🇸 Español 

L'interface s'affiche automatiquement dans la langue configurée sur votre instance Home Assistant, avec repli sur l'anglais sinon. Vous parlez une autre langue ? [Ouvrez une issue](../../issues/new) ou une pull request avec un fichier `translations/<code langue>.json` supplémentaire.

## Crédits

Ce projet est né d'un travail de rétro-ingénierie du protocole Modbus de l'électrolyseur Pool Technologie, mené et documenté par [Profil404](https://github.com/Profil404) sur le [forum HACF](https://forum.hacf.fr/t/electrolyseur-pool-technologie-via-le-port-rs485-justsalt-ibaregul-duo/), avant de donner lieu à cette intégration Home Assistant.

Plusieurs registres et fonctionnalités supplémentaires ont ensuite été identifiés et repris depuis d'autres forks et contributions de la communauté, notamment :

- [neopsyko](https://github.com/neopsyko/HA-Pool-Technologie-via-Modbus) — mode boost, synchronisation continue des consignes
- [romain563](https://github.com/romain563/pooltechnologie) — option de configuration ORP
- Pierre Brdn — consigne électrolyse (Poolsquad UV)
- [nadlio](https://github.com/nadlio) — modèle Racer, tension/consigne électrolyse sur ce modèle ([issue #4](../../issues/4))
- [Locodice67](https://github.com/Locodice67) — concentration correcteur pH, réglage taille du bassin, diagnostics cellule (heures de fonctionnement, alarmes, heure d'inversion)
- les contributeurs du fil du forum HACF (Phil, Cyril44, jimbo7384 et d'autres) pour la découverte et la confirmation de nombreux registres et modèles compatibles
