pool_technologie – Version 1.0.7
	Préparation du dépôt pour HACS : ajout de hacs.json, LICENSE, logos de la marque, workflows de validation (HACS action + hassfest)
	Correction du manifest.json : ajout du champ issue_tracker requis et tri des clés (domain, name, puis ordre alphabétique)

pool_technologie – Version 1.0.6
	Ajout d'une entité switch pour activer/désactiver la régulation pH automatique
	Ajout d'une option de configuration (activable après coup, avec rechargement automatique) pour indiquer si une sonde ORP est installée : sans elle, les entités ORP (capteur, consigne en lecture seule, consigne éditable) ne sont pas créées
	L'intervalle de rafraîchissement Modbus est maintenant configurable à l'installation et modifiable ensuite dans les options, au lieu d'être fixé en dur à 60s
	Ajout des modèles WaterAir Salt Gold Duo et Poolsquad UV (confirmés fonctionnels par des utilisateurs du forum HACF, même mapping Modbus que l'Ibiza iBasel Duo)
	Correction : le switch de mode boost (ajouté en 1.0.5) tentait une lecture Modbus à chaque cycle même électrolyseur déconnecté, provoquant des avertissements de dépassement d'intervalle (timeouts de ~10s)
	Correction : le switch de mode boost sondait aussi la reconnexion de son côté, ce qui doublait la fréquence réelle des tentatives par rapport à celle voulue
	Les entités switch (boost, régulation pH auto) sont désormais rafraîchies sur le même cycle que les capteurs (piloté par le controller) plutôt que par leur propre polling natif Home Assistant, pour rester alignées sur l'intervalle configuré et éviter tout sondage dupliqué de la reconnexion
	Ajout de l'adresse Modbus en attribut de chaque capteur

pool_technologie – Version 1.0.5
	Ajout d'une entité switch pour activer/désactiver le mode boost
	Les cycles de lecture sont sautés quand l'électrolyseur est déconnecté, avec tentative de reconnexion périodique, au lieu de tenter la lecture à chaque cycle

pool_technologie – Version 1.0.4
	Connexion Modbus TCP maintenue ouverte en continu (fin des connexions/déconnexions à chaque lecture ou écriture)
	Lectures et écritures Modbus déplacées hors de la boucle principale de Home Assistant (thread executor) pour éviter tout blocage de l'interface
	Ajout d'un verrou d'accès pour sérialiser les échanges Modbus entre les capteurs et les entités number
	Un seul client Modbus partagé entre les plateformes sensor et number (suppression d'une connexion dupliquée)
	Confirmation par relecture après chaque écriture de consigne pH ou ORP
	Filtrage des lectures hors plage physique (pH, température, taux de sel, ORP) pour écarter les valeurs aberrantes
	Correction d'un bug empêchant le capteur binaire de communication Modbus de refléter l'état réel de la liaison (le rafraîchissement périodique restait figé sur un callback qui ne lisait jamais Modbus)
	Fermeture propre de la connexion Modbus au déchargement de l'intégration
	Suppression complète de l'entité de filtration (config_flow, options flow, binary_sensor), non utilisée
	Ajout des métadonnées iot_class / integration_type dans le manifest
