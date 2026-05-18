# Pool Technologie – Intégration Home Assistant

Intégration personnalisée Home Assistant pour les électrolyseurs de la marque Pool Technologie (testé et validé avec l’Ibiza iBasel Duo) via Modbus TCP.

## Fonctionnalité

Cette intégration permet de suivre et contrôler facilement les principaux paramètres de votre piscine

- Température de l’eau 
- pH
- Taux de sel
- ORP
- Taille du bassin
- Consignes pH et ORP (lecture et écriture)
- État de la communication Modbus

## Matériel nécessaire

Un convertisseur RS485 ↔ TCP/IP est indispensable pour connecter l’électrolyseur à votre réseau.

Exemple : [Waveshare Industrial Serial Server RS485 to RJ45 Ethernet TCP/IP to Serial Rail-Mount](https://amzn.to/3HeBeuT)

## Compatibilité

Testé avec les modèles d'électrolyseurs suivants : 

- [X]  Ibiza iBasel Duo
- [X]  WaterAir Salt Gold Duo

Il est toutefois fort probable que cela fonctionne également avec d'autres modèles Pool Technologie. 

## Installation

- [Télécharger la dernière version](../../releases/latest)
- Décompressez l’archive .zip.
- Renommez le dossier extrait en **pool_technologie** s'il ne l'est déjà pas
- Copiez le dossier **pool_technologie** dans **config/custom_components/**
- Redémarrer Home Assistant
- Ajouter l'intégration via **Paramètres** > **Appareils & services** > **Ajouter une intégration**.
- Recherchez **Pool Technologie**.
- Suivre les indications de configuration.

## Aperçu

<img width="789" height="855" alt="aperçu" src="https://github.com/user-attachments/assets/ebfe917e-f240-41bb-8b7a-fd5d1d67eb45" />
