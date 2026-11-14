"""Configuration partagée des tests Tracy Core.

Fixtures réutilisables :
- mantota_client : client Mantota mocké via respx
- fake_ai_gateway : AI Gateway de test qui retourne une réponse formatée
- tool_registry : registre avec tous les V1 tools
- commercial_agent, negotiation_agent, catalog_agent : agents configurés
- orchestrator : orchestrateur complet avec mémoire en RAM
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest
import respx

from app.ai_gateway.base import AIGateway, ChatMessage, ChatResponse
from app.agents.campaign_agent import CampaignAgent
from app.agents.catalog_agent import CatalogAgent
from app.agents.commercial_agent import CommercialAgent
from app.agents.memory_agent import MemoryAgent
from app.agents.negotiation_agent import NegotiationAgent
from app.agents.order_agent import OrderAgent
from app.agents.payment_agent import PaymentAgent
from app.agents.restaurant_agent import RestaurantAgent
from app.agents.support_agent import SupportAgent
from app.agents.vendor_copilot import VendorCopilot
from app.config import reset_settings_cache
from app.core.orchestrator import TracyOrchestrator
from app.logging_config import configure_logging
from app.mantota_client.client import MantotaClient
from app.mantota_client.schemas import MemoryEntry, MemorySearchResult, ShopConfig
from app.memory.short_term import InMemoryShortTermMemory
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
from app.tools.get_currencies import GetCurrenciesTool
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
from app.tools.send_catalog import SendCatalogTool
from app.tools.send_payment_link import SendPaymentLinkTool
from app.tools.track_order import TrackOrderTool
from app.tools.track_restaurant_order import TrackRestaurantOrderTool
from app.tools.get_shop_config import GetShopConfigTool
from app.tools.search_knowledge import SearchKnowledgeTool
from app.tools.update_memory import UpdateMemoryTool
from app.tools.update_shop_config import UpdateShopConfigTool
from app.tools.vendor_reports import (
    ConnectVendorTool,
    GetVendorReportsTool,
    GetVendorStatsTool,
    ScheduleFollowUpTool,
    SendVendorReportTool,
)

MANTOTA_BASE_URL = "https://mantota.test/api"


class FakeAIGateway(AIGateway):
    """AI Gateway de test : retourne une réponse basée sur le contexte fourni."""

    def __init__(self) -> None:
        self._call_count = 0

    async def complete(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> ChatResponse:
        self._call_count += 1
        user_msg = next((m for m in messages if m.role == "user"), None)
        content = f"[Réponse Tracy] {user_msg.content[:200]}" if user_msg else "[Réponse Tracy]"
        return ChatResponse(content=content, provider="fake", model="test-model")

    @property
    def call_count(self) -> int:
        return self._call_count


@pytest.fixture(autouse=True)
def setup_logging() -> None:
    configure_logging("development", "WARNING")


@pytest.fixture(autouse=True)
def reset_config() -> None:
    reset_settings_cache()


@pytest.fixture(autouse=True)
def mock_mantota_common_methods(request):
    """Patch MantotaClient methods communs (get_shop_config, search_memory, save_memory)
    pour éviter les appels HTTP non mockés dans les tests.

    Skip si le test a le marker 'skip_common_mocks' (tests qui mockent eux-mêmes
    ces endpoints via respx).
    """
    if request.node.get_closest_marker("skip_common_mocks"):
        yield
        return

    async def _fake_get_shop_config(self, store_id: str):
        return ShopConfig(
            store_id=store_id,
            min_margin_percent=10.0,
            first_order_discount_percent=0.0,
            max_discount_percent=15.0,
            free_shipping_threshold=None,
            auto_accept_below=5.0,
            custom_rules=None,
            currency="XOF",
        )

    async def _fake_search_memory(self, scope: str, entity_id: str, query: str | None = None):
        return MemorySearchResult(entries=[], total=0)

    async def _fake_save_memory(self, scope: str, entity_id: str, key: str, value: str, source: str = "inferred"):
        return MemoryEntry(id="mem_1", scope=scope, entity_id=entity_id, key=key, value=value, source=source)

    with patch.object(MantotaClient, "get_shop_config", _fake_get_shop_config), \
         patch.object(MantotaClient, "search_memory", _fake_search_memory), \
         patch.object(MantotaClient, "save_memory", _fake_save_memory):
        yield


@pytest.fixture
def mantota_client() -> MantotaClient:
    return MantotaClient(
        base_url=MANTOTA_BASE_URL,
        api_key="test-bot-key",
        retry_max=1,
        retry_backoff=0.01,
    )


@pytest.fixture
def fake_ai_gateway() -> FakeAIGateway:
    return FakeAIGateway()


@pytest.fixture
def tool_registry(mantota_client: MantotaClient) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(SearchProductsTool(mantota_client))
    registry.register(SearchCatalogTool(mantota_client))
    registry.register(SearchStoreTool(mantota_client))
    registry.register(CreateStoreTool(mantota_client))
    registry.register(SendCatalogTool(mantota_client))
    registry.register(CreateOrderTool(mantota_client))
    registry.register(CancelOrderTool(mantota_client))
    registry.register(CreateSupportTicketTool(mantota_client))
    registry.register(CreateDisputeTool(mantota_client))
    registry.register(TrackOrderTool(mantota_client))
    registry.register(CreatePaymentTool(mantota_client))
    registry.register(GetWalletTool(mantota_client))
    registry.register(RequestWithdrawalTool(mantota_client))
    registry.register(SendPaymentLinkTool(mantota_client))
    registry.register(GetCampaignTool(mantota_client))
    registry.register(SearchPartnerTool(mantota_client))
    registry.register(SaveMemoryTool(mantota_client))
    registry.register(SearchMemoryTool(mantota_client))
    registry.register(UpdateMemoryTool(mantota_client))
    registry.register(DeleteMemoryTool(mantota_client))
    registry.register(ActivateTracySubscriptionTool(mantota_client))
    registry.register(GetShopConfigTool(mantota_client))
    registry.register(UpdateShopConfigTool(mantota_client))
    registry.register(SearchRestaurantsTool(mantota_client))
    registry.register(GetRestaurantMenuTool(mantota_client))
    registry.register(CreateRestaurantOrderTool(mantota_client))
    registry.register(TrackRestaurantOrderTool(mantota_client))
    registry.register(GetCurrenciesTool(mantota_client))
    registry.register(SendVendorReportTool(mantota_client))
    registry.register(GetVendorReportsTool(mantota_client))
    registry.register(GetVendorStatsTool(mantota_client))
    registry.register(ScheduleFollowUpTool(mantota_client))
    registry.register(ConnectVendorTool(mantota_client))

    # RAG tool (avec un retriever mocké)
    from app.rag.retriever import KnowledgeRetriever
    from unittest.mock import AsyncMock
    mock_retriever = AsyncMock(spec=KnowledgeRetriever)
    mock_retriever.search_knowledge = AsyncMock(return_value=[])
    mock_retriever.format_chunks_for_prompt = lambda chunks: ""
    registry.register(SearchKnowledgeTool(mock_retriever))

    return registry


@pytest.fixture
def commercial_agent(
    fake_ai_gateway: FakeAIGateway,
    tool_registry: ToolRegistry,
) -> CommercialAgent:
    return CommercialAgent(ai_gateway=fake_ai_gateway, tool_registry=tool_registry)


@pytest.fixture
def negotiation_agent(
    fake_ai_gateway: FakeAIGateway,
    tool_registry: ToolRegistry,
) -> NegotiationAgent:
    return NegotiationAgent(ai_gateway=fake_ai_gateway, tool_registry=tool_registry)


@pytest.fixture
def catalog_agent(
    fake_ai_gateway: FakeAIGateway,
    tool_registry: ToolRegistry,
) -> CatalogAgent:
    return CatalogAgent(ai_gateway=fake_ai_gateway, tool_registry=tool_registry)


@pytest.fixture
def order_agent(
    fake_ai_gateway: FakeAIGateway,
    tool_registry: ToolRegistry,
) -> OrderAgent:
    return OrderAgent(ai_gateway=fake_ai_gateway, tool_registry=tool_registry)


@pytest.fixture
def payment_agent(
    fake_ai_gateway: FakeAIGateway,
    tool_registry: ToolRegistry,
) -> PaymentAgent:
    return PaymentAgent(ai_gateway=fake_ai_gateway, tool_registry=tool_registry)


@pytest.fixture
def support_agent(
    fake_ai_gateway: FakeAIGateway,
    tool_registry: ToolRegistry,
) -> SupportAgent:
    return SupportAgent(ai_gateway=fake_ai_gateway, tool_registry=tool_registry)


@pytest.fixture
def campaign_agent(
    fake_ai_gateway: FakeAIGateway,
    tool_registry: ToolRegistry,
) -> CampaignAgent:
    return CampaignAgent(ai_gateway=fake_ai_gateway, tool_registry=tool_registry)


@pytest.fixture
def memory_agent(
    fake_ai_gateway: FakeAIGateway,
    tool_registry: ToolRegistry,
) -> MemoryAgent:
    return MemoryAgent(ai_gateway=fake_ai_gateway, tool_registry=tool_registry)


@pytest.fixture
def short_term_memory() -> InMemoryShortTermMemory:
    return InMemoryShortTermMemory(max_history=20)


@pytest.fixture
def restaurant_agent(
    fake_ai_gateway: FakeAIGateway,
    tool_registry: ToolRegistry,
) -> RestaurantAgent:
    return RestaurantAgent(ai_gateway=fake_ai_gateway, tool_registry=tool_registry)


@pytest.fixture
def vendor_copilot(
    fake_ai_gateway: FakeAIGateway,
    tool_registry: ToolRegistry,
) -> VendorCopilot:
    return VendorCopilot(ai_gateway=fake_ai_gateway, tool_registry=tool_registry)


@pytest.fixture
def orchestrator(
    commercial_agent: CommercialAgent,
    negotiation_agent: NegotiationAgent,
    catalog_agent: CatalogAgent,
    order_agent: OrderAgent,
    payment_agent: PaymentAgent,
    support_agent: SupportAgent,
    campaign_agent: CampaignAgent,
    memory_agent: MemoryAgent,
    restaurant_agent: RestaurantAgent,
    short_term_memory: InMemoryShortTermMemory,
    mantota_client: MantotaClient,
    vendor_copilot: VendorCopilot,
) -> TracyOrchestrator:
    return TracyOrchestrator(
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
        vendor_copilot=vendor_copilot,
    )


# ── Helpers pour mock Mantota ────────────────────────────────────────


def mock_product_search_response(
    products: list[dict] | None = None,
    total: int | None = None,
) -> dict:
    if products is None:
        products = [
            {"id": "1", "nom": "Tecno Spark 10", "prix": 95000, "stock": 5, "image_url": None, "store_id": "store_1"},
            {"id": "2", "nom": "Infinix Hot 30", "prix": 90000, "stock": 3, "image_url": None, "store_id": "store_1"},
        ]
    return {"products": products, "total": total if total is not None else len(products)}


def mock_catalog_response(
    store_id: str = "store_1",
    products: list[dict] | None = None,
    categories: list[dict] | None = None,
) -> dict:
    if products is None:
        products = [
            {"id": "1", "nom": "Tecno Spark 10", "prix": 95000, "stock": 5, "image_url": None, "store_id": store_id},
        ]
    if categories is None:
        categories = [{"id": "cat1", "nom": "Téléphones", "product_count": 2}]
    return {"store_id": store_id, "categories": categories, "products": products}


def mock_store_config_response(
    store_id: str = "store_1",
    min_margin_percent: float = 10.0,
    max_discount_percent: float = 15.0,
) -> dict:
    return {
        "store_id": store_id,
        "min_margin_percent": min_margin_percent,
        "first_order_discount_percent": 0.0,
        "max_discount_percent": max_discount_percent,
        "free_shipping_threshold": None,
        "auto_accept_below": 5.0,
        "custom_rules": None,
        "currency": "XOF",
    }
