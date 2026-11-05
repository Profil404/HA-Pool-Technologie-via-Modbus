pool_technologie – Version 261105
	[Information] Home Assistant 2026.10.1 minimum requis
	[Amélioration] Connexion Modbus confiée à Home Assistant (async_get_unit) : l'intégration n'ouvre plus son propre client et ne dépend plus de pymodbus. Plus de threads ni de verrou : Home Assistant ne peut plus se figer quand l'électrolyseur est injoignable (#12, refonte par @chpego)
	[Amélioration] La connexion est partagée avec les autres intégrations Modbus qui utilisent la même passerelle, et rouverte automatiquement après une coupure (#7)
	[Amélioration] Démarrage de Home Assistant plus rapide quand l'électrolyseur est éteint : la première lecture se fait en arrière-plan (#12, merci @cedricrosse)
	[Amélioration] Redémarrage de Home Assistant électrolyseur éteint : les réglages (consignes, concentration, taille du bassin, heure d'inversion) et les interrupteurs (boost, régulation pH automatique) reprennent leur dernier état connu au lieu de leur valeur par défaut
	[Amélioration] Un registre utilisé par plusieurs entités (consigne pH, consigne ORP, taille du bassin) n'est plus lu qu'une seule fois par cycle
	[Amélioration] L'assistant de configuration vérifie que l'électrolyseur répond, refuse un électrolyseur déjà configuré (même adresse IP, port et adresse Modbus) et signale une passerelle déjà utilisée par Home Assistant avec d'autres paramètres de liaison
	[Amélioration] README : installation via le Marketplace intégré à Home Assistant depuis la 2026.11 (ex-HACS)
	[Information] Aucune migration : mêmes entités, mêmes identifiants, mêmes options. Pendant une coupure, les entités gardent leur dernière valeur et seul « État de la communication Modbus » passe à désactivé
	[Information] Testé sur Poolsquad UV (@cedricrosse) et sur Ibiza iBasel Duo (@Profil404) : démarrage, coupure, retour de l'électrolyseur et écritures

pool_technologie – Version 261102
	[Correctif] Home Assistant pouvait encore se figer au démarrage quand l'électrolyseur était injoignable : les entités de réglage et les interrupteurs ne font plus de lecture initiale tant que la connexion de départ n'a pas réussi, leur valeur est rafraîchie au premier cycle réussi (#12, merci @cedricrosse)

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
