# Pool Technologie – Intégration Home Assistant

Intégration personnalisée Home Assistant pour les électrolyseurs de la marque Pool Technologie via Modbus TCP.

## Fonctionnalités

Cette intégration permet de suivre et contrôler facilement les principaux paramètres de votre piscine :

- Température de l'eau
- pH
- Taux de sel
- ORP *(optionnel, si une sonde ORP est installée)*
- Taille du bassin
- Consignes pH et ORP (lecture et écriture)
- Mode boost (activation/désactivation)
- Régulation pH automatique (activation/désactivation)
- État de la communication Modbus (avec reprise automatique après une déconnexion)

## Configuration

Lors de l'ajout de l'intégration, vous renseignez :

- L'adresse IP et le port de votre convertisseur Modbus TCP/IP
- L'adresse Modbus de l'électrolyseur
- Le modèle de votre électrolyseur (voir la liste ci-dessous)
- La présence ou non d'une sonde ORP (masque les entités ORP si absente)
- L'intervalle de rafraîchissement des données (en secondes)

Ces deux derniers réglages restent modifiables après coup, sans réinstaller l'intégration, via **Paramètres** > **Appareils & services** > **Pool Technologie** > **Configurer**.

## Matériel nécessaire

Un convertisseur RS485 ↔ TCP/IP est indispensable pour connecter l'électrolyseur à votre réseau.

Exemple : [Waveshare Industrial Serial Server RS485 to RJ45 Ethernet TCP/IP to Serial Rail-Mount](https://amzn.to/3HeBeuT)

## Compatibilité

Testé et validé par des utilisateurs avec les modèles d'électrolyseurs suivants :

- [X] Ibiza iBasel Duo
- [X] WaterAir Salt Gold Duo
- [X] Poolsquad UV

Il est toutefois fort probable que cela fonctionne également avec d'autres modèles Pool Technologie, le mapping Modbus étant identique d'un modèle à l'autre.

## Installation

- [Télécharger la dernière version](../../releases/latest)
- Décompressez l'archive .zip
- Renommez le dossier extrait en **pool_technologie** s'il ne l'est pas déjà
- Copiez le dossier **pool_technologie** dans **config/custom_components/**
- Redémarrez Home Assistant
- Ajoutez l'intégration via **Paramètres** > **Appareils & services** > **Ajouter une intégration**
- Recherchez **Pool Technologie**
- Suivez les indications de configuration

## Aperçu

<img width="789" height="855" alt="aperçu" src="https://github.com/user-attachments/assets/ebfe917e-f240-41bb-8b7a-fd5d1d67eb45" />
