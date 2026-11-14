"""LogisticsAgent — Livraison : « tu livres chez moi ? », zones, retrait sur place.

Rôle : répondre honnêtement sur la COUVERTURE de livraison d'une boutique vers la
ville du client (données Mantota : mode de livraison, villes, quartiers, retrait).

Outils autorisés : get_delivery_info.

Limites : Mantota ne fournit ni frais ni délai par zone. L'agent ne les invente
jamais : il indique que le vendeur les confirme à la commande.

Autonomie V1 : conversation_only (aucune action, lecture seule).
"""

from __future__ import annotations

from app.agents.base import AgentAutonomy, AgentInput, AgentOutput, BaseAgent
from app.agents.location import extract_city, extract_city_after_preposition
from app.ai_gateway.base import ChatMessage
from app.logging_config import bind_context, get_logger
from app.tools.base import ToolContext

logger = get_logger(__name__)

SYSTEM_PROMPT = (
    "Tu es Tracy, une vendeuse chaleureuse et honnête de Mantota. Tu réponds aux "
    "questions de livraison à partir des FAITS fournis, jamais d'après tes suppositions.\n\n"
    "RÈGLES :\n"
    "- N'invente JAMAIS un tarif, un délai ou une zone : si ce n'est pas dans les faits, "
    "dis que le vendeur le confirme à la commande.\n"
    "- Si la boutique ne livre pas chez le client, dis-le clairement et propose le retrait "
    "sur place s'il existe, sinon propose de chercher un produit équivalent plus proche.\n"
    "- Pas de liste à puces, pas de « En tant que IA ». 2 à 3 phrases maximum."
)


class LogisticsAgent(BaseAgent):
    """Couverture de livraison d'une boutique vers la ville du client."""

    @property
    def name(self) -> str:
        return "LogisticsAgent"

    @property
    def autonomy(self) -> AgentAutonomy:
        return "conversation_only"

    @property
    def _raw_system_prompt(self) -> str:
        return SYSTEM_PROMPT

    @staticmethod
    def _resolve_store(input_data: AgentInput) -> str | None:
        conv = input_data.conversation_context
        if conv is not None and conv.product_store_id:
            return str(conv.product_store_id)
        if input_data.store_id and input_data.store_id != "public":
            return input_data.store_id
        if conv is not None and conv.last_cards:
            return str(conv.last_cards[0].store_id)
        return None

    async def handle(self, input_data: AgentInput) -> AgentOutput:
        bind_context(agent=self.name)
        logger.info(
            "agent_handling_message",
            agent=self.name,
            store_id=input_data.store_id,
            correlation_id=input_data.correlation_id,
        )

        ctx = ToolContext(
            agent_name=self.name,
            correlation_id=input_data.correlation_id,
            store_id=input_data.store_id,
        )

        city = (
            extract_city_after_preposition(input_data.message)
            or extract_city(input_data.message)
            or input_data.user_city
        )
        store_id = self._resolve_store(input_data)

        if store_id is None:
            reply = await self._call_ai([
                ChatMessage(role="system", content=self.system_prompt),
                ChatMessage(
                    role="user",
                    content=(
                        f"Message du client : {input_data.message}\n\n"
                        "Le client pose une question de livraison mais aucun produit n'est "
                        "sélectionné. Demande-lui de quel produit ou boutique il parle."
                    ),
                ),
            ], max_tokens=150)
            return AgentOutput(reply=self._polish_text(reply), handled=True, tools_used=[])

        result = await self._tool_registry.execute(
            "get_delivery_info", ctx, store_id=store_id, city=city,
        )

        if not result.success or result.data is None:
            reply = await self._call_ai([
                ChatMessage(role="system", content=self.system_prompt),
                ChatMessage(
                    role="user",
                    content=(
                        f"Message du client : {input_data.message}\n\n"
                        "Les informations de livraison de cette boutique sont indisponibles. "
                        "Dis-le honnêtement et propose de demander au vendeur."
                    ),
                ),
            ], max_tokens=150)
            return AgentOutput(
                reply=self._polish_text(reply), handled=True, tools_used=["get_delivery_info"],
            )

        info = result.data
        facts = [
            f"Mode de livraison de la boutique : {info.delivery_mode}",
            f"Retrait sur place possible : {'oui' if info.pickup_available else 'non'}",
        ]
        if info.shop_address:
            facts.append(f"Adresse de la boutique : {info.shop_address}")
        if info.delivery_cities:
            facts.append("Villes desservies : " + ", ".join(info.delivery_cities))
        if info.city is None:
            facts.append("Ville du client : INCONNUE (demande-la avant de conclure)")
        elif info.covers_city:
            zones = f" (quartiers : {', '.join(info.quartiers_in_city)})" if info.quartiers_in_city else ""
            facts.append(f"Livraison vers {info.city} : OUI{zones}")
        else:
            facts.append(f"Livraison vers {info.city} : NON")
        facts.append("Frais et délais : non disponibles, confirmés par le vendeur à la commande")

        reply = await self._call_ai([
            ChatMessage(role="system", content=self.system_prompt),
            ChatMessage(
                role="user",
                content=(
                    f"Message du client : {input_data.message}\n\nFAITS :\n- "
                    + "\n- ".join(facts)
                ),
            ),
        ], max_tokens=200)

        return AgentOutput(
            reply=self._polish_text(reply), handled=True, tools_used=["get_delivery_info"],
        )

    @staticmethod
    def _polish_text(text: str) -> str:
        return text.strip()
