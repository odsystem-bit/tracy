"""SupportAgent (docs/tracy/03-AGENTS.md).

Rôle : Assistant après-vente.
Responsabilité : Traiter les réclamations, répondre aux questions après achat,
escalader les cas complexes.

Outils autorisés : track_order, get_wallet, cancel_order.

Limites : ne décide jamais seul d'un remboursement ; propose et transmet pour
validation. Peut annuler une commande à la demande explicite du client, jamais
de sa propre initiative.

Autonomie V1 : Autonome pour répondre, jamais pour rembourser.

Comportement IA (docs/tracy/05-AI_BEHAVIOR.md §14) :
- Écoute, reformule la plainte pour montrer qu'elle a compris.
- Vérifie le statut réel via Mantota avant de répondre.
- Propose une solution concrète ou escalade vers un humain.
- Ne promet jamais un remboursement qu'elle ne peut garantir.
"""

from __future__ import annotations

import re

from app.agents.base import AgentAutonomy, AgentInput, AgentOutput, BaseAgent
from app.agents.order_flow import extract_order_reference
from app.ai_gateway.base import ChatMessage
from app.logging_config import bind_context, get_logger
from app.tools.base import ToolContext

logger = get_logger(__name__)

SYSTEM_PROMPT = (
    "Tu es Tracy, une employée IA chaleureuse et honnête. Tu gères le support "
    "après-vente : réclamations, questions sur les commandes, escalades. "
    "Tu es une commerciale expérimentée, pas un chatbot.\n\n"
    "VOCABULAIRE INTERDIT :\n"
    "- « En tant que IA… », « Je suis un modèle de langage… »\n"
    "- « Je suis vraiment vraiment désolé » (excuses excessives)\n"
    "- « Bien sûr ! » en début de phrase\n"
    "- Listes à puces dans tes réponses\n"
    "- « Je vais vous mettre en relation avec un agent humain. Veuillez patienter. »\n\n"
    "RÈGLES DE SUPPORT :\n"
    "- Reformule la plainte du client pour montrer que tu as compris.\n"
    "- Vérifie toujours le statut réel de la commande avant de répondre.\n"
    "- Propose une solution concrète (suivi, échange) si elle est disponible.\n"
    "- Ne promets jamais un remboursement que tu ne peux pas garantir.\n"
    "- Si le cas dépasse tes limites, propose une escalade vers un humain de manière "
    "transparente et rassurante : explique pourquoi, rassure sur la continuité.\n"
    "- Reste calme et empathique face à un client mécontent.\n"
    "- Une seule expression d'empathie suffit, puis passe à la solution.\n"
    "- Face à un client agressif, ne t'excuse pas — écoute, reformule, propose.\n"
    "- N'invente jamais une information (statut, délai, remboursement).\n"
    "- Réponds en français, de façon concise et naturelle (max 3-4 phrases)."
)


class SupportAgent(BaseAgent):
    """Assistant après-vente."""

    @property
    def name(self) -> str:
        return "SupportAgent"

    @property
    def autonomy(self) -> AgentAutonomy:
        return "conversation_only"

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

        # Chat public : support possible (tickets guest + suivi par lien magique)
        if input_data.store_id == "public":
            history_context = ""
            if input_data.conversation_history:
                history_context = "\n\nHistorique récent :\n" + "\n".join(
                    f"  - {msg}" for msg in input_data.conversation_history[-5:]
                )
            message_lower_pub = input_data.message.lower()
            ctx_data = input_data.conversation_context

            # ── Commande créée dans la conversation : le suivi passe par le lien magique ──
            # NB : une plainte ou une annulation qui mentionne "commande" ne doit PAS
            # tomber ici — elle ira créer un ticket ou déclencher l'annulation.
            _is_complaint_or_cancel = bool(re.search(
                r"probl[eè]me|plainte|r[ée]clam|annul|supprim|plus besoin|"
                r"pas.*conforme|non.*conforme|litige|d[ée]f[ée]ct|cass|ab[îi]m|"
                r"pas.*ce.*que|erreur|arnaque|rembour|veux.*plus|veut.*plus",
                message_lower_pub,
            ))
            if (
                ctx_data and ctx_data.order_id
                and not _is_complaint_or_cancel
                and any(
                    w in message_lower_pub for w in ("livr", "arriv", "commande", "colis", "suiv", "où")
                )
            ):
                tracking_info = (
                    f"Référence : {ctx_data.order_reference or ctx_data.order_id}"
                )
                if ctx_data.order_tracking_url:
                    tracking_info += f"\nLien de suivi : {ctx_data.order_tracking_url}"
                reply = await self._call_ai([
                    ChatMessage(role="system", content=self.system_prompt),
                    ChatMessage(
                        role="user",
                        content=(
                            f"Message du client : {input_data.message}\n\n"
                            f"Une commande existe dans cette conversation :\n{tracking_info}\n\n"
                            "Donne au client son lien de suivi et rassure-le. "
                            "Réponds en 1-2 phrases avec empathie."
                            f"{history_context}"
                        ),
                    ),
                ])
                return AgentOutput(reply=reply, handled=True, tools_used=[])

            # ── Escalade humaine ou réclamation : créer un vrai ticket guest ──
            wants_human = any(
                p in message_lower_pub
                for p in ("humain", "agent", "vrai personne", "quelqu'un", "quelquun")
            ) or bool(re.search(
                r"contacter.*(?:support|quelqu|service|agent|vendeur)|"
                r"(?:support|service|vendeur).*(?:pour moi|m[' ']aider|m[' ']aide)|"
                r"parler.*[àa].*(?:quelqu|agent|personne|support|vendeur)|"
                r"mettre.*en.*(?:relation|contact)|joindre.*(?:support|quelqu|vendeur)",
                message_lower_pub,
            ))
            has_complaint = any(
                w in message_lower_pub
                for w in ("signaler", "réclamation", "reclamation", "plainte", "arnaque", "escroquerie", "problème", "probleme", "litige")
            )
            if wants_human or has_complaint:
                subject = input_data.message[:80] + "..." if len(input_data.message) > 80 else input_data.message
                category = "signalement"
                ticket_result = await self._tool_registry.execute(
                    "create_support_ticket",
                    ctx,
                    subject=subject,
                    category=category,
                    message=input_data.message,
                    customer_id=input_data.customer_id,
                )
                if ticket_result.success:
                    data = ticket_result.data  # type: ignore[union-attr]
                    return AgentOutput(
                        reply=(
                            "C'est noté, notre équipe va s'en occuper rapidement. "
                            f"Ton code de suivi est {data.get('reference_code')} — "
                            "garde-le pour suivre ta demande sur mantota.com/support/track."
                        ),
                        handled=True,
                        tools_used=["create_support_ticket"],
                    )
                reply = await self._call_ai([
                    ChatMessage(role="system", content=self.system_prompt),
                    ChatMessage(
                        role="user",
                        content=(
                            f"Message du client : {input_data.message}\n\n"
                            "Le client a un problème mais le ticket n'a pas pu être créé. "
                            "Dis-lui qu'il peut créer sa demande directement sur mantota.com/support "
                            "ou réessayer dans un moment. Reste empathique (1-2 phrases)."
                            f"{history_context}"
                        ),
                    ),
                ])
                return AgentOutput(reply=reply, handled=True, tools_used=["create_support_ticket"])

            # ── Produit non conforme / litige : référence du message ou du contexte ──
            # "le produit n'est pas conforme à ce que j'ai demandé" après CMD-XXXX
            conformity_words = (
                "conforme", "défaut", "defaut", "mauvais", "faux", "contrefa",
                "erreur", "échang", "echang", "cass", "abim", "abîm",
                "pas ce que", "pas ce qu'on", "different", "différent",
            )
            order_ref_pub = extract_order_reference(input_data.message)
            if not order_ref_pub and ctx_data and ctx_data.order_reference:
                order_ref_pub = ctx_data.order_reference
            if order_ref_pub and any(w in message_lower_pub for w in conformity_words):
                dispute_result = await self._tool_registry.execute(
                    "create_dispute",
                    ctx,
                    order_reference=order_ref_pub,
                    reason=input_data.message,
                    customer_id=input_data.customer_id,
                )
                if dispute_result.success:
                    data = dispute_result.data  # type: ignore[union-attr]
                    return AgentOutput(
                        reply=(
                            "Je suis désolée pour ça, j'ai ouvert un litige pour ta commande "
                            f"{order_ref_pub} (réf. #{data.get('dispute_id')}). "
                            "Notre équipe examine ça rapidement et te recontacte."
                        ),
                        handled=True,
                        tools_used=["create_dispute"],
                    )
                reply = await self._call_ai([
                    ChatMessage(role="system", content=self.system_prompt),
                    ChatMessage(
                        role="user",
                        content=(
                            f"Message du client : {input_data.message}\n\n"
                            f"Le client signale un problème de conformité sur sa commande {order_ref_pub} "
                            "mais le litige n'a pas pu être créé. "
                            "Rassure-le et dis-lui que le support va traiter sa demande (1-2 phrases)."
                            f"{history_context}"
                        ),
                    ),
                ])
                return AgentOutput(reply=reply, handled=True, tools_used=["create_dispute"])

            # ── Autre demande support : écouter et orienter honnêtement ──
            kb_context = await self._knowledge_context(ctx, input_data.message)
            reply = await self._call_ai([
                ChatMessage(
                    role="system",
                    content=(
                        "Tu es Tracy, une vendeuse de l'équipe Mantota. "
                        "Le client est sur le site public de Mantota. "
                        "Sur le site, le client PEUT : suivre sa commande avec son lien de suivi "
                        "(reçu à la commande), créer un ticket support sur mantota.com/support, "
                        "et suivre son ticket sur mantota.com/support/track. "
                        "Si le client a perdu son lien de suivi, demande-lui la référence de sa commande (CMD-XXXX). "
                        "Réponds en 1 ou 2 phrases maximum, chaleureuse et empathique. "
                        f"{self._raw_system_prompt}"
                    ),
                ),
                ChatMessage(
                    role="user",
                    content=(
                        f"Message du client : {input_data.message}"
                        f"{history_context}"
                        + (f"\n\n{kb_context}" if kb_context else "")
                    ),
                ),
            ])
            return AgentOutput(
                reply=reply, handled=True,
                tools_used=["search_knowledge"] if kb_context else [],
            )

        message_lower = input_data.message.lower()
        tools_used: list[str] = []

        # Détection : demande de parler à un humain
        if any(p in message_lower for p in ("humain", "agent", "vrai personne", "quelqu'un", "quelquun", "support humain")):
            # Crée un ticket support pour escalade
            ticket_result = await self._tool_registry.execute(
                "create_support_ticket",
                ctx,
                subject="Demande d'escalade humaine",
                category="signalement",
                message=input_data.message,
                customer_id=input_data.customer_id,
            )
            tools_used.append("create_support_ticket")
            reply = await self._call_ai([
                ChatMessage(role="system", content=self.system_prompt),
                ChatMessage(
                    role="user",
                    content=(
                        f"Message du client : {input_data.message}\n\n"
                        "Le client demande à parler à un humain. "
                        "Présente tes excuses pour le désagrément, dis-lui que tu as transmis sa demande "
                        "à l'équipe support qui le recontactera. Reste empathique et concise (1-2 phrases)."
                    ),
                ),
            ])
            return AgentOutput(reply=reply, handled=True, tools_used=tools_used)

        # Détection : création d'un litige
        if any(word in message_lower for word in ("litige", "dispute", "arnaque", "escroquerie")):
            order_match = re.search(r"(?:cmd|order)[-_]?(\w+)", input_data.message, re.IGNORECASE)
            if not order_match:
                reply = await self._call_ai([
                    ChatMessage(role="system", content=self.system_prompt),
                    ChatMessage(
                        role="user",
                        content=(
                            f"Message du client : {input_data.message}\n\n"
                            "Le client veut ouvrir un litige. Demande-lui la référence de sa commande (ex: CMD-XXXX)."
                        ),
                    ),
                ])
                return AgentOutput(reply=reply, handled=True, tools_used=tools_used)

            order_reference = f"CMD-{order_match.group(1).upper()}" if not order_match.group(1).upper().startswith("CMD") else order_match.group(1).upper()
            dispute_result = await self._tool_registry.execute(
                "create_dispute",
                ctx,
                order_reference=order_reference,
                reason=input_data.message,
                customer_id=input_data.customer_id,
            )
            tools_used.append("create_dispute")

            if dispute_result.success:
                data = dispute_result.data  # type: ignore[union-attr]
                return AgentOutput(
                    reply=(
                        "Le litige est ouvert. Notre équipe va examiner ça rapidement. "
                        f"Référence du litige : #{data.get('dispute_id')}. "
                        "Tu peux suivre l'évolution sur l'app Mantota."
                    ),
                    handled=True,
                    tools_used=tools_used,
                )

            return AgentOutput(
                reply=(
                    "Je n'ai pas trouvé cette commande. Vérifie la référence "
                    "ou contacte le support directement."
                ),
                handled=True,
                tools_used=tools_used,
            )

        # Détection : création d'un ticket support
        if any(word in message_lower for word in ("signaler", "support", "contacter", "contact", "réclamation", "plainte", "problème", "aide")):
            # Déterminer la catégorie
            category = "autre"
            if any(w in message_lower for w in ("bug", "bugue", "marche pas")):
                category = "bug"
            elif any(w in message_lower for w in ("pay", "paiement", "moneroo", "retrait", "argent")):
                category = "paiement"
            elif any(w in message_lower for w in ("litige", "arnaque", "escroquerie")):
                category = "litige"
            elif any(w in message_lower for w in ("signaler", "signalement")):
                category = "signalement"
            elif any(w in message_lower for w in ("question", "aide")):
                category = "question"

            subject = input_data.message[:80] + "..." if len(input_data.message) > 80 else input_data.message
            ticket_result = await self._tool_registry.execute(
                "create_support_ticket",
                ctx,
                subject=subject,
                category=category,
                message=input_data.message,
                customer_id=input_data.customer_id,
            )
            tools_used.append("create_support_ticket")

            if ticket_result.success:
                data = ticket_result.data  # type: ignore[union-attr]
                return AgentOutput(
                    reply=(
                        "C'est noté. Notre équipe va te répondre dès que possible. "
                        f"Ton code de suivi est {data.get('reference_code')}. "
                        "Conserve-le pour suivre sur /support/track."
                    ),
                    handled=True,
                    tools_used=tools_used,
                )

            return AgentOutput(
                reply="Désolée, je n'ai pas pu créer le ticket. Tu peux réessayer dans un moment.",
                handled=True,
                tools_used=tools_used,
            )

        # Détection : suivi de commande (réclamation sur livraison)
        if any(word in message_lower for word in ("livr", "arriv", "commande", "colis", "pas reçu", "jamais")):
            # Suivi de commande — extraire la référence (CMD-XXXX ou order_XXX)
            order_ref = extract_order_reference(input_data.message)
            if not order_ref:
                reply = await self._call_ai([
                    ChatMessage(role="system", content=self.system_prompt),
                    ChatMessage(
                        role="user",
                        content=(
                            f"Message du client : {input_data.message}\n\n"
                            "Le client a un problème avec sa commande mais n'a pas "
                            "fourni l'identifiant. Demande-le lui avec empathie."
                        ),
                    ),
                ])
                return AgentOutput(reply=reply, handled=True, tools_used=tools_used)

            track_result = await self._tool_registry.execute(
                "track_order",
                ctx,
                order_id=order_ref,
            )
            tools_used.append("track_order")

            if track_result.success:
                tracking = track_result.data  # type: ignore[union-attr]
                history_summary = "\n".join(
                    f"  - {h.statut} ({h.date})" for h in tracking.historique
                ) or "Aucun historique disponible"

                reply = await self._call_ai([
                    ChatMessage(role="system", content=self.system_prompt),
                    ChatMessage(
                        role="user",
                        content=(
                            f"Message du client : {input_data.message}\n\n"
                            f"Statut de la commande : {tracking.statut}\n"
                            f"Historique :\n{history_summary}\n"
                            f"Date estimée de livraison : {tracking.date_estimee_livraison or 'Non communiquée'}\n\n"
                            "Le client a un problème avec sa commande. Réponds avec "
                            "empathie, reformule sa plainte, et propose une solution "
                            "concrète basée sur le statut réel. Si le cas nécessite "
                            "une escalade, informe-le transparentment."
                        ),
                    ),
                ])
                return AgentOutput(reply=reply, handled=True, tools_used=tools_used)

        # Détection : remboursement
        if any(word in message_lower for word in ("rembours", "rembourser", "argent", "recuperer")):
            reply = await self._call_ai([
                ChatMessage(role="system", content=self.system_prompt),
                ChatMessage(
                    role="user",
                    content=(
                        f"Message du client : {input_data.message}\n\n"
                        "Le client demande un remboursement. Écoute sa demande avec "
                        "empathie, reformule-la, mais ne promets jamais un remboursement "
                        "que tu ne peux pas garantir. Explique que la demande sera "
                        "transmise pour validation. Propose une escalade vers un humain "
                        "si nécessaire."
                    ),
                ),
            ])
            return AgentOutput(reply=reply, handled=True, tools_used=tools_used)

        # Réclamation générale
        kb_context = await self._knowledge_context(ctx, input_data.message)
        if kb_context:
            tools_used.append("search_knowledge")
        reply = await self._call_ai([
            ChatMessage(role="system", content=self.system_prompt),
            ChatMessage(
                role="user",
                content=(
                    f"Message du client : {input_data.message}\n\n"
                    "Le client a une réclamation ou une question après achat. "
                    "Écoute avec empathie, reformule sa demande, et propose une "
                    "solution ou une escalade si nécessaire."
                    + (f"\n\n{kb_context}" if kb_context else "")
                ),
            ),
        ])

        logger.info(
            "agent_reply_generated",
            agent=self.name,
            correlation_id=input_data.correlation_id,
        )

        return AgentOutput(reply=reply, handled=True, tools_used=tools_used)
