"""Mémoire courte (docs/tracy/06-MEMORY.md) — portée : la conversation en cours.

Contient :
- les derniers messages échangés,
- le produit ou l'action évoqué récemment ("celui-ci", "le même en bleu"),
- le panier en cours de constitution,
- le contexte de conversation (préférences détectées, produit évoqué, résumé).

Durée de vie : la conversation. Stockée en Redis, jamais persistée en base durable.

Cette implémentation fournit deux backends :
- InMemoryShortTermMemory : pour les tests et le développement local,
- RedisShortTermMemory : pour staging/production (requiert Redis).

Le choix du backend est déterminé par la configuration (app/config.py).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Literal

from pydantic import BaseModel, Field

from app.core.schemas import ProductCard
from app.logging_config import get_logger

logger = get_logger(__name__)


class ConversationMessage(BaseModel):
    """Message stocké dans la mémoire courte."""

    role: Literal["user", "assistant"]
    content: str
    timestamp: str | None = None


class ConversationContext(BaseModel):
    """Contexte de conversation enrichi (docs/tracy/06-MEMORY.md §Contexte).

    Stocke les informations utiles échangées pendant la conversation
    pour personnaliser les réponses sans reposer sur la mémoire longue
    (qui appartient à Mantota).

    Ce contexte est volatile : il vit et meurt avec la conversation.
    """

    product_mentioned: str | None = None
    preferences_detected: list[str] = Field(default_factory=list)
    conversation_summary: str | None = None
    last_agent: str | None = None
    last_intent: str | None = None
    country_code: str | None = None
    user_city: str | None = None
    user_latitude: float | None = None
    user_longitude: float | None = None

    # ── Conversation state (task tracking) ──
    current_task: str | None = None
    """Tâche en cours : product_search, purchase, negotiation, order, support, etc."""
    
    task_state: str | None = None
    """État de la tâche : searching, product_found, awaiting_quantity, awaiting_city, awaiting_confirmation, etc."""
    
    product_id: str | None = None
    """ID du produit actuellement sélectionné dans la conversation."""
    
    product_name: str | None = None
    """Nom du produit actuellement sélectionné."""
    
    product_price: float | None = None
    """Prix du produit actuellement sélectionné."""
    
    product_store_id: str | None = None
    """Store_id du produit sélectionné."""
    
    pending_action: str | None = None
    """Action en attente : awaiting_download_link, awaiting_quantity, etc."""
    
    last_tool_result: str | None = None
    """Dernier résultat de tool (résumé court)."""
    
    last_user_confirmation: str | None = None
    """Dernière confirmation utilisateur : oui, non, ok, etc."""
    
    language: str | None = None
    """Langue détectée de l'utilisateur : fr, en, etc."""

    # ── Commande en cours (créée pendant la conversation) ──
    pending_quantity: int | None = None
    """Quantité collectée pour la commande en cours (le client peut donner
    la quantité et la ville dans des messages séparés)."""

    pending_city: str | None = None
    """Ville de livraison collectée pour la commande en cours."""

    pending_payment_method: str | None = None
    """Moyen de paiement cité par le client (« MTN MoMo », « carte », « Wave »…)."""

    user_phone: str | None = None
    """Numéro de téléphone laissé par le client (ex: contact vendeur, livraison)."""

    pending_multi_ids: list[str] = Field(default_factory=list)
    """IDs produits d'une commande multi-produits en attente de confirmation."""

    last_named_ids: list[str] = Field(default_factory=list)
    """IDs des cards citées nommément dans le dernier message (1 ou plusieurs)."""

    pending_cancel_ref: str | None = None
    """Référence de la commande à annuler, en attente de confirmation client."""

    order_id: str | None = None
    """ID de la dernière commande créée dans cette conversation."""

    order_reference: str | None = None
    """Référence de la commande (ex: CMD-XXXX)."""

    order_payment_url: str | None = None
    """Lien de paiement Moneroo de la commande."""

    order_tracking_url: str | None = None
    """Lien de suivi de la commande."""

    # ── Négociation en cours (état par produit) ──
    negotiation_product_id: str | None = None
    """Produit sur lequel porte la négociation en cours."""

    negotiation_rounds: int = 0
    """Nombre de relances de prix du client sur ce produit."""

    vendor_reports_sent: list[str] = Field(default_factory=list)
    """Comptes-rendus déjà envoyés au vendeur (clé kind:product_id) pour éviter les doublons."""

    negotiation_last_price_asks: int = 0
    """Nombre de fois où le client a explicitement demandé le « dernier prix »."""

    negotiation_last_ask: float | None = None
    """Dernier prix annoncé par Tracy (ne remonte jamais)."""

    negotiated_price: float | None = None
    """Prix accepté par les deux parties (appliqué à la commande, revalidé par Laravel)."""

    # ── Cartes produit récemment proposées (pour renvoi sur demande) ──
    last_cards: list[ProductCard] | None = None
    """Cartes produit de la dernière recherche — renvoyées si le client demande à voir/voir."""


class ShortTermMemory(ABC):
    """Interface abstraite de la mémoire courte (docs/tracy/06-MEMORY.md)."""

    @abstractmethod
    async def get_history(self, conversation_id: str) -> list[ConversationMessage]:
        """Retourne l'historique des messages d'une conversation."""

    @abstractmethod
    async def append(self, conversation_id: str, message: ConversationMessage) -> None:
        """Ajoute un message à l'historique d'une conversation."""

    @abstractmethod
    async def clear(self, conversation_id: str) -> None:
        """Efface l'historique d'une conversation."""

    @abstractmethod
    async def get_context(self, conversation_id: str) -> ConversationContext:
        """Retourne le contexte enrichi d'une conversation.

        Si aucun contexte n'existe, retourne un ConversationContext vide.
        """

    @abstractmethod
    async def update_context(self, conversation_id: str, context: ConversationContext) -> None:
        """Met à jour le contexte enrichi d'une conversation.

        Remplace entièrement le contexte existant.
        """

    async def get_history_as_strings(self, conversation_id: str) -> list[str]:
        """Retourne l'historique sous forme de chaînes (pour AgentInput.conversation_history)."""
        messages = await self.get_history(conversation_id)
        return [f"{m.role}: {m.content}" for m in messages]


class InMemoryShortTermMemory(ShortTermMemory):
    """Mémoire courte en mémoire — pour tests et développement local."""

    def __init__(self, max_history: int = 20) -> None:
        self._store: dict[str, list[ConversationMessage]] = {}
        self._contexts: dict[str, ConversationContext] = {}
        self._max_history = max_history

    async def get_history(self, conversation_id: str) -> list[ConversationMessage]:
        return self._store.get(conversation_id, [])

    async def append(self, conversation_id: str, message: ConversationMessage) -> None:
        history = self._store.setdefault(conversation_id, [])
        history.append(message)
        if len(history) > self._max_history:
            self._store[conversation_id] = history[-self._max_history :]

    async def clear(self, conversation_id: str) -> None:
        self._store.pop(conversation_id, None)
        self._contexts.pop(conversation_id, None)

    async def get_context(self, conversation_id: str) -> ConversationContext:
        return self._contexts.get(conversation_id, ConversationContext())

    async def update_context(self, conversation_id: str, context: ConversationContext) -> None:
        self._contexts[conversation_id] = context


class RedisShortTermMemory(ShortTermMemory):
    """Mémoire courte Redis — pour staging/production.

    Utilise une liste Redis par conversation avec TTL configurable.
    """

    def __init__(self, redis_url: str, ttl: int = 3600, max_history: int = 20) -> None:
        import redis.asyncio as aioredis

        self._redis = aioredis.from_url(redis_url, decode_responses=True)
        self._ttl = ttl
        self._max_history = max_history
        self._key_prefix = "tracy:memory:short:"

    def _key(self, conversation_id: str) -> str:
        return f"{self._key_prefix}{conversation_id}"

    def _context_key(self, conversation_id: str) -> str:
        return f"{self._key_prefix}ctx:{conversation_id}"

    async def get_history(self, conversation_id: str) -> list[ConversationMessage]:
        import json

        raw = await self._redis.lrange(self._key(conversation_id), 0, -1)
        return [ConversationMessage.model_validate(json.loads(item)) for item in raw]

    async def append(self, conversation_id: str, message: ConversationMessage) -> None:
        import json

        key = self._key(conversation_id)
        await self._redis.rpush(key, json.dumps(message.model_dump()))
        await self._redis.ltrim(key, -self._max_history, -1)
        await self._redis.expire(key, self._ttl)

    async def clear(self, conversation_id: str) -> None:
        await self._redis.delete(self._key(conversation_id))
        await self._redis.delete(self._context_key(conversation_id))

    async def get_context(self, conversation_id: str) -> ConversationContext:
        import json

        raw = await self._redis.get(self._context_key(conversation_id))
        if raw is None:
            return ConversationContext()
        return ConversationContext.model_validate(json.loads(raw))

    async def update_context(self, conversation_id: str, context: ConversationContext) -> None:
        import json

        key = self._context_key(conversation_id)
        await self._redis.set(key, json.dumps(context.model_dump()))
        await self._redis.expire(key, self._ttl)

    async def aclose(self) -> None:
        await self._redis.aclose()


def create_short_term_memory(
    redis_url: str,
    ttl: int = 3600,
    max_history: int = 20,
    use_redis: bool = False,
) -> ShortTermMemory:
    """Factory pour la mémoire courte selon l'environnement.

    Args:
        redis_url: URL Redis (utilisé si use_redis=True).
        ttl: Durée de vie en secondes.
        max_history: Nombre maximum de messages conservés.
        use_redis: Si True, utilise Redis ; sinon, mémoire en RAM.

    Returns:
        Une instance de ShortTermMemory.
    """
    if use_redis:
        logger.info("short_term_memory_redis", ttl=ttl, max_history=max_history)
        return RedisShortTermMemory(redis_url=redis_url, ttl=ttl, max_history=max_history)

    logger.info("short_term_memory_inmemory", max_history=max_history)
    return InMemoryShortTermMemory(max_history=max_history)
