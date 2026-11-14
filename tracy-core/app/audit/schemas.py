"""Schémas Pydantic pour le module audit.

Module préparé. Aucune implémentation dans la V1.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


AuditEventType = Literal[
    "connexion",
    "commande",
    "paiement",
    "wallet",
    "outil_ia",
    "conversation",
    "erreur",
    "modification",
]


class AuditContext(BaseModel):
    """Contexte d'un événement d'audit.

    Fournit les informations nécessaires pour tracer l'événement :
    qui, quoi, quand, où, et pourquoi.
    """

    correlation_id: str
    user_id: str | None = None
    store_id: str | None = None
    agent_name: str | None = None
    tool_name: str | None = None
    session_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class AuditEvent(BaseModel):
    """Événement d'audit.

    Représente une action tracée dans le système d'audit. Chaque
    événement est immuable et horodaté.

    Types d'événements prévus (docs/tracy/02-ARCHITECTURE.md §Audit) :
    - connexion : connexion/déconnexion utilisateur
    - commande : création, modification, annulation de commande
    - paiement : initiation, confirmation, échec de paiement
    - wallet : consultation, retrait, dépôt
    - outil_ia : appel à un tool, réponse d'un agent
    - conversation : début/fin de conversation, transfert d'agent
    - erreur : erreur technique, exception non gérée
    - modification : modification de catalogue, prix, règle vendeur
    """

    event_id: str = Field(description="Identifiant unique de l'événement")
    event_type: AuditEventType
    timestamp: str = Field(description="Horodatage ISO 8601")
    context: AuditContext
    description: str = Field(description="Description lisible de l'événement")
    before_state: dict[str, str] | None = Field(
        default=None,
        description="État avant l'action (pour les modifications)",
    )
    after_state: dict[str, str] | None = Field(
        default=None,
        description="État après l'action (pour les modifications)",
    )
    severity: Literal["info", "warning", "critical"] = "info"
