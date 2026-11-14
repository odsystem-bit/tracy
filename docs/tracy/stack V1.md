Donc notre stack V1 devient beaucoup plus raisonnable
┌──────────────────────────────┐
│       Web / future APK       │
└──────────────┬───────────────┘
               │
            FastAPI
               │
         ┌─────▼─────┐
         │ TRACY CORE│
         └─────┬─────┘
               │
          LangGraph
        ┌──────┴──────┐
        │             │
    AI Gateway       Tools
        │             │
 GPT/Claude/etc.    Mantota
                      │
                   Moneroo

        ┌─────────────────┐
        │ Redis           │
        │ PostgreSQL      │
        └─────────────────┘

Et plus tard seulement :

RabbitMQ
gRPC
Ollama en production
multi-GPU
Kubernetes
etc.
Pourquoi je préfère cette architecture à « tout faire dans Laravel »

Parce que Laravel reste excellent pour Mantota métier :

boutiques
produits
commandes
wallet
paiements
campagnes
partenaires
Moneroo

Et Python devient excellent pour Tracy IA :

agents
LLM
mémoire conversationnelle
tool calling
orchestration
raisonnement
négociation
relances

On ne détruit donc pas Mantota pour construire Tracy.