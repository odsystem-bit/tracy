"""Orchestrateur Tracy Core, basé sur LangGraph (docs/tracy/02-ARCHITECTURE.md).

L'orchestrateur :
1. reçoit le message ou l'événement,
2. charge le contexte (mémoire courte via Redis),
3. classifie l'intention (docs/tracy/03-AGENTS.md §Principe de sélection),
4. sélectionne l'agent pertinent via le graphe LangGraph,
5. collecte le résultat de l'agent,
6. produit la réponse finale.

Tracy Core ne contient aucune logique métier Mantota. Il orchestre uniquement.

Règle (docs/tracy/03-AGENTS.md) : un agent n'est jamais sélectionné "par défaut"
— l'absence de correspondance claire déclenche une clarification.
"""

from __future__ import annotations

import asyncio
import re
import time
import uuid
from typing import TypedDict

from langgraph.graph import END, StateGraph

from app.agents.base import AgentInput, AgentOutput, BaseAgent
from app.agents.campaign_agent import CampaignAgent
from app.agents.catalog_agent import CatalogAgent
from app.agents.commercial_agent import CommercialAgent
from app.agents.location import extract_city
from app.agents.logistics_agent import LogisticsAgent
from app.agents.memory_agent import MemoryAgent
from app.agents.negotiation_agent import NegotiationAgent
from app.negotiation.reporting import wants_vendor_contact
from app.agents.order_agent import OrderAgent
from app.agents.payment_agent import PaymentAgent
from app.agents.restaurant_agent import RestaurantAgent
from app.agents.support_agent import SupportAgent
from app.agents.vendor_copilot import VendorCopilot
from app.config import get_settings
from app.core.intent import classify_intent, classify_intent_async
from app.core.llm_intent import classify_with_llm
from app.core.message_interpreter import apply_to_context, interpret_message, state_summary
from app.core.schemas import IncomingMessage, IntentClassification, TracyReply
from app.logging_config import bind_context, get_logger
from app.memory.short_term import ConversationContext, ConversationMessage, ShortTermMemory
from app.mantota_client.client import MantotaClient
from app.mantota_client.exceptions import MantotaError

logger = get_logger(__name__)


class GraphState(TypedDict):
    incoming: IncomingMessage
    correlation_id: str
    intent: IntentClassification
    agent_output: AgentOutput | None
    reply: str
    context: ConversationContext | None  # partagé entre classify et execute


class TracyOrchestrator:
    """Orchestrateur Tracy Core basé sur LangGraph.

    Le graphe comporte trois nœuds :
    - classify : classifie l'intention du message,
    - route : sélectionne l'agent selon l'intention,
    - execute : exécute l'agent sélectionné.

    V1 : CommercialAgent, NegotiationAgent, CatalogAgent, OrderAgent,
    PaymentAgent, SupportAgent, CampaignAgent, MemoryAgent sont implémentés.
    """

    def __init__(
        self,
        commercial_agent: CommercialAgent,
        negotiation_agent: NegotiationAgent,
        catalog_agent: CatalogAgent,
        order_agent: OrderAgent,
        payment_agent: PaymentAgent,
        support_agent: SupportAgent,
        campaign_agent: CampaignAgent,
        memory_agent: MemoryAgent,
        restaurant_agent: RestaurantAgent,
        short_term_memory: ShortTermMemory,
        mantota_client: MantotaClient,
        logistics_agent: LogisticsAgent | None = None,
        vendor_copilot: VendorCopilot | None = None,
    ) -> None:
        self._agents: dict[str, BaseAgent] = {
            "CommercialAgent": commercial_agent,
            "NegotiationAgent": negotiation_agent,
            "CatalogAgent": catalog_agent,
            "OrderAgent": order_agent,
            "PaymentAgent": payment_agent,
            "SupportAgent": support_agent,
            "CampaignAgent": campaign_agent,
            "MemoryAgent": memory_agent,
            "RestaurantAgent": restaurant_agent,
        }
        if logistics_agent is not None:
            self._agents["LogisticsAgent"] = logistics_agent
        if vendor_copilot is not None:
            self._agents["VendorCopilot"] = vendor_copilot
        self._memory = short_term_memory
        self._mantota = mantota_client
        self._graph = self._build_graph().compile()

        # Cache shop_config : store_id → (address_form, expiry_timestamp)
        # Évite un appel HTTP à chaque message pour récupérer address_form
        self._shop_config_cache: dict[str, tuple[str, float]] = {}
        self._shop_config_ttl: float = 300.0  # 5 minutes

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(GraphState)

        graph.add_node("classify", self._classify_node)
        graph.add_node("execute", self._execute_node)

        graph.set_entry_point("classify")
        graph.add_edge("classify", "execute")
        graph.add_edge("execute", END)

        return graph

    async def _classify_node(self, state: GraphState) -> GraphState:
        incoming = state["incoming"]

        # Charger le contexte de conversation pour le routing contextuel
        conversation_id = incoming.conversation_id or f"{incoming.store_id}:{incoming.customer_id}"
        context = await self._memory.get_context(conversation_id)

        # ── Pré-traitement : extraire les entités AVANT le routing ──
        # « je suis a calavi » remplit pending_city quel que soit l'agent
        # sélectionné — plus jamais d'info perdue par un mauvais routage.
        _extracted = interpret_message(incoming.text, context)
        apply_to_context(context, _extracted)
        if any((
            _extracted.declared_city, _extracted.delivery_city,
            _extracted.quantity, _extracted.payment_method,
            _extracted.named_product_ids,
        )):
            logger.info(
                "message_interpreter_extracted",
                declared_city=_extracted.declared_city,
                delivery_city=_extracted.delivery_city,
                quantity=_extracted.quantity,
                payment_method=_extracted.payment_method,
                named_products=_extracted.named_product_ids,
                correlation_id=state["correlation_id"],
            )

        state["context"] = context  # partager avec _execute_node pour éviter un 2e get_context

        intent = await classify_intent_async(incoming.text, context.last_intent)
        
        # ── Routing contextuel : si intent "unknown", utiliser le contexte ──
        if intent.intent == "unknown" and context.last_intent:
            # Follow-up : messages courts comme "ok", "oui", "je le prends", "donne moi le lien"
            text_lower = incoming.text.lower().strip()
            follow_up_patterns = [
                r"^(?:ok|d.?accord|ouais|oui|ouep|volontiers|génial|super|parfait)$",
                r"^(?:je le prends|je la prends|je veux celui.l[àa]|vas.y|go)$",
                r"^(?:donne.*lien|le lien|t[ée]l[ée]charger|t[ée]lecharger|download|installer.*app|l.app|l application)$",
                r"^(?:combien|c'est combien|le prix|disponible|en stock)$",
                r"^(?:comment.*paie|je peux payer|je paie|paiement|mom|cash|carte)$",
                r"^(?:o[ùu].*t[ée]l[ée]charger|o[ùu].*app|lien.*app|app.*lien)$",
                r"^(?:c'est.*compris|compris|bien reç.u|noté|parfait)$",
                # Référence de commande seule ("CMD-D4EDD8", "CMD D4EDD8", "48210")
                r"^cmd[-\s]?[0-9a-z]{4,10}$",
                r"^[0-9]{4,10}$",
            ]
            is_followup = any(re.search(p, text_lower) for p in follow_up_patterns)
            
            if is_followup:
                # Router vers le dernier agent qui avait le contexte
                last_agent = context.last_agent or "CommercialAgent"
                last_intent = context.last_intent or "unknown"
                # "ok / je le prends" après une contre-offre = acceptation du prix
                # annoncé : le CommercialAgent fige le prix et lance la commande.
                if (
                    last_agent == "NegotiationAgent"
                    and context.negotiation_last_ask is not None
                    and any(re.search(p, text_lower) for p in follow_up_patterns[:2])
                ):
                    last_agent, last_intent = "CommercialAgent", "order"
                intent = IntentClassification(
                    intent=last_intent,
                    confidence=0.6,
                    selected_agent=last_agent,
                    reason=f"Follow-up contextual routing (last_intent={context.last_intent})",
                )
                logger.info(
                    "orchestrator_followup_routing",
                    last_intent=context.last_intent,
                    last_agent=last_agent,
                    correlation_id=state["correlation_id"],
                )

        # ── Repli LLM : regex = unknown, pas un follow-up, pas de flux de commande actif ──
        if (
            intent.intent == "unknown"
            and get_settings().llm_intent_fallback
            and context.task_state not in (
                "awaiting_qty_city", "awaiting_confirmation", "awaiting_cancel_confirm",
            )
        ):
            llm_intent = await classify_with_llm(
                self._agents["CommercialAgent"]._ai_gateway,  # noqa: SLF001
                incoming.text,
                context.last_intent,
            )
            if llm_intent is not None and llm_intent.selected_agent in self._agents:
                intent = llm_intent
                logger.info(
                    "orchestrator_llm_intent",
                    intent=llm_intent.intent,
                    confidence=llm_intent.confidence,
                    correlation_id=state["correlation_id"],
                )

        # ── "Je veux parler au vendeur" → mise en relation gérée par CommercialAgent ──
        if wants_vendor_contact(incoming.text) and intent.selected_agent != "CommercialAgent":
            intent = IntentClassification(
                intent="support",
                confidence=0.85,
                selected_agent="CommercialAgent",
                reason="Vendor contact request",
            )

        # ── Flux de commande en cours → CommercialAgent ──
        # Pendant la collecte quantité/ville ou après création, les confirmations,
        # offres de prix et messages ambigus restent dans le flux (pending) au lieu
        # de repartir vers OrderAgent/NegotiationAgent qui ignoreraient le contexte.
        _cancel_words = re.search(
            r"annul|supprim|plus besoin|veux\s+plu|veut\s+plu|rach[èe]te|l[àa]che",
            incoming.text.lower(),
        )
        if (
            context.task_state in ("awaiting_qty_city", "awaiting_confirmation", "order_created")
            and intent.intent in ("unknown", "order", "negotiation")
            and intent.selected_agent != "CommercialAgent"
            and not _cancel_words
            and context.task_state != "awaiting_cancel_confirm"
        ):
            intent = IntentClassification(
                intent="order",
                confidence=0.75,
                selected_agent="CommercialAgent",
                reason=f"Contextual override: order flow active (task_state={context.task_state})",
            )
            logger.info(
                "orchestrator_order_flow_override",
                task_state=context.task_state,
                correlation_id=state["correlation_id"],
            )

        # ── Routing contextuel : "voir" / "catalogue" / "image" avec produits récents ──
        # Si le client demande à voir les produits déjà proposés, router vers CommercialAgent
        # pour qu'il renvoie les cards, peu importe l'intent classifié (ex: catalog_management)
        if context.last_cards and intent.selected_agent != "CommercialAgent":
            text_lower = incoming.text.lower().strip()
            _show_products_words = (
                "voir", "vois", "montre", "image", "images",
                "photo", "photos", "catalogue", "affiche", "afficher",
            )
            if any(w in text_lower for w in _show_products_words):
                intent = IntentClassification(
                    intent="product_search",
                    confidence=0.8,
                    selected_agent="CommercialAgent",
                    reason="Contextual override: show-products intent with recent cards",
                )
                logger.info(
                    "orchestrator_show_products_override",
                    original_agent=intent.selected_agent,
                    new_agent="CommercialAgent",
                    correlation_id=state["correlation_id"],
                )

        # ── Routing contextuel : intercepter payment/order quand produit en contexte ──
        # Si le client a un produit sélectionné et pose une question courte de paiement/prix,
        # garder sur CommercialAgent pour ne pas perdre le contexte produit
        if intent.intent in ("payment", "order") and context.product_name:
            text_lower = incoming.text.lower().strip()
            short_followup = [
                r"^(?:combien|c'est combien|le prix|disponible|en stock)$",
                r"^(?:comment.*paie|je peux payer|je paie|comment payer)$",
                r"^(?:je le prends|je la prends|je veux celui.l[àa])$",
                r"^(?:c'est.*bon|ok.*je.*prends|je.*l'ach[èe]te)$",
            ]
            is_short = any(re.search(p, text_lower) for p in short_followup)
            if is_short:
                intent = IntentClassification(
                    intent="product_search",
                    confidence=0.7,
                    selected_agent="CommercialAgent",
                    reason=f"Contextual override: product in context ({context.product_name}), short follow-up",
                )
                logger.info(
                    "orchestrator_context_override",
                    original_intent="payment/order",
                    new_agent="CommercialAgent",
                    product=context.product_name,
                    correlation_id=state["correlation_id"],
                )

        # Photo jointe → CommercialAgent, seul agent qui analyse les images.
        # Sinon « tu as ça ? » pourrait partir ailleurs et l'image serait ignorée.
        if incoming.image and intent.selected_agent != "CommercialAgent":
            intent = IntentClassification(
                intent="product_search",
                confidence=1.0,
                selected_agent="CommercialAgent",
            )

        state["intent"] = intent
        logger.info(
            "orchestrator_intent_classified",
            intent=intent.intent,
            agent=intent.selected_agent,
            confidence=intent.confidence,
            correlation_id=state["correlation_id"],
        )
        return state

    async def _get_address_form(self, store_id: str) -> str:
        """Récupère address_form avec cache en mémoire (TTL 5 min)."""
        if not store_id or store_id == "public":
            return "tu"

        cached = self._shop_config_cache.get(store_id)
        if cached and cached[1] > time.monotonic():
            return cached[0]

        try:
            shop_config = await self._mantota.get_shop_config(store_id)
            form = shop_config.address_form
        except MantotaError:
            form = "tu"

        self._shop_config_cache[store_id] = (form, time.monotonic() + self._shop_config_ttl)
        return form

    async def _execute_node(self, state: GraphState) -> GraphState:
        intent = state["intent"]
        incoming = state["incoming"]
        correlation_id = state["correlation_id"]

        agent = self._agents.get(intent.selected_agent)
        if agent is None:
            logger.warning(
                "orchestrator_agent_not_implemented",
                agent=intent.selected_agent,
                correlation_id=correlation_id,
            )
            state["reply"] = (
                "Je ne peux pas encore traiter ce type de demande. "
                "Pouvez-vous reformuler ou me contacter plus tard ?"
            )
            state["agent_output"] = None
            return state

        # Charger l'historique et le contexte de conversation
        # Contexte déjà chargé dans _classify_node → réutiliser (évite un 2e appel Redis)
        conversation_id = incoming.conversation_id or f"{incoming.store_id}:{incoming.customer_id}"
        context = state.get("context")
        if context is None:
            # Fallback si _classify_node n'a pas pu charger le contexte
            history, context = await asyncio.gather(
                self._memory.get_history_as_strings(conversation_id),
                self._memory.get_context(conversation_id),
            )
        else:
            history = await self._memory.get_history_as_strings(conversation_id)

        # ── Injecter l'état structuré en tête d'historique ──
        # L'agent voit « [État collecté] produit=Mocassins | quantité=1 |
        # ville=Calavi | paiement=MTN MoMo » au lieu de reparser le texte brut.
        _summary = state_summary(context)
        if _summary:
            history = [f"system: {_summary}", *history]

        # Récupérer le pays : priorité incoming > contexte précédent
        effective_country = incoming.country_code or context.country_code
        effective_city = incoming.city or extract_city(incoming.text) or context.user_city
        effective_lat = incoming.latitude if incoming.latitude is not None else context.user_latitude
        effective_lng = incoming.longitude if incoming.longitude is not None else context.user_longitude

        # Récupérer la forme d'adresse configurée par le vendeur (par boutique)
        # Cache en mémoire — évite un appel HTTP à chaque message
        address_form = await self._get_address_form(incoming.store_id or "")
        agent.set_address_form(address_form)

        agent_input = AgentInput(
            message=incoming.text,
            store_id=incoming.store_id,
            correlation_id=correlation_id,
            customer_id=incoming.customer_id,
            conversation_id=incoming.conversation_id,
            conversation_history=history,
            country_code=effective_country,
            user_city=effective_city,
            user_latitude=effective_lat,
            user_longitude=effective_lng,
            conversation_context=context,
            image=incoming.image,
        )

        bind_context(agent=intent.selected_agent)
        output = await agent.handle(agent_input)

        # ── Anti-spam : ne pas renvoyer les mêmes cards à chaque réponse ──
        # Le client garde la bulle précédente avec ses cards ; on ne ré-affiche
        # que si la sélection change ou s'il demande explicitement à revoir.
        if output.cards and context.last_cards:
            _new_ids = {str(c.id) for c in output.cards}
            _old_ids = {str(c.id) for c in context.last_cards}
            _show_words = (
                "voir", "vois", "montre", "image", "images",
                "photo", "photos", "catalogue", "affiche", "afficher",
            )
            if _new_ids == _old_ids and not any(
                w in incoming.text.lower() for w in _show_words
            ):
                output.cards = None

        # Sauvegarder dans la mémoire courte + mettre à jour le contexte — tout en parallèle
        context.last_agent = intent.selected_agent
        context.last_intent = intent.intent
        if effective_country:
            context.country_code = effective_country
        if effective_city:
            context.user_city = effective_city
        if effective_lat is not None and effective_lng is not None:
            context.user_latitude = effective_lat
            context.user_longitude = effective_lng

        # ── Extraire le produit sélectionné depuis les cards ──
        if output.cards:
            context.last_cards = output.cards
            # Si une seule card, c'est le produit sélectionné
            # Ne jamais rétrograder un état de flux de commande actif quand
            # l'agent renvoie des cartes (ex : "oui" → ask qty/city + cards).
            _ORDER_STATES = ("awaiting_qty_city", "awaiting_confirmation", "order_created")
            if len(output.cards) == 1:
                # Produit unique trouvé → produit "courant"
                card = output.cards[0]
                if (
                    context.task_state in _ORDER_STATES
                    and context.product_id
                    and context.product_id != str(card.id)
                ):
                    # Changement de produit pendant la collecte : réinitialiser
                    context.pending_quantity = None
                    context.pending_city = None
                context.product_id = str(card.id)
                context.product_name = card.name
                context.product_mentioned = card.name
                context.product_price = card.raw_price
                context.product_store_id = card.store_id
                if context.task_state not in _ORDER_STATES:
                    context.task_state = "product_found"
                context.current_task = "product_search"
                context.last_tool_result = f"search_products: {card.name} ({card.price})"
            else:
                # Plusieurs cards : le client nomme-t-il explicitement l'une d'elles ?
                _msg = incoming.text.lower()
                _named = [
                    c for c in output.cards
                    if c.name.lower() in _msg
                    or all(w in _msg for w in c.name.lower().split() if len(w) > 2)
                ]
                if len(_named) == 1:
                    card = _named[0]
                    if (
                        context.task_state in _ORDER_STATES
                        and context.product_id
                        and context.product_id != str(card.id)
                    ):
                        context.pending_quantity = None
                        context.pending_city = None
                    context.product_id = str(card.id)
                    context.product_name = card.name
                    context.product_mentioned = card.name
                    context.product_price = card.raw_price
                    context.product_store_id = card.store_id
                    if context.task_state not in _ORDER_STATES:
                        context.task_state = "product_found"
                    context.current_task = "product_search"
                    context.last_tool_result = f"search_products: {card.name} ({card.price})"
                else:
                    # Produits proposés, en attente de choix
                    if context.task_state not in _ORDER_STATES:
                        context.task_state = "products_proposed"
                    context.current_task = "product_search"
                    context.last_tool_result = f"search_products: {len(output.cards)} results"

        # ── Détecter les follow-up confirmations ──
        text_lower = incoming.text.lower().strip()
        if text_lower in ("oui", "ok", "ouais", "ouep", "volontiers", "go", "vas-y", "vas.y", "parfait", "super", "génial"):
            context.last_user_confirmation = "yes"
        elif text_lower in ("non", "no", "non merci", "pas maintenant"):
            context.last_user_confirmation = "no"

        await asyncio.gather(
            self._memory.append(
                conversation_id,
                ConversationMessage(role="user", content=incoming.text),
            ),
            self._memory.append(
                conversation_id,
                ConversationMessage(role="assistant", content=output.reply),
            ),
            self._memory.update_context(conversation_id, context),
        )

        state["reply"] = output.reply
        state["agent_output"] = output
        return state

    async def handle_message(self, incoming: IncomingMessage) -> TracyReply:
        correlation_id = str(uuid.uuid4())
        bind_context(correlation_id=correlation_id)

        logger.info(
            "orchestrator_received_message",
            store_id=incoming.store_id,
            customer_id=incoming.customer_id,
            correlation_id=correlation_id,
            message_preview=incoming.text[:100],
        )

        result = await self._graph.ainvoke(
            {
                "incoming": incoming,
                "correlation_id": correlation_id,
                "intent": IntentClassification(
                    intent="unknown",
                    confidence=0.0,
                    selected_agent="CommercialAgent",
                ),
                "agent_output": None,
                "reply": "",
                "context": None,
            }
        )

        agent_output: AgentOutput | None = result.get("agent_output")
        intent: IntentClassification = result.get("intent", IntentClassification(
            intent="unknown",
            confidence=0.0,
            selected_agent="CommercialAgent",
        ))

        reply = TracyReply(
            text=result["reply"],
            correlation_id=correlation_id,
            agent=intent.selected_agent,
            tools_used=agent_output.tools_used if agent_output else [],
            cards=agent_output.cards if agent_output else None,
            data=agent_output.data if agent_output else None,
        )

        logger.info(
            "orchestrator_reply_sent",
            correlation_id=correlation_id,
            agent=intent.selected_agent,
            tools_used=reply.tools_used,
        )

        return reply
