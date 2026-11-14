"""CampaignAgent (docs/tracy/03-AGENTS.md).

Rôle : Responsable des campagnes marketing et des relances.
Responsabilité : Proposer et suivre les campagnes promotionnelles, relancer
les paniers abandonnés, informer les partenaires de leurs performances.

Outils autorisés : get_campaign, search_partner, send_catalog.

Limites : ne lance jamais une campagne payante sans validation du vendeur.

Autonomie V1 : Propose, le vendeur valide avant tout envoi payant.

Comportement IA (docs/tracy/05-AI_BEHAVIOR.md §5) :
- Une relance commence toujours par une aide potentielle, jamais par une pression.
- Relance au maximum deux fois sans réponse, puis s'arrête.
- Ne relance jamais un client qui a demandé à ne plus être contacté.
"""

from __future__ import annotations

import re

from app.agents.base import AgentAutonomy, AgentInput, AgentOutput, BaseAgent
from app.ai_gateway.base import ChatMessage
from app.logging_config import bind_context, get_logger
from app.tools.base import ToolContext

logger = get_logger(__name__)

SYSTEM_PROMPT = (
    "Tu es Tracy, une employée IA chaleureuse et honnête. Tu gères les "
    "campagnes marketing, les relances et le suivi des partenaires. "
    "Tu es une commerciale expérimentée, pas un chatbot.\n\n"
    "VOCABULAIRE INTERDIT :\n"
    "- « En tant que IA… », « Je suis un modèle de langage… »\n"
    "- « Offre spéciale limitée ! Profitez-en ! » (ton agressif)\n"
    "- « Cliquez ici pour finaliser votre achat maintenant ! »\n"
    "- Listes à puces dans tes réponses\n"
    "- « Bien sûr ! » en début de phrase\n\n"
    "RÈGLES DE RELANCE :\n"
    "- Une relance commence toujours par une aide potentielle, jamais par une pression.\n"
    "- Relance au maximum deux fois sans réponse, puis s'arrête.\n"
    "- Ne relance jamais un client qui a demandé à ne plus être contacté.\n"
    "- Ne lance jamais une campagne payante sans validation explicite du vendeur.\n\n"
    "RÈGLES PARTENAIRE :\n"
    "- Communique clairement les performances et commissions.\n"
    "- Reste factuelle sur les chiffres, sans exagération.\n"
    "- Propose des actions concrètes pour améliorer les résultats.\n\n"
    "- N'invente jamais une information (statistiques, conversions, commissions).\n"
    "- Réponds en français, de façon concise et naturelle (max 3-4 phrases)."
)


class CampaignAgent(BaseAgent):
    """Responsable des campagnes marketing et des relances."""

    @property
    def name(self) -> str:
        return "CampaignAgent"

    @property
    def autonomy(self) -> AgentAutonomy:
        return "propose_only"

    @property
    def _raw_system_prompt(self) -> str:
        return SYSTEM_PROMPT

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

        message_lower = input_data.message.lower()
        tools_used: list[str] = []

        # Handler public : pas de gestion campagne sur le site public
        if input_data.store_id == "public":
            # Info partenaire/affiliation → autorisée même sur public
            if any(word in message_lower for word in ("partenaire", "parrain", "commission", "affili")):
                reply = await self._call_ai([
                    ChatMessage(role="system", content=self.system_prompt),
                    ChatMessage(
                        role="user",
                        content=(
                            f"Message du client : {input_data.message}\n\n"
                            "Le client demande des informations sur le programme partenaire/affiliation. "
                            "Explique brièvement comment devenir partenaire Mantota (via l'app), "
                            "les avantages (commissions sur les parrainages) et donne le lien vers l'app. "
                            "Reste concise (2-3 phrases)."
                        ),
                    ),
                ])
                return AgentOutput(reply=reply, handled=True, tools_used=[])

            # Tout le reste (campagnes, relances, stats) → redirige vers l'app
            reply = await self._call_ai([
                ChatMessage(role="system", content=self.system_prompt),
                ChatMessage(
                    role="user",
                    content=(
                        f"Message du vendeur : {input_data.message}\n\n"
                        "Le vendeur est sur le site public et demande une action marketing "
                        "(campagne, relance, statistiques). Dis-lui que la gestion des campagnes "
                        "se fait sur l'app Mantota dans la section Marketing. "
                        "Reste concise (1-2 phrases)."
                    ),
                ),
            ])
            return AgentOutput(reply=reply, handled=True, tools_used=[])

        # Détection : recherche partenaire
        if any(word in message_lower for word in ("partenaire", "parrain", "commission", "affili")):
            partner_result = await self._tool_registry.execute(
                "search_partner",
                ctx,
                query=input_data.message,
            )
            tools_used.append("search_partner")

            if partner_result.success:
                partner = partner_result.data  # type: ignore[union-attr]
                reply = await self._call_ai([
                    ChatMessage(role="system", content=self.system_prompt),
                    ChatMessage(
                        role="user",
                        content=(
                            f"Message du vendeur/partenaire : {input_data.message}\n\n"
                            f"Partenaire trouvé : {partner.nom}\n"
                            f"Code de parrainage : {partner.code_parrainage or 'N/A'}\n"
                            f"Commissions cumulées : {partner.commissions_cumulees:.0f} FCFA\n\n"
                            "Présente ces informations de manière claire et professionnelle. "
                            "Le partenaire peut demander un retrait de ses gains via le wallet."
                        ),
                    ),
                ])
                return AgentOutput(reply=reply, handled=True, tools_used=tools_used)

        # Détection : consultation de campagne
        if any(word in message_lower for word in ("campagne", "performance", "statistique", "résultat", "vues", "clics", "conversion")):
            # Extraire l'ID de campagne du message
            campaign_id_match = re.search(r"camp[_-](\w+)", input_data.message, re.IGNORECASE)
            if not campaign_id_match:
                reply = await self._call_ai([
                    ChatMessage(role="system", content=self.system_prompt),
                    ChatMessage(
                        role="user",
                        content=(
                            f"Message du vendeur : {input_data.message}\n\n"
                            "Le vendeur souhaite consulter une campagne mais n'a pas "
                            "fourni l'identifiant. Demande-le lui."
                        ),
                    ),
                ])
                return AgentOutput(reply=reply, handled=True, tools_used=tools_used)

            campaign_id = f"camp_{campaign_id_match.group(1)}"
            campaign_result = await self._tool_registry.execute(
                "get_campaign",
                ctx,
                campaign_id=campaign_id,
            )
            tools_used.append("get_campaign")

            if campaign_result.success:
                campaign = campaign_result.data  # type: ignore[union-attr]
                reply = await self._call_ai([
                    ChatMessage(role="system", content=self.system_prompt),
                    ChatMessage(
                        role="user",
                        content=(
                            f"Message du vendeur : {input_data.message}\n\n"
                            f"Campagne : {campaign.nom}\n"
                            f"Statut : {campaign.statut}\n"
                            f"Vues : {campaign.vues}\n"
                            f"Clics : {campaign.clics}\n"
                            f"Conversions : {campaign.conversions}\n\n"
                            "Présente ces performances de manière claire et factuelle. "
                            "Propose des actions concrètes pour les améliorer si pertinent."
                        ),
                    ),
                ])
                return AgentOutput(reply=reply, handled=True, tools_used=tools_used)

        # Détection : relance / panier abandonné
        if any(word in message_lower for word in ("relance", "panier", "abandonn", "inactif", "rappeler")):
            reply = await self._call_ai([
                ChatMessage(role="system", content=self.system_prompt),
                ChatMessage(
                    role="user",
                    content=(
                        f"Message du vendeur : {input_data.message}\n\n"
                        "Le vendeur souhaite relancer des clients (panier abandonné, "
                        "clients inactifs). Propose une stratégie de relance pertinente. "
                        "Rappelle que chaque relance doit commencer par une aide potentielle, "
                        "jamais par une pression. Le vendeur doit valider avant tout envoi."
                    ),
                ),
            ])
            return AgentOutput(reply=reply, handled=True, tools_used=tools_used)

        # Campagne générale
        reply = await self._call_ai([
            ChatMessage(role="system", content=self.system_prompt),
            ChatMessage(
                role="user",
                content=(
                    f"Message du vendeur : {input_data.message}\n\n"
                    "Le vendeur a une demande liée au marketing ou aux campagnes. "
                    "Propose une stratégie pertinente et demande validation avant "
                    "toute action payante."
                ),
            ),
        ])

        logger.info(
            "agent_reply_generated",
            agent=self.name,
            correlation_id=input_data.correlation_id,
        )

        return AgentOutput(reply=reply, handled=True, tools_used=tools_used)
