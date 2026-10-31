pool_technologie – Version à venir (numéro à définir par le mainteneur)
	[Amélioration] Connexion Modbus confiée à l'intégration Modbus de Home Assistant (async_get_unit) : l'intégration n'ouvre plus son propre client pymodbus et ne dépend plus de pymodbus. Plus aucun thread ni verrou : les lectures sont asynchrones et ne peuvent plus saturer Home Assistant quand l'électrolyseur est injoignable (#12). La liaison est partagée avec les autres intégrations qui joignent la même passerelle par Home Assistant, rouverte d'elle-même à la requête suivante après une coupure (#7), et fermée par Home Assistant au déchargement
	[Amélioration] Accès à l'électrolyseur regroupé dans une petite bibliothèque intégrée au dépôt (pool_technologie_modbus), construite sur modbus-connection et testée sans matériel. Mêmes registres, mêmes échelles, mêmes plages valides, même découpage des lectures (un registre par requête), même relecture de confirmation après chaque écriture ; comme en 261029, un seul cycle à la fois, abandonné dès la première lecture sans réponse
	[Amélioration] Un registre lu par deux entités (consigne pH, consigne ORP, taille du bassin) n'est plus lu qu'une fois par cycle
	[Amélioration] Le démarrage de Home Assistant n'attend plus l'électrolyseur : la première lecture se fait en arrière-plan (#12, merci @cedricrosse)
	[Amélioration] L'assistant de configuration vérifie que l'électrolyseur répond avant de créer l'entrée, refuse un électrolyseur déjà configuré (même adresse IP, port et adresse Modbus) et signale une passerelle déjà utilisée par Home Assistant avec d'autres paramètres de liaison (traduit en français, anglais et espagnol)
	[Information] Version minimale de Home Assistant : 2026.10.1. async_get_unit et async_get_temporary_unit existent depuis 2026.9, mais la bibliothèque s'appuie sur la classe Device de modbus-connection (4.12.1, livrée à partir de 2026.10.0), et 2026.10.1 livre modbus-connection 4.12.4, qui rouvre la liaison pour une requête en attente derrière une liaison tombée au lieu de la faire échouer
	[Information] Aucune migration : mêmes entités, mêmes identifiants, mêmes options. Une installation existante se recharge telle quelle. Pendant une coupure, les entités gardent leur dernière valeur et seul « État de la communication Modbus » passe à off, comme en 261029
	[Information] Une version antérieure de ces changements a été testée sur un Poolsquad UV : plus de blocage pompe arrêtée, valeurs rapides au retour, écritures fonctionnelles (#12, merci @cedricrosse). La reprise des comportements de la 261029 (dernières valeurs gardées en coupure, cycle arrêté au premier délai dépassé, première lecture en arrière-plan) reste à confirmer sur matériel

pool_technologie – Version 261029
	[Correctif] Home Assistant se figeait quand l'électrolyseur était injoignable (pompe arrêtée) : les cycles de lecture s'empilaient et saturaient les threads. Un seul cycle tourne désormais à la fois, le cycle est abandonné dès la première lecture en échec de connexion, et l'attente du verrou Modbus est limitée à 10 s (#12, merci @cedricrosse)

pool_technologie – Version 261024
	[Nouveauté] Poolsquad UV confirmé - Ratio électrolyse (2051) (#9, merci @pierrebaridon63)
	[Nouveauté] Poolsquad UV confirmé - Ratio UV (2050) (#9, merci @pierrebaridon63)
	[Amélioration] Poolsquad UV confirmé - Courant cellule (1062) (#8, merci @pierrebaridon63)
	[Amélioration] Poolsquad UV confirmé - Puissance cellule (1063) (#8, merci @pierrebaridon63)
	[Amélioration] Poolsquad UV confirmé - Réglage taille du bassin (4111) (#8, merci @pierrebaridon63)
	[Amélioration] Les entités confirmées sont créées et activées par défaut uniquement sur les nouvelles installations : les entités déjà présentes gardent leur état actuel (activables en un clic depuis la page de l'appareil)
	[Amélioration] 🎉 L'intégration est maintenant disponible dans le store officiel HACS : README mis à jour (badges, installation sans dépôt personnalisé)

pool_technologie – Version 261011
	[Nouveauté] Modèle Racer (sans sonde pH) disponible dans la liste de configuration (#4, merci @nadlio)
	[Nouveauté] Racer confirmé - Courant cellule (1062) (#4, merci @nadlio)
	[Nouveauté] Racer confirmé - Puissance cellule (1063) (#4, merci @nadlio)
	[Nouveauté] Concentration correcteur pH (4208) (#5, merci @Locodice67)
	[Nouveauté] Réglage taille du bassin (4111), confirmé sur Just Salt Pro (#5, merci @Locodice67)
	[Nouveauté] Poolsquad UV et Just Salt Pro confirmés - Heures de fonctionnement (4463) (#6, merci @Locodice67)
	[Nouveauté] Poolsquad UV et Just Salt Pro confirmés - Réglage heure d'inversion cellule (4170) (#6, merci @Locodice67)
	[Amélioration] Racer confirmé - Tension cellule (1061) (#4, merci @nadlio)
	[Amélioration] Racer confirmé - Consigne électrolyse (4168) (#4, merci @nadlio)
	[Amélioration] Les réglages éditables (consigne électrolyse, taille du bassin, heure d'inversion) suivent le même principe que les capteurs : non créés si confirmé non fonctionnel, créés mais désactivés par défaut si non testé, créés et activés si confirmé
	[Amélioration] README : tableau de compatibilité scindé en entités en lecture / entités en écriture, avec 3 notes de bas de page
	[Information] Les 4 alarmes cellule (registre 4172) ne sont pas intégrées pour l'instant : mapping des bits non confirmé (#4)

pool_technologie – Version 261001
	[Correctif] Entités indisponibles après une coupure de connexion de l'électrolyseur ou de la passerelle Modbus TCP (« Connection reset by peer ») : la connexion est maintenant refermée puis rouverte automatiquement, y compris pour les écritures (#7)
	[Nouveauté] Option « Régulation pH (sonde pH installée) », modifiable après coup : sans sonde pH, les entités pH ne sont pas créées, ce qui permet d'utiliser un électrolyseur sans pH comme le Racer (#4)
	[Amélioration] Les entités en lecture seule non confirmées sur un modèle sont créées mais désactivées par défaut (activables en un clic), pour les nouvelles installations uniquement. Concerne pour l'instant Tension cellule sur WaterAir Salt Gold Duo et Just Salt Pro
	[Amélioration] Nouveau format de version basé sur la date de publication (AAMMJJ) au lieu de 1.0.x

pool_technologie – Version 1.0.9
	[Correctif] Structure du dépôt corrigée pour HACS : fichiers de l'intégration déplacés dans custom_components/pool_technologie/ (retour de Frenck, mainteneur HACS)
	[Amélioration] Workflow hassfest.yml simplifié

pool_technologie – Version 1.0.8
	[Nouveauté] Modèle Just Salt Pro disponible
	[Nouveauté] Tension cellule (1061), non créée sur Ibiza iBasel Duo (registre à 0 en permanence sur ce modèle)
	[Nouveauté] Consigne électrolyse (4168), Poolsquad UV uniquement et sans sonde ORP (merci Pierre_Brdn)
	[Nouveauté] Traductions anglaise et espagnole
	[Amélioration] Consignes pH et ORP rafraîchies à chaque cycle : un changement fait depuis l'appli Pool Technologie est répercuté sans redémarrage
	[Amélioration] Détection de déconnexion plus fiable : une lecture isolée en échec n'est plus comptée à tort, et le seuil passe à 3 cycles ratés d'affilée
	[Amélioration] Attribut modbus_address exposé aussi sur les consignes et les interrupteurs
	[Amélioration] Template d'issue GitHub pour signaler un registre ou confirmer une entité, et tableau de compatibilité par modèle dans le README

pool_technologie – Version 1.0.7
	[Amélioration] Dépôt préparé pour HACS : hacs.json, LICENSE, logos, workflows de validation (HACS action + hassfest)
	[Correctif] manifest.json : champ issue_tracker ajouté et clés triées

pool_technologie – Version 1.0.6
	[Nouveauté] Interrupteur Régulation pH automatique
	[Nouveauté] Option sonde ORP, modifiable après coup : sans sonde, les entités ORP ne sont pas créées
	[Nouveauté] Intervalle de rafraîchissement configurable (au lieu de 60 s fixe)
	[Nouveauté] Modèles WaterAir Salt Gold Duo et Poolsquad UV disponibles
	[Nouveauté] Adresse Modbus en attribut de chaque capteur
	[Amélioration] Interrupteurs rafraîchis sur le même cycle que les capteurs, pour rester alignés sur l'intervalle configuré
	[Correctif] Mode boost : lecture Modbus tentée à chaque cycle même électrolyseur déconnecté, provoquant des avertissements de timeout
	[Correctif] Mode boost : sondage de reconnexion en double

pool_technologie – Version 1.0.5
	[Nouveauté] Interrupteur Mode boost
	[Amélioration] Lectures sautées quand l'électrolyseur est déconnecté, avec tentative de reconnexion périodique

pool_technologie – Version 1.0.4
	[Amélioration] Connexion Modbus TCP maintenue ouverte en continu
	[Amélioration] Lectures et écritures Modbus hors de la boucle principale de Home Assistant (plus de blocage de l'interface)
	[Amélioration] Un seul client Modbus partagé, avec verrou d'accès pour sérialiser les échanges
	[Amélioration] Relecture de confirmation après chaque écriture de consigne pH ou ORP
	[Amélioration] Lectures hors plage physique ignorées (pH, température, taux de sel, ORP)
	[Amélioration] Fermeture propre de la connexion au déchargement de l'intégration
	[Amélioration] Métadonnées iot_class / integration_type ajoutées au manifest
	[Amélioration] Entité de filtration supprimée (non utilisée)
	[Correctif] Le capteur binaire de communication Modbus ne reflétait pas l'état réel de la liaison
