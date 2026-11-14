"""OrderAgent (docs/tracy/03-AGENTS.md).

Rôle : Responsable du cycle de vie de la commande.
Responsabilité : Créer, suivre et annuler des commandes en fonction de la
conversation.

Outils autorisés : create_order, cancel_order, track_order.

Limites : ne déclenche jamais de paiement lui-même ; délègue systématiquement
à PaymentAgent.

Autonomie V1 : Autonome pour créer/suivre, confirmation requise pour annuler.

Comportement IA (docs/tracy/05-AI_BEHAVIOR.md) :
- Chaleureuse, compétente, honnête, proactive.
- Conclut toujours par une invitation claire à l'action.
- Ne promet jamais un délai qu'elle ne peut confirmer.
"""

from __future__ import annotations

import re

from app.agents.base import AgentAutonomy, AgentInput, AgentOutput, BaseAgent
from app.agents.order_flow import (
    QuantityCity,
    apply_order_to_context,
    create_order_from_context,
    extract_order_reference,
    parse_partial_order_details,
    parse_quantity_city,
)

_CANCEL_WORDS_RE = re.compile(
    r"annul|supprim|plus\s+besoin|veux\s+plu|veut\s+plu|l[àa]che\s+tomber|"
    r"retourne\s+ta\s+commande|renvoy\w*\s+commande"
)
_CONFIRM_WORDS_RE = re.compile(
    r"\b(?:oui|ouais|ouep|ok|d['\s]?accord|vas.?y|exact|exactement|bien\s+s[ûu]r|"
    r"c['\s]?est\s+\w*a|confirm)\w*\b"
)
_TRACK_WORDS_RE = re.compile(
    r"suiv|trac|statut|o[ùu]\b|livraison|livr[ée]|livreur|colis|arriv[ée]e?|"
    r"notifi|au\s+courant|tiens\s+moi|tenez.moi"
)
from app.ai_gateway.base import ChatMessage
from app.logging_config import bind_context, get_logger
from app.tools.base import ToolContext

logger = get_logger(__name__)

SYSTEM_PROMPT = (
    "Tu es Tracy, une employée IA chaleureuse et honnête. Tu gères les "
    "commandes des clients : création, suivi et annulation. Tu es une commerciale "
    "expérimentée, pas un chatbot.\n\n"
    "VOCABULAIRE INTERDIT :\n"
    "- « En tant que IA… », « Je suis un modèle de langage… »\n"
    "- « Souhaitez-vous procéder à l'achat ? »\n"
    "- « Voulez-vous finaliser votre commande ? »\n"
    "- Listes à puces dans tes réponses\n"
    "- « Bien sûr ! » en début de phrase\n\n"
    "VOCABULAIRE PRIVILÉGIÉ :\n"
    "- « Je le mets de côté ? », « Je passe la commande ? »\n\n"
    "RÈGLES :\n"
    "- Récupère les informations manquantes (adresse, quantité) avant de créer une commande.\n"
    "- Confirme toujours les détails avec le client avant de valider.\n"
    "- Pour une annulation, demande confirmation explicite au client.\n"
    "- Ne déclenche jamais un paiement toi-même : oriente vers le paiement après création.\n"
    "- Ne promets jamais un délai que tu ne peux pas confirmer.\n"
    "- N'invente jamais une information (statut, délai, montant).\n"
    "- Réponds en français, de façon concise et naturelle (max 3-4 phrases)."
)


class OrderAgent(BaseAgent):
    """Responsable du cycle de vie de la commande."""

    @property
    def name(self) -> str:
        return "OrderAgent"

    @property
    def autonomy(self) -> AgentAutonomy:
        return "confirmation_required"

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

        # Chat public : commande et paiement possibles sur le site
        if input_data.store_id == "public":
            history_context = ""
            if input_data.conversation_history:
                history_context = "\n\nHistorique récent :\n" + "\n".join(
                    f"  - {msg}" for msg in input_data.conversation_history[-5:]
                )

            ctx_data = input_data.conversation_context
            message_lower_pub = input_data.message.lower()
            tools_used_pub: list[str] = []

            # ── Annulation : vraie exécution via cancel_order après confirmation ──
            _is_cancel = bool(_CANCEL_WORDS_RE.search(message_lower_pub))
            if _is_cancel or (
                ctx_data and ctx_data.task_state == "awaiting_cancel_confirm"
            ):
                order_ref = (
                    extract_order_reference(input_data.message)
                    or (ctx_data and ctx_data.pending_cancel_ref)
                    or (ctx_data and (ctx_data.order_reference or ctx_data.order_id))
                )
                if not order_ref:
                    reply = await self._call_ai([
                        ChatMessage(role="system", content=self.system_prompt),
                        ChatMessage(
                            role="user",
                            content=(
                                f"Message du client : {input_data.message}\n\n"
                                "Le client veut annuler une commande mais n'a pas donné sa référence. "
                                "Demande-lui la référence de la commande (format CMD-XXXX). "
                                "1 phrase courte."
                                f"{history_context}"
                            ),
                        ),
                    ])
                    return AgentOutput(reply=reply, handled=True, tools_used=[])

                if ctx_data and ctx_data.task_state == "awaiting_cancel_confirm":
                    _msg_norm = re.sub(r"[^a-zàâäéèêëîïôöùûüç' ]", " ", message_lower_pub)
                    _said_no = bool(re.search(r"\b(?:non|nan|en\s+fait\s+non)\b", _msg_norm))
                    if _CONFIRM_WORDS_RE.search(_msg_norm) and not _said_no:
                        # Confirmation reçue → annuler réellement la commande
                        cancel_result = await self._tool_registry.execute(
                            "cancel_order",
                            ctx,
                            order_id=order_ref,
                            reason=f"Annulation demandée par le client : {input_data.message[:150]}",
                        )
                        tools_used_pub.append("cancel_order")
                        if ctx_data:
                            ctx_data.task_state = None
                            ctx_data.pending_action = None
                            ctx_data.pending_cancel_ref = None
                        if cancel_result.success:
                            if ctx_data and (
                                ctx_data.order_reference == order_ref
                                or ctx_data.order_id == order_ref
                            ):
                                ctx_data.order_id = None
                                ctx_data.order_reference = None
                                ctx_data.order_payment_url = None
                                ctx_data.order_tracking_url = None
                            reply = await self._call_ai([
                                ChatMessage(role="system", content=self.system_prompt),
                                ChatMessage(
                                    role="user",
                                    content=(
                                        f"Message du client : {input_data.message}\n\n"
                                        f"La commande {order_ref} a bien été annulée. "
                                        "Annonce-le au client avec empathie en 1-2 phrases. "
                                        "Propose ton aide pour autre chose."
                                        f"{history_context}"
                                    ),
                                ),
                            ])
                            return AgentOutput(reply=reply, handled=True, tools_used=tools_used_pub)
                        reply = await self._call_ai([
                            ChatMessage(role="system", content=self.system_prompt),
                            ChatMessage(
                                role="user",
                                content=(
                                    f"Message du client : {input_data.message}\n\n"
                                    f"L'annulation de la commande {order_ref} a échoué "
                                    f"(commande introuvable ou déjà livrée/annulée). "
                                    "Explique-le honnêtement au client et propose de signaler "
                                    "le problème au support si besoin. 1-2 phrases."
                                    f"{history_context}"
                                ),
                            ),
                        ])
                        return AgentOutput(reply=reply, handled=True, tools_used=tools_used_pub)
                    if _said_no:
                        # Le client renonce à l'annulation
                        if ctx_data:
                            ctx_data.task_state = "order_created" if ctx_data.order_id else None
                            ctx_data.pending_action = None
                            ctx_data.pending_cancel_ref = None
                        reply = await self._call_ai([
                            ChatMessage(role="system", content=self.system_prompt),
                            ChatMessage(
                                role="user",
                                content=(
                                    f"Message du client : {input_data.message}\n\n"
                                    f"Le client renonce à annuler sa commande {order_ref}. "
                                    "Rassure-le en 1 phrase : la commande est conservée."
                                    f"{history_context}"
                                ),
                            ),
                        ])
                        return AgentOutput(reply=reply, handled=True, tools_used=[])
                    # Ni oui ni non → reposer la question sans boucler à l'identique
                    reply = await self._call_ai([
                        ChatMessage(role="system", content=self.system_prompt),
                        ChatMessage(
                            role="user",
                            content=(
                                f"Message du client : {input_data.message}\n\n"
                                f"Le client veut annuler la commande {order_ref} mais n'a pas "
                                "encore confirmé clairement. Demande-lui de répondre "
                                "« oui » pour confirmer l'annulation, ou « non » pour garder "
                                "sa commande. 1 phrase directe, sans te répéter."
                                f"{history_context}"
                            ),
                        ),
                    ])
                    return AgentOutput(reply=reply, handled=True, tools_used=[])

                # Première demande d'annulation → une seule demande de confirmation
                if ctx_data:
                    ctx_data.task_state = "awaiting_cancel_confirm"
                    ctx_data.pending_action = "awaiting_cancel_confirm"
                    ctx_data.pending_cancel_ref = order_ref
                reply = await self._call_ai([
                    ChatMessage(role="system", content=self.system_prompt),
                    ChatMessage(
                        role="user",
                        content=(
                            f"Message du client : {input_data.message}\n\n"
                            f"Le client demande l'annulation de la commande {order_ref}. "
                            "Confirme la référence en UNE phrase et demande une confirmation "
                            "explicite (oui/non) avant d'annuler définitivement."
                            f"{history_context}"
                        ),
                    ),
                ])
                return AgentOutput(reply=reply, handled=True, tools_used=[])

            # ── Suivi / notification livreur : réf du message ou de la conversation ──
            if _TRACK_WORDS_RE.search(message_lower_pub):
                order_ref = (
                    extract_order_reference(input_data.message)
                    or (ctx_data and (ctx_data.order_reference or ctx_data.order_id))
                )
                if not order_ref:
                    reply = await self._call_ai([
                        ChatMessage(role="system", content=self.system_prompt),
                        ChatMessage(
                            role="user",
                            content=(
                                f"Message du client : {input_data.message}\n\n"
                                "Le client souhaite suivre une commande mais n'a pas "
                                "fourni l'identifiant. Demande-le lui poliment."
                                f"{history_context}"
                            ),
                        ),
                    ])
                    return AgentOutput(reply=reply, handled=True, tools_used=[])

                track_result = await self._tool_registry.execute(
                    "track_order",
                    ctx,
                    order_id=order_ref,
                )
                tools_used_pub.append("track_order")
                tracking_link = (
                    f"\nLien de suivi : {ctx_data.order_tracking_url}"
                    if ctx_data and ctx_data.order_tracking_url
                    else ""
                )
                if not track_result.success:
                    reply = await self._call_ai([
                        ChatMessage(role="system", content=self.system_prompt),
                        ChatMessage(
                            role="user",
                            content=(
                                f"Message du client : {input_data.message}\n\n"
                                "Impossible de retrouver la commande. Demande au client "
                                "l'identifiant ou les détails de sa commande."
                                f"{history_context}"
                            ),
                        ),
                    ])
                    return AgentOutput(reply=reply, handled=True, tools_used=tools_used_pub)

                tracking = track_result.data  # type: ignore[union-attr]
                history_summary = "\n".join(
                    f"  - {h.statut} ({h.date})" for h in tracking.historique
                ) or "Aucun historique disponible"
                wants_notify = bool(re.search(r"notifi|livreur|au courant|tiens|tenez", message_lower_pub))
                notify_note = (
                    "Le client demande aussi une notification quand le livreur arrive : "
                    "dis-lui honnêtement que tu ne peux pas lui envoyer d'alerte automatique, "
                    "mais qu'il peut vérifier le statut en temps réel via le lien de suivi."
                    if wants_notify else ""
                )
                reply = await self._call_ai([
                    ChatMessage(role="system", content=self.system_prompt),
                    ChatMessage(
                        role="user",
                        content=(
                            f"Message du client : {input_data.message}\n\n"
                            f"Statut de la commande {order_ref} : {tracking.statut}\n"
                            f"Historique :\n{history_summary}\n"
                            f"Date estimée de livraison : {tracking.date_estimee_livraison or 'Non communiquée'}"
                            f"{tracking_link}\n"
                            f"{notify_note}\n"
                            "Présente ces informations de manière claire et rassurante, 2-3 phrases."
                            f"{history_context}"
                        ),
                    ),
                ])
                return AgentOutput(reply=reply, handled=True, tools_used=tools_used_pub)

            # ── Création réelle : produit en contexte + quantité + ville détectées ──
            if ctx_data and ctx_data.product_id and ctx_data.product_name:
                qty_city = parse_quantity_city(input_data.message)
                partial = None if qty_city else parse_partial_order_details(input_data.message)
                if partial is not None:
                    if partial.quantity:
                        ctx_data.pending_quantity = partial.quantity
                    if partial.city:
                        ctx_data.pending_city = partial.city
                _pq = ctx_data.pending_quantity
                _pc = ctx_data.pending_city
                if not qty_city and _pq and _pc:
                    qty_city = QuantityCity(quantity=_pq, city=_pc)

                if qty_city and qty_city.city and qty_city.quantity:
                    order = await create_order_from_context(
                        self._tool_registry, ctx, ctx_data, input_data,
                        qty_city.quantity, qty_city.city,
                    )
                    if order:
                        apply_order_to_context(ctx_data, order)
                        payment_info = ""
                        if order.payment_url:
                            payment_info = f"\n\nLien de paiement : {order.payment_url}\nDis au client de cliquer sur le lien pour payer."
                        elif order.tracking_url:
                            payment_info = f"\n\nLien de suivi : {order.tracking_url}\nDis au client qu'il peut suivre sa commande avec ce lien."
                        reply = await self._call_ai([
                            ChatMessage(role="system", content=self.system_prompt),
                            ChatMessage(
                                role="user",
                                content=(
                                    f"Message du client : {input_data.message}\n\n"
                                    f"Commande créée avec succès !\n"
                                    f"Produit : {ctx_data.product_name}\n"
                                    f"Quantité : {order.quantity}\n"
                                    f"Ville de livraison : {order.city}\n"
                                    f"Référence : {order.reference or order.order_id}\n"
                                    f"Montant total : {order.amount or 'N/A'} FCFA"
                                    f"{payment_info}"
                                    f"\n\nConfirme la commande de façon naturelle et chaleureuse (1-2 phrases)."
                                    f"{history_context}"
                                ),
                            ),
                        ])
                        return AgentOutput(
                            reply=reply,
                            handled=True,
                            tools_used=["create_order"],
                            data={
                                k: v for k, v in {
                                    "payment_url": order.payment_url,
                                    "tracking_url": order.tracking_url,
                                    "order_id": str(order.order_id) if order.order_id else None,
                                }.items() if v
                            } or None,
                        )

                # Infos partielles collectées → demander ce qui manque (jamais créer sans ville)
                if partial is not None or (ctx_data.pending_quantity or ctx_data.pending_city):
                    if not ctx_data.pending_quantity and not ctx_data.pending_city:
                        _missing = "la quantité souhaitée et ta ville de livraison"
                    elif not ctx_data.pending_quantity:
                        _missing = "la quantité souhaitée"
                    else:
                        _missing = "ta ville de livraison"
                    ctx_data.task_state = "awaiting_qty_city"
                    ctx_data.pending_action = "awaiting_qty_city"
                    _already = ""
                    if ctx_data.pending_quantity:
                        _already += f"Quantité déjà notée : {ctx_data.pending_quantity}.\n"
                    if ctx_data.pending_city:
                        _already += f"Ville déjà notée : {ctx_data.pending_city}.\n"
                    reply = await self._call_ai([
                        ChatMessage(role="system", content=self.system_prompt),
                        ChatMessage(
                            role="user",
                            content=(
                                f"Message du client : {input_data.message}\n\n"
                                f"Le client commande {ctx_data.product_name} "
                                f"(prix: {ctx_data.product_price or 'N/A'} FCFA).\n"
                                f"{_already}"
                                f"Demande-lui {_missing} en 1 phrase naturelle et chaleureuse."
                                f"{history_context}"
                            ),
                        ),
                    ])
                    return AgentOutput(reply=reply, handled=True, tools_used=[])

            # ── Commande déjà créée dans la conversation : rappeler les liens ──
            if ctx_data and ctx_data.order_id:
                links = ""
                if ctx_data.order_payment_url:
                    links += f"\nLien de paiement : {ctx_data.order_payment_url}"
                if ctx_data.order_tracking_url:
                    links += f"\nLien de suivi : {ctx_data.order_tracking_url}"
                reply = await self._call_ai([
                    ChatMessage(role="system", content=self.system_prompt),
                    ChatMessage(
                        role="user",
                        content=(
                            f"Message du client : {input_data.message}\n\n"
                            f"Une commande existe déjà dans cette conversation :\n"
                            f"Référence : {ctx_data.order_reference or ctx_data.order_id}"
                            f"{links}\n\n"
                            "Réponds à la question du client en t'appuyant sur ces informations réelles. "
                            "Donne-lui le lien utile (paiement ou suivi). Réponds en 1-2 phrases."
                            f"{history_context}"
                        ),
                    ),
                ])
                return AgentOutput(
                    reply=reply,
                    handled=True,
                    tools_used=[],
                    data={
                        k: v for k, v in {
                            "payment_url": ctx_data.order_payment_url,
                            "tracking_url": ctx_data.order_tracking_url,
                        }.items() if v
                    } or None,
                )

            # ── Infos manquantes : demander quantité/ville sans rien promettre ──
            product_info = ""
            if ctx_data and ctx_data.product_name:
                product_info = (
                    f"\n\nLe client s'intéresse au produit : {ctx_data.product_name}"
                    f" (prix: {ctx_data.product_price or 'N/A'} FCFA)."
                )
            reply = await self._call_ai([
                ChatMessage(
                    role="system",
                    content=(
                        "Tu es Tracy, une vendeuse de l'équipe Mantota. "
                        "Le client est sur le site public de Mantota. "
                        "Sur le site public, le client PEUT commander et payer directement. "
                        "Pour créer la commande, il te faut la quantité et la ville de livraison : "
                        "demande UNIQUEMENT les informations manquantes. "
                        "Ne dis JAMAIS que la commande est créée tant qu'elle ne l'est pas. "
                        "Si aucun produit n'est sélectionné, demande au client quel produit il veut. "
                        "Réponds en 1 ou 2 phrases maximum, chaleureuse et directe."
                    ),
                ),
                ChatMessage(
                    role="user",
                    content=(
                        f"Message du client : {input_data.message}"
                        f"{product_info}"
                        f"{history_context}"
                    ),
                ),
            ])
            return AgentOutput(reply=reply, handled=True, tools_used=[])

        # Détecter l'intention : annulation vs suivi vs création
        message_lower = input_data.message.lower()
        tools_used: list[str] = []

        if any(word in message_lower for word in ("annul", "supprim", "plus besoin")):
            # Annulation — demander confirmation avant d'exécuter
            reply = await self._call_ai([
                ChatMessage(role="system", content=self.system_prompt),
                ChatMessage(
                    role="user",
                    content=(
                        f"Message du client : {input_data.message}\n\n"
                        "Le client souhaite annuler une commande. Demande-lui "
                        "confirmation explicite et l'identifiant de la commande "
                        "avant de procéder à l'annulation."
                    ),
                ),
            ])
            return AgentOutput(reply=reply, handled=True, tools_used=tools_used)

        if any(word in message_lower for word in ("suiv", "statut", "où", "livraison", "livré")):
            # Suivi de commande — extraire la référence (CMD-XXXX ou order_XXX)
            order_ref = extract_order_reference(input_data.message)
            if not order_ref:
                reply = await self._call_ai([
                    ChatMessage(role="system", content=self.system_prompt),
                    ChatMessage(
                        role="user",
                        content=(
                            f"Message du client : {input_data.message}\n\n"
                            "Le client souhaite suivre une commande mais n'a pas "
                            "fourni l'identifiant. Demande-le lui poliment."
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

            if not track_result.success:
                logger.info(
                    "agent_track_failed",
                    agent=self.name,
                    correlation_id=input_data.correlation_id,
                    error_code=track_result.error.code if track_result.error else None,
                )
                reply = await self._call_ai([
                    ChatMessage(role="system", content=self.system_prompt),
                    ChatMessage(
                        role="user",
                        content=(
                            f"Message du client : {input_data.message}\n\n"
                            "Impossible de retrouver la commande. Demande au client "
                            "l'identifiant ou les détails de sa commande."
                        ),
                    ),
                ])
                return AgentOutput(reply=reply, handled=True, tools_used=tools_used)

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
                        "Présente ces informations au client de manière claire et rassurante."
                    ),
                ),
            ])
            return AgentOutput(reply=reply, handled=True, tools_used=tools_used)

        # Création de commande — demander les informations manquantes
        reply = await self._call_ai([
            ChatMessage(role="system", content=self.system_prompt),
            ChatMessage(
                role="user",
                content=(
                    f"Message du client : {input_data.message}\n\n"
                    "Le client souhaite passer ou confirmer une commande. "
                    "Vérifie que tu as toutes les informations nécessaires "
                    "(produit, quantité, adresse de livraison). Si oui, confirme "
                    "les détails avec le client. Si non, demande poliment "
                    "les informations manquantes."
                ),
            ),
        ])

        logger.info(
            "agent_reply_generated",
            agent=self.name,
            correlation_id=input_data.correlation_id,
        )

        return AgentOutput(reply=reply, handled=True, tools_used=tools_used)
