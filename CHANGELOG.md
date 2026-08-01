pool_technologie – Version 1.0.8
	Ajout du modèle Just Salt Pro (même mapping Modbus, reverse engineering confirmé par un utilisateur du forum HACF)
	Les consignes pH et ORP (number.py) sont maintenant rafraîchies à chaque cycle au lieu d'être lues uniquement au démarrage de l'intégration : un changement fait depuis l'application Pool Technologie (ou un autre client Modbus) est désormais répercuté dans Home Assistant sans redémarrage. Les lectures hors plage sont ignorées, la dernière valeur connue est conservée
	notify_modbus_success/failure n'est plus appelé une fois par capteur mais une seule fois par cycle (au moins une lecture réussie = cycle réussi) : une lecture isolée en échec sur un registre ponctuellement invalide ne fait plus avancer à tort le compteur de déconnexion
	Seuil de détection de déconnexion abaissé à 3 cycles ratés d'affilée (au lieu de 5), pour compenser le changement ci-dessus et garder un temps de détection comparable à avant
	Ajout du capteur diagnostic "Tension cellule" (registre 1061), non créé pour le modèle Ibiza iBasel Duo — confirmé indisponible sur cette topologie (l'iBaRegul Duo ne communique pas cette donnée depuis l'iBaSel, registre à 0 en permanence)
	L'attribut modbus_address (déjà présent sur les capteurs) est désormais aussi exposé sur les entités number (consignes pH/ORP) et switch (mode boost, régulation pH auto)
	Ajout de la "Consigne électrolyse" (registre 4168, %), réglage éditable disponible uniquement sur Poolsquad UV et seulement en l'absence de sonde ORP (l'électrolyse est sinon pilotée automatiquement) — fonctionnalité confirmée par un utilisateur HACS (Pierre_Brdn)
	Ajout d'un template d'issue GitHub pour signaler un nouveau registre découvert ou confirmer/infirmer qu'une entité fonctionne sur un modèle donné, et d'un tableau de compatibilité par modèle dans le README (✅/❌/❓) pour orienter les contributions de la communauté
	Ajout des traductions anglaise et espagnole (translations/en.json, translations/es.json), en plus du français

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
