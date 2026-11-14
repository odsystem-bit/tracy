"""NegotiationAgent (docs/tracy/03-AGENTS.md).

Rôle : Gère les demandes de réduction ou de négociation de prix.
Responsabilité : Évaluer une demande de rabais selon les règles définies par
le vendeur (marge minimale, promotions actives) et proposer une contre-offre.

Outils autorisés : search_catalog, get_campaign.

Limites : ne peut jamais accorder une réduction en dehors des marges autorisées
par le vendeur ; aucune remise n'est appliquée sans validation Mantota.

Autonomie V1 : Autonome dans la marge définie par le vendeur uniquement.

Comportement IA (docs/tracy/05-AI_BEHAVIOR.md §4) :
- Valorise le produit avant de discuter du prix.
- Accueille la demande sans se braquer.
- Propose une contre-offre réaliste plutôt qu'un refus sec.
- Explique la raison si elle ne peut pas descendre plus bas.
- Propose des alternatives : quantité, produit similaire, offre groupée.
- Ne négocie jamais deux fois la même remise pour la même commande.
"""

from __future__ import annotations

from app.agents.base import AgentAutonomy, AgentInput, AgentOutput, BaseAgent
from app.ai_gateway.base import ChatMessage
from app.logging_config import bind_context, get_logger
from app.negotiation.engine import Decision, Rules, asks_last_price, decide, parse_offer
from app.negotiation.reporting import (
    negotiation_summary,
    schedule_client_followup,
    send_vendor_report,
)
from app.tools.base import ToolContext

logger = get_logger(__name__)

SYSTEM_PROMPT = (
    "Tu es Tracy, une employée IA chaleureuse et honnête. Tu es une commerciale "
    "expérimentée qui négocie comme un bon commerçant : ferme mais respectueuse. "
    "Tu n'es pas un chatbot.\n\n"
    "VOCABULAIRE INTERDIT :\n"
    "- « En tant que IA… », « Je suis un modèle de langage… »\n"
    "- « Bien sûr ! » en début de phrase\n"
    "- « N'hésitez pas à me contacter »\n"
    "- Listes à puces dans tes réponses\n\n"
    "RÈGLES DE NÉGOCIATION :\n"
    "- Valorise le produit avant de discuter du prix.\n"
    "- Accueille la demande de réduction sans te braquer.\n"
    "- Vérifie si une marge de négociation existe (via les données fournies).\n"
    "- Propose une contre-offre réaliste plutôt qu'un refus sec.\n"
    "- Explique la raison si tu ne peux pas descendre plus bas (coût, qualité, quantité).\n"
    "- Propose des alternatives : quantité plus importante, produit similaire, offre groupée.\n"
    "- N'accorde jamais une réduction en dehors des marges autorisées par le vendeur.\n"
    "- Ne négocie jamais deux fois la même remise pour la même commande.\n"
    "- Face à une objection, reformule d'abord, puis réponds avec des faits.\n"
    "- Accepte le refus final du client sans insister.\n"
    "- N'invente jamais une information (prix, marge, stock).\n"
    "- Réponds en français, de façon concise et naturelle (max 3-4 phrases)."
)


class NegotiationAgent(BaseAgent):
    """Gère les demandes de négociation de prix."""

    @property
    def name(self) -> str:
        return "NegotiationAgent"

    @property
    def autonomy(self) -> AgentAutonomy:
        return "within_margin"

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

        # Chat public : pas de négociation possible
        if input_data.store_id == "public":
            history_context = ""
            if input_data.conversation_history:
                history_context = "\n\nHistorique récent :\n" + "\n".join(
                    f"  - {msg}" for msg in input_data.conversation_history[-5:]
                )

            # Chercher de VRAIES alternatives si un produit est en contexte
            # (sinon GPT inventerait des produits qui n'existent pas)
            ctx_data = input_data.conversation_context
            alternatives_info = ""
            tools_used_public: list[str] = []
            if ctx_data and ctx_data.product_mentioned:
                search_result = await self._tool_registry.execute(
                    "search_products",
                    ctx,
                    query=ctx_data.product_mentioned,
                    store_id=None,
                    limit=5,
                )
                tools_used_public.append("search_products")
                if search_result.success and search_result.data.products:
                    products_summary = "\n".join(
                        f"- {p.nom} : {p.prix:.0f} FCFA (stock: {p.stock})"
                        for p in search_result.data.products[:5]
                    )
                    alternatives_info = (
                        f"\n\nProduits réellement disponibles (source officielle) :\n{products_summary}\n"
                        "Tu ne peux proposer QUE ces produits. N'invente aucun autre produit."
                    )
                else:
                    alternatives_info = (
                        "\n\nAucune alternative trouvée dans les boutiques. "
                        "Ne propose AUCUN produit précis : demande au client s'il veut chercher autre chose."
                    )
            else:
                alternatives_info = (
                    "\n\nAucun produit en contexte. Ne propose AUCUN produit précis : "
                    "demande au client quel produit l'intéresse pour vérifier ce qui est disponible."
                )

            reply = await self._call_ai([
                ChatMessage(
                    role="system",
                    content=(
                        "Tu es Tracy, une vendeuse de l'équipe Mantota. "
                        "Le client est sur le site public de Mantota. "
                        "Sur le site public, on discute des produits. Si le client trouve un produit trop cher, "
                        "propose-lui des alternatives moins chères parmi les produits réellement disponibles. "
                        "Les prix sont fixes sur le site, mais tu peux l'aider à trouver un meilleur rapport qualité-prix. "
                        "Réponds en 1 ou 2 phrases maximum, chaleureuse et directe. "
                        f"{self._raw_system_prompt}"
                    ),
                ),
                ChatMessage(
                    role="user",
                    content=(
                        f"Message du client : {input_data.message}"
                        f"{alternatives_info}"
                        f"{history_context}"
                    ),
                ),
            ])
            return AgentOutput(reply=reply, handled=True, tools_used=tools_used_public)

        tools_used: list[str] = []

        # Étape 1 : récupérer la configuration de négociation du vendeur
        config_result = await self._tool_registry.execute(
            "get_shop_config",
            ctx,
            store_id=input_data.store_id,
        )
        tools_used.append("get_shop_config")

        config_context = ""
        if config_result.success and config_result.data:
            cfg = config_result.data
            config_context = (
                f"\n\nRÈGLES DU VENDEUR :\n"
                f"- Marge minimale : {cfg.min_margin_percent}%\n"
                f"- Réduction max autorisée : {cfg.max_discount_percent}%\n"
                f"- Réduction auto-acceptée (sans validation) : jusqu'à {cfg.auto_accept_below}%\n"
                f"- Réduction premier achat : {cfg.first_order_discount_percent}%\n"
                f"- Livraison gratuite à partir de : {cfg.free_shipping_threshold or 'non défini'}\n"
                f"- Devise : {cfg.currency}\n"
            )
            if cfg.custom_rules:
                config_context += f"- Règles personnalisées : {cfg.custom_rules}\n"
        else:
            config_context = (
                "\n\nRÈGLES DU VENDEUR : non disponibles. "
                "Utilise une marge par défaut prudente (max 5% de réduction).\n"
            )

        # Étape 2 : récupérer le catalogue pour connaître les prix
        catalog_result = await self._tool_registry.execute(
            "search_catalog",
            ctx,
            store_id=input_data.store_id,
        )
        tools_used.append("search_catalog")

        if not catalog_result.success:
            logger.info(
                "agent_catalog_unavailable",
                agent=self.name,
                correlation_id=input_data.correlation_id,
                error_code=catalog_result.error.code if catalog_result.error else None,
            )
            reply = await self._call_ai([
                ChatMessage(role="system", content=self.system_prompt),
                ChatMessage(
                    role="user",
                    content=(
                        f"Message du client : {input_data.message}\n\n"
                        "Le catalogue n'est pas accessible pour le moment. "
                        "Informe le client que tu ne peux pas négocier actuellement "
                        "et propose de revenir vers lui dès que possible."
                    ),
                ),
            ])
            return AgentOutput(reply=reply, handled=True, tools_used=tools_used)

        catalog = catalog_result.data  # type: ignore[union-attr]
        products_summary = "\n".join(
            f"- {p.nom} : {p.prix:.0f} FCFA (stock: {p.stock})"
            for p in catalog.products[:10]
        )

        # Étape 3 : décision de prix déterministe (le LLM ne fait que la formuler)
        decision = self._decide_price(input_data, catalog.products, config_result)
        if decision is not None:
            if decision.action in ("final", "accept") and input_data.conversation_context:
                conv = input_data.conversation_context
                kind, summary = negotiation_summary(conv, decision)
                phone = input_data.customer_id if (input_data.customer_id or "").lstrip("+").isdigit() else None
                if await send_vendor_report(
                    self._tool_registry, ctx, conv, input_data.store_id, kind, summary,
                    customer_phone=phone,
                ):
                    tools_used.append("send_vendor_report")
            # Négociation ouverte (offre émise, pas encore d'accord) : relance 2h au cas
            # où le client disparaît — WhatsApp pour les clients wa_*, notification in-app
            # sinon. Jamais bloquant, dédup gérée côté Laravel.
            if (
                not decision.accepted
                and decision.action in ("counter", "final")
                and input_data.conversation_context is not None
            ):
                if await schedule_client_followup(
                    self._tool_registry,
                    ctx,
                    input_data.conversation_context,
                    input_data.store_id,
                    input_data.customer_id,
                    input_data.conversation_id,
                ):
                    tools_used.append("schedule_follow_up")
            reply = await self._call_ai([
                ChatMessage(role="system", content=self.system_prompt),
                ChatMessage(
                    role="user",
                    content=(
                        f"Message du client : {input_data.message}\n\n"
                        f"{self._directive(decision, input_data)}"
                    ),
                ),
            ])
            return AgentOutput(reply=reply, handled=True, tools_used=tools_used)

        # Pas de produit identifié : génération libre mais encadrée
        reply = await self._call_ai([
            ChatMessage(role="system", content=self.system_prompt),
            ChatMessage(
                role="user",
                content=(
                    f"Message du client : {input_data.message}\n\n"
                    f"Catalogue de la boutique :\n{products_summary}"
                    f"{config_context}\n"
                    "Respecte STRICTEMENT les règles du vendeur. Tu ne peux PAS "
                    "accorder une remise supérieure à max_discount_percent. "
                    "Si la demande est <= auto_accept_below, accepte directement. "
                    "Si la demande dépasse les marges, propose une contre-offre "
                    "au maximum autorisé ou explique pourquoi tu ne peux pas descendre."
                ),
            ),
        ])

        logger.info(
            "agent_reply_generated",
            agent=self.name,
            correlation_id=input_data.correlation_id,
        )

        return AgentOutput(reply=reply, handled=True, tools_used=tools_used)

    @staticmethod
    def _decide_price(input_data: AgentInput, products: list, config_result) -> Decision | None:
        conv = input_data.conversation_context
        if conv is None or not config_result.success or not config_result.data:
            return None

        price = conv.product_price
        product_id = conv.product_id
        if not price:
            name = (conv.product_mentioned or "").lower()
            match = next((p for p in products if name and name in p.nom.lower()), None)
            if match is None and len(products) == 1:
                match = products[0]
            if match is None:
                return None
            price, product_id = match.prix, str(match.id)
            conv.product_id, conv.product_name, conv.product_price = product_id, match.nom, price

        if conv.negotiation_product_id != product_id:
            conv.negotiation_product_id = product_id
            conv.negotiation_rounds = 0
            conv.negotiation_last_price_asks = 0
            conv.negotiation_last_ask = None
            conv.negotiated_price = None

        cfg = config_result.data
        rules = Rules(
            max_discount_percent=float(cfg.max_discount_percent or 0),
            auto_accept_below=float(cfg.auto_accept_below or 0),
            custom_rules=cfg.custom_rules,
            free_shipping_threshold=cfg.free_shipping_threshold,
        )
        if asks_last_price(input_data.message):
            conv.negotiation_last_price_asks += 1
        decision = decide(
            float(price),
            rules,
            conv.negotiation_rounds,
            conv.negotiation_last_ask,
            parse_offer(input_data.message, float(price)),
            conv.negotiation_last_price_asks,
        )
        if decision.action != "disabled":
            conv.negotiation_rounds = decision.rounds
            conv.negotiation_last_ask = decision.price
            conv.current_task = "negotiation"
            if decision.accepted:
                conv.negotiated_price = decision.price
        return decision

    @staticmethod
    def _directive(decision: Decision, input_data: AgentInput) -> str:
        conv = input_data.conversation_context
        name = conv.product_name if conv else "le produit"
        list_price = conv.product_price if conv and conv.product_price else 0
        p = f"{decision.price:.0f} FCFA"
        common = (
            f"Produit : {name} (prix affiché {list_price:.0f} FCFA). "
            "Réponds en 2-3 phrases max, ton naturel de vendeuse, sans liste. "
            "N'annonce AUCUN autre prix que celui indiqué ci-dessous. "
            "Ne révèle jamais ta marge ni un prix plancher.\n"
        )
        directives = {
            "disabled": (
                "Le vendeur ne fait pas de remise sur ce produit. Explique poliment que le prix est fixe, "
                "valorise la qualité et propose de finaliser la commande."
            ),
            "hold": (
                f"Tu tiens ton prix actuel de {p}. Valorise le produit (qualité, utilité), "
                "dis que le prix est déjà juste et que tu as déjà fait un effort si c'est le cas, "
                "et demande quel budget le client avait en tête. "
                "N'offre AUCUNE réduction supplémentaire. Ne parle PAS de 'dernier prix'."
            ),
            "counter": (
                f"Fais une concession : propose {p} (pas moins). Dis que c'est un effort de ta part "
                "mais NE dis PAS que c'est ton dernier prix ; tu gardes encore un peu de marge de discussion. "
                "Demande si ça lui convient pour commander."
            ),
            "too_low": (
                "L'offre du client est trop basse, tu ne peux pas l'accepter. Explique-le gentiment "
                f"(qualité, coûts) et propose {p}."
            ),
            "final": (
                f"C'est ton dernier prix : {p}. Dis-le clairement et chaleureusement, sans pouvoir "
                "descendre davantage, et propose de passer commande. Accepte son refus s'il décline."
            ),
            "accept": (
                f"Tu acceptes le prix de {p}. Confirme avec enthousiasme et demande quantité et ville "
                "de livraison pour finaliser."
            ),
        }
        return common + directives[decision.action]
