# Pool Technologie – Intégration Home Assistant

[![HACS Default](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)
[![Release](https://img.shields.io/github/v/release/Profil404/HA-Pool-Technologie-via-Modbus)](../../releases/latest)

[![Ouvrir dans HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Profil404&repository=HA-Pool-Technologie-via-Modbus&category=integration)

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
| Ratio électrolyse | Capteur (diagnostic) | 2051 | % | Part de fonctionnement de l'électrolyse — non disponible sur tous les modèles, voir [Compatibilité par modèle](#compatibilité-par-modèle) |
| Ratio UV | Capteur (diagnostic) | 2050 | % | Part de fonctionnement du traitement UV — non disponible sur tous les modèles, voir [Compatibilité par modèle](#compatibilité-par-modèle) |
| Heures de fonctionnement | Capteur (diagnostic) | 4463 | h | Heures de fonctionnement cumulées de la cellule — non disponible sur tous les modèles, voir [Compatibilité par modèle](#compatibilité-par-modèle) |
| Consigne pH | Réglage éditable | 4207 | pH | Valeur cible de régulation du pH |
| Concentration correcteur pH | Réglage éditable | 4208 | % | Concentration du produit correcteur de pH utilisé pour le dosage |
| Consigne ORP | Réglage éditable | 4235 | mV | Valeur cible de régulation de l'ORP |
| Consigne électrolyse | Réglage éditable | 4168 | % | Niveau de production de l'électrolyse en régulation manuelle |
| Réglage taille du bassin | Réglage éditable | 4111 | m³ | Modifie le volume du bassin configuré sur l'appareil |
| Heure inversion cellule | Réglage éditable | 4170 | h | Fréquence d'inversion de polarité de la cellule |
| Mode boost | Interrupteur | 4188 / 4182 | — | Active la production maximale pendant 24h |
| Régulation pH automatique | Interrupteur | 4200 | — | Active/désactive la régulation pH automatique |
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
| Courant cellule | ❓ | ❓ | ✅ | ❓ | ✅ |
| Puissance cellule | ❓ | ❓ | ✅ | ❓ | ✅ |
| Ratio électrolyse | ❓ | ❓ | ✅ | ❓ | ❓ |
| Ratio UV | ❓ | ❓ | ✅ | ❓ | ❓ |
| Heures de fonctionnement | ❌ | ❓ | ✅ | ✅ | ❓ |
| État de la communication Modbus | ✅ | ✅ | ✅ | ✅ | ✅ |

**Entités en écriture**

| Entité | Ibiza iBasel Duo | WaterAir Salt Gold Duo | Poolsquad UV | Just Salt Pro | Racer |
|---|---|---|---|---|---|
| Consigne pH² | ✅ | ✅ | ✅ | ✅ | ✅ |
| Concentration correcteur pH² | ✅ | ✅ | ✅ | ✅ | ✅ |
| Consigne ORP¹ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Consigne électrolyse | ❌ | ❓ | ✅ | ❓ | ✅ |
| Réglage taille du bassin | ❓ | ❓ | ✅ | ✅ | ❓ |
| Heure inversion cellule | ❌ | ❓ | ✅ | ✅ | ❓ |
| Mode boost | ✅ | ✅ | ✅ | ✅ | ✅ |
| Régulation pH automatique² | ✅ | ✅ | ✅ | ✅ | ✅ |

✅ Confirmé fonctionnel, entité créée et activée &nbsp;&nbsp;❓ Non testé sur ce modèle, entité créée mais **désactivée par défaut** (activable en un clic depuis la page de l'appareil, aucune lecture/écriture Modbus tant qu'elle reste désactivée) &nbsp;&nbsp;❌ Confirmé non fonctionnel sur ce modèle, entité non créée

¹ Créée uniquement si une sonde ORP est déclarée dans la configuration.

² Créée uniquement si une sonde pH est déclarée dans la configuration.

### Vous avez un autre modèle, ou pouvez confirmer/infirmer une ligne ❓ ?

Cette intégration s'améliore grâce aux retours de la communauté. Si vous pouvez tester une entité marquée ❓ sur votre modèle (Tension cellule, Courant cellule, Puissance cellule, Heures de fonctionnement, Consigne électrolyse, Réglage taille du bassin, Heure inversion cellule), ou si vous avez découvert un registre Modbus qui n'est pas encore documenté ici, [ouvrez une issue avec le template dédié](../../issues/new?template=contribution.yml) — même un simple "ça marche chez moi aussi" sur un modèle non confirmé est utile.

## Configuration

Lors de l'ajout de l'intégration, vous renseignez :

- L'adresse IP et le port de votre convertisseur Modbus TCP/IP
- L'adresse Modbus de l'électrolyseur : reprenez le réglage « AD » de l'électrolyseur (certains appareils sont réglés sur 10 et non sur 1)
- Le modèle de votre électrolyseur (voir la liste ci-dessous)
- La présence ou non d'une sonde pH (masque les entités pH si absente)
- La présence ou non d'une sonde ORP (masque les entités ORP si absente)
- L'intervalle de rafraîchissement des données (en secondes)

L'assistant vérifie que l'électrolyseur répond avant de créer l'entrée : il doit donc être sous tension (pompe en marche) au moment de l'ajout.

La présence des sondes et l'intervalle restent modifiables après coup, sans réinstaller l'intégration, via **Paramètres** > **Appareils & services** > **Pool Technologie** > **Configurer**.

### Connexion Modbus

L'intégration n'ouvre pas sa propre connexion : elle passe par l'intégration Modbus de Home Assistant, qui la partage avec les autres intégrations joignant la même passerelle par ce biais. Après une coupure de l'électrolyseur ou de la passerelle, la liaison est rouverte d'elle-même au cycle suivant, sans recharger l'intégration. Pendant une coupure, les entités gardent leur dernière valeur, et « État de la communication Modbus » passe à off après 3 cycles ratés d'affilée.

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

Prérequis : **Home Assistant 2026.10.1** ou plus récent.

### Via HACS (recommandé)

L'intégration est disponible dans le store officiel HACS, aucun dépôt personnalisé n'est nécessaire.

[![Ouvrir dans HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Profil404&repository=HA-Pool-Technologie-via-Modbus&category=integration)

1. Dans Home Assistant, ouvrez **HACS** (ou cliquez sur le bouton ci-dessus)
2. Recherchez **Pool Technologie** et cliquez sur **Télécharger**
3. Redémarrez Home Assistant
4. Ajoutez l'intégration via **Paramètres** > **Appareils & services** > **Ajouter une intégration**, recherchez **Pool Technologie** — ou directement : [![Ajouter l'intégration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=pool_technologie)
5. Suivez les indications de configuration

> Vous l'aviez installée en dépôt personnalisé avant son arrivée dans le store ? Rien à faire, les mises à jour continuent d'arriver normalement. Vous pouvez retirer l'entrée de **HACS** > **⋮** > **Dépôts personnalisés** si vous le souhaitez.

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
- [pierrebaridon63](https://github.com/pierrebaridon63) — consigne électrolyse, courant/puissance cellule, réglage taille du bassin et ratios électrolyse/UV sur Poolsquad UV ([issue #8](../../issues/8), [issue #9](../../issues/9))
- [nadlio](https://github.com/nadlio) — modèle Racer, tension/consigne électrolyse sur ce modèle ([issue #4](../../issues/4))
- [Locodice67](https://github.com/Locodice67) — concentration correcteur pH, réglage taille du bassin, diagnostics cellule (heures de fonctionnement, heure d'inversion)
- les contributeurs du fil du forum HACF (Phil, Cyril44, jimbo7384 et d'autres) pour la découverte et la confirmation de nombreux registres et modèles compatibles
