"""Module events — système d'événements interne de Tracy Core.

Module préparé. Aucune implémentation dans la V1.
Voir README.md pour le fonctionnement futur.

Tous les événements de Tracy devront passer par cet EventBus.
Cela permet :
- de découpler les composants (agents, tools, orchestrateur),
- de brancher l'audit, les notifications et la sécurité sur les mêmes événements,
- d'ajouter de nouveaux subscribers sans modifier le code existant.
"""
