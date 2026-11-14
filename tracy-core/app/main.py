"""Point d'entrée FastAPI de Tracy Core (docs/tracy/02-ARCHITECTURE.md).

Architecture en couches (docs/tracy/02-ARCHITECTURE.md) :
    Client → Gateway (auth + rate limit) → Tracy Core (orchestrateur) → Agents → Tools → Mantota

Toutes les requêtes passent par la Gateway (auth) puis l'orchestrateur (LangGraph).
Aucune logique métier ici — uniquement le wiring des dépendances (DI).

Règles (docs/tracy/07-DEVELOPMENT_RULES.md) :
- 100% asynchrone, dépendances injectées, Pydantic, logs structurés.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import Depends, FastAPI

from app.agents.campaign_agent import CampaignAgent
from app.agents.catalog_agent import CatalogAgent
from app.agents.commercial_agent import CommercialAgent
from app.agents.logistics_agent import LogisticsAgent
from app.agents.memory_agent import MemoryAgent
from app.agents.negotiation_agent import NegotiationAgent
from app.agents.order_agent import OrderAgent
from app.agents.payment_agent import PaymentAgent
from app.agents.restaurant_agent import RestaurantAgent
from app.agents.support_agent import SupportAgent
from app.ai_gateway.factory import create_ai_gateway
from app.config import get_settings
from app.core.orchestrator import TracyOrchestrator
from app.core.schemas import IncomingMessage, TracyReply
from app.gateway.auth import verify_gateway_api_key
from app.gateway.middleware import CorrelationIdMiddleware
from app.gateway.rate_limit import check_rate_limit, configure_rate_limiter
from app.logging_config import configure_logging, get_logger
from app.mantota_client.client import MantotaClient
from app.memory.short_term import create_short_term_memory
from app.tools.activate_tracy_subscription import ActivateTracySubscriptionTool
from app.tools.cancel_order import CancelOrderTool
from app.tools.create_dispute import CreateDisputeTool
from app.tools.create_order import CreateOrderTool
from app.tools.create_payment import CreatePaymentTool
from app.tools.create_restaurant_order import CreateRestaurantOrderTool
from app.tools.create_store import CreateStoreTool
from app.tools.create_support_ticket import CreateSupportTicketTool
from app.tools.delete_memory import DeleteMemoryTool
from app.tools.get_campaign import GetCampaignTool
from app.tools.get_restaurant_menu import GetRestaurantMenuTool
from app.tools.get_wallet import GetWalletTool
from app.tools.registry import ToolRegistry
from app.tools.request_withdrawal import RequestWithdrawalTool
from app.tools.save_memory import SaveMemoryTool
from app.tools.search_catalog import SearchCatalogTool
from app.tools.search_memory import SearchMemoryTool
from app.tools.search_partner import SearchPartnerTool
from app.tools.search_products import SearchProductsTool
from app.tools.search_restaurants import SearchRestaurantsTool
from app.tools.search_store import SearchStoreTool
from app.tools.get_currencies import GetCurrenciesTool
from app.tools.get_delivery_info import GetDeliveryInfoTool
from app.tools.send_catalog import SendCatalogTool
from app.tools.send_payment_link import SendPaymentLinkTool
from app.tools.track_order import TrackOrderTool
from app.tools.track_restaurant_order import TrackRestaurantOrderTool
from app.tools.get_shop_config import GetShopConfigTool
from app.tools.search_knowledge import SearchKnowledgeTool
from app.tools.update_memory import UpdateMemoryTool
from app.agents.vendor_copilot import VendorCopilot
from app.tools.vendor_reports import (
    ConnectVendorTool,
    GetVendorReportsTool,
    GetVendorStatsTool,
    ScheduleFollowUpTool,
    SendVendorReportTool,
)
from app.tools.update_shop_config import UpdateShopConfigTool
from app.vision.endpoints import router as vision_router
from app.restaurant.endpoints import router as restaurant_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Cycle de vie de Tracy Core : initialise et nettoie toutes les dépendances."""
    settings = get_settings()
    configure_logging(settings.environment, settings.log_level)
    logger = get_logger("main")

    logger.info(
        "tracy_core_starting",
        environment=settings.environment,
        default_ai_provider=settings.default_ai_provider,
        fallback_ai_provider=settings.fallback_ai_provider,
    )

    # ── Infrastructure ────────────────────────────────────────────
    mantota_client = MantotaClient(
        base_url=settings.mantota_api_url,
        api_key=settings.mantota_api_key,
        timeout=settings.mantota_timeout,
        retry_max=settings.mantota_retry_max,
        retry_backoff=settings.mantota_retry_backoff,
    )

    ai_gateway = create_ai_gateway(settings)

    # ── Classifieur d'intention (feature flag INTENT_CLASSIFIER) ──
    # keyword = regex (défaut V1), llm = LLM primaire + repli regex,
    # shadow = regex + vote LLM en fond (dataset de divergences).
    if settings.intent_classifier != "keyword":
        from app.core.intent import (
            LLMIntentClassifier,
            ShadowIntentClassifier,
            set_intent_classifier,
        )

        if settings.intent_classifier == "llm":
            set_intent_classifier(LLMIntentClassifier(ai_gateway))
        else:  # shadow
            set_intent_classifier(ShadowIntentClassifier(ai_gateway))
        logger.info("intent_classifier_active", mode=settings.intent_classifier)

    short_term_memory = create_short_term_memory(
        redis_url=settings.redis_url,
        ttl=settings.short_term_memory_ttl,
        max_history=settings.max_conversation_history,
        use_redis=settings.is_production,
    )

    # ── Tools (docs/tracy/04-TOOLS.md) ────────────────────────────
    tool_registry = ToolRegistry()
    tool_registry.register(SearchProductsTool(mantota_client))
    tool_registry.register(SearchCatalogTool(mantota_client))
    tool_registry.register(SearchStoreTool(mantota_client))
    tool_registry.register(CreateStoreTool(mantota_client))
    tool_registry.register(SendCatalogTool(mantota_client))
    tool_registry.register(CreateOrderTool(mantota_client))
    tool_registry.register(CancelOrderTool(mantota_client))
    tool_registry.register(CreateSupportTicketTool(mantota_client))
    tool_registry.register(CreateDisputeTool(mantota_client))
    tool_registry.register(TrackOrderTool(mantota_client))
    tool_registry.register(CreatePaymentTool(mantota_client))
    tool_registry.register(GetWalletTool(mantota_client))
    tool_registry.register(RequestWithdrawalTool(mantota_client))
    tool_registry.register(SendPaymentLinkTool(mantota_client))
    tool_registry.register(GetCampaignTool(mantota_client))
    tool_registry.register(SearchPartnerTool(mantota_client))
    tool_registry.register(SaveMemoryTool(mantota_client))
    tool_registry.register(SearchMemoryTool(mantota_client))
    tool_registry.register(UpdateMemoryTool(mantota_client))
    tool_registry.register(DeleteMemoryTool(mantota_client))
    tool_registry.register(ActivateTracySubscriptionTool(mantota_client))
    tool_registry.register(GetShopConfigTool(mantota_client))
    tool_registry.register(UpdateShopConfigTool(mantota_client))
    tool_registry.register(SearchRestaurantsTool(mantota_client))
    tool_registry.register(GetRestaurantMenuTool(mantota_client))
    tool_registry.register(CreateRestaurantOrderTool(mantota_client))
    tool_registry.register(TrackRestaurantOrderTool(mantota_client))
    tool_registry.register(GetCurrenciesTool(mantota_client))
    tool_registry.register(GetDeliveryInfoTool(mantota_client))
    tool_registry.register(SendVendorReportTool(mantota_client))
    tool_registry.register(GetVendorReportsTool(mantota_client))
    tool_registry.register(GetVendorStatsTool(mantota_client))
    tool_registry.register(ConnectVendorTool(mantota_client))
    tool_registry.register(ScheduleFollowUpTool(mantota_client))

    # ── RAG (Knowledge Retrieval) ────────────────────────────────
    # Le service d'embedding utilise la même clé OpenAI que l'AI Gateway
    if settings.openai_api_key:
        from app.rag.embeddings import EmbeddingService
        from app.rag.retriever import KnowledgeRetriever

        embedding_service = EmbeddingService(
            api_key=settings.openai_api_key,
            timeout=settings.ai_timeout,
            retry_max=settings.ai_retry_max,
        )
        knowledge_retriever = KnowledgeRetriever(
            embedding_service=embedding_service,
            mantota_client=mantota_client,
        )
        tool_registry.register(SearchKnowledgeTool(knowledge_retriever))
        logger.info("rag_tool_registered")
    else:
        logger.warning("rag_tool_skipped_no_openai_key")

    logger.info("tools_registered", tools=tool_registry.list_tools())

    # ── Agents (docs/tracy/03-AGENTS.md) ──────────────────────────
    commercial_agent = CommercialAgent(ai_gateway=ai_gateway, tool_registry=tool_registry, address_form=settings.address_form)
    negotiation_agent = NegotiationAgent(ai_gateway=ai_gateway, tool_registry=tool_registry, address_form=settings.address_form)
    catalog_agent = CatalogAgent(ai_gateway=ai_gateway, tool_registry=tool_registry, address_form=settings.address_form)
    order_agent = OrderAgent(ai_gateway=ai_gateway, tool_registry=tool_registry, address_form=settings.address_form)
    payment_agent = PaymentAgent(ai_gateway=ai_gateway, tool_registry=tool_registry, address_form=settings.address_form)
    support_agent = SupportAgent(ai_gateway=ai_gateway, tool_registry=tool_registry, address_form=settings.address_form)
    campaign_agent = CampaignAgent(ai_gateway=ai_gateway, tool_registry=tool_registry, address_form=settings.address_form)
    memory_agent = MemoryAgent(ai_gateway=ai_gateway, tool_registry=tool_registry, address_form=settings.address_form)
    restaurant_agent = RestaurantAgent(ai_gateway=ai_gateway, tool_registry=tool_registry, address_form=settings.address_form)
    logistics_agent = LogisticsAgent(ai_gateway=ai_gateway, tool_registry=tool_registry, address_form=settings.address_form)
    vendor_copilot = VendorCopilot(ai_gateway=ai_gateway, tool_registry=tool_registry, address_form=settings.address_form)

    # ── Orchestrateur (docs/tracy/02-ARCHITECTURE.md) ─────────────
    orchestrator = TracyOrchestrator(
        commercial_agent=commercial_agent,
        negotiation_agent=negotiation_agent,
        catalog_agent=catalog_agent,
        order_agent=order_agent,
        payment_agent=payment_agent,
        support_agent=support_agent,
        campaign_agent=campaign_agent,
        memory_agent=memory_agent,
        restaurant_agent=restaurant_agent,
        short_term_memory=short_term_memory,
        mantota_client=mantota_client,
        logistics_agent=logistics_agent,
        vendor_copilot=vendor_copilot,
    )

    # ── Rate limiter ──────────────────────────────────────────────
    configure_rate_limiter(settings.rate_limit_per_minute)

    # ── Stockage dans app.state pour les endpoints ────────────────
    app.state.orchestrator = orchestrator
    app.state.mantota_client = mantota_client
    app.state.tool_registry = tool_registry
    app.state.short_term_memory = short_term_memory

    logger.info("tracy_core_ready", port=settings.port)

    yield

    # ── Nettoyage ─────────────────────────────────────────────────
    await mantota_client.aclose()
    logger.info("tracy_core_stopped")


app = FastAPI(
    title="Tracy Core",
    version="0.1.0",
    description="Orchestrateur IA de Tracy — agents, tools, mémoire (docs/tracy/)",
    lifespan=lifespan,
)

# Middleware : correlation ID pour traçabilité de bout en bout
app.add_middleware(CorrelationIdMiddleware)

# Vision modules (Product Vision, Authenticity, Conformity, Shop Quality)
app.include_router(vision_router)

# Restaurant module (menu, orders, tracking)
app.include_router(restaurant_router)


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check — ne nécessite pas d'authentification."""
    return {"status": "ok", "service": "tracy-core"}


@app.get("/config")
async def config(
    _auth: None = Depends(verify_gateway_api_key),
) -> dict[str, object]:
    """Retourne la configuration actuelle de Tracy Core (read-only)."""
    settings = get_settings()
    return {
        "environment": settings.environment,
        "port": settings.port,
        "ai_provider": settings.default_ai_provider,
        "fallback_ai_provider": settings.fallback_ai_provider,
        "openai_model": settings.openai_model,
        "ollama_model": settings.ollama_model,
        "ollama_base_url": settings.ollama_base_url,
        "address_form": settings.address_form,
        "ai_temperature": settings.ai_temperature,
        "max_conversation_history": settings.max_conversation_history,
        "rate_limit_per_minute": settings.rate_limit_per_minute,
        "mantota_api_url": settings.mantota_api_url,
        "short_term_memory_ttl": settings.short_term_memory_ttl,
        "tools_registered": app.state.tool_registry.list_tools(),
    }


@app.post("/chat", response_model=TracyReply)
async def chat(
    message: IncomingMessage,
    _auth: None = Depends(verify_gateway_api_key),
    _rate: None = Depends(check_rate_limit),
) -> TracyReply:
    """Endpoint principal : reçoit un message et retourne la réponse de Tracy.

    Flux (docs/tracy/02-ARCHITECTURE.md §Exemple de bout en bout) :
    1. Gateway authentifie la requête.
    2. Tracy Core charge le contexte et lance le graphe LangGraph.
    3. Le graphe sélectionne l'agent pertinent.
    4. L'agent appelle les Tools nécessaires (via Mantota).
    5. La réponse remonte jusqu'au client.
    """
    orchestrator: TracyOrchestrator = app.state.orchestrator
    return await orchestrator.handle_message(message)
