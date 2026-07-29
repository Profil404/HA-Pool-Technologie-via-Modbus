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
