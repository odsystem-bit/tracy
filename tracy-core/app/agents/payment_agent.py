"""PaymentAgent (docs/tracy/03-AGENTS.md).

Rôle : Responsable des paiements, retraits et remboursements.
Responsabilité : Initier un paiement via Moneroo (par l'intermédiaire de
Mantota), vérifier le solde du wallet, traiter les demandes de retrait.

Outils autorisés : create_payment, get_wallet, request_withdrawal,
send_payment_link, activate_tracy_subscription.

Limites : n'exécute jamais une transaction sans validation Mantota ; ne stocke
jamais de données bancaires sensibles.

Autonomie V1 : Toujours validé par Mantota avant exécution finale.

Comportement IA (docs/tracy/05-AI_BEHAVIOR.md) :
- Chaleureuse, rassurante, factuelle sur les montants.
- Sécurité avant vitesse : une action sensible est toujours validée.
- Ne stocke jamais de données bancaires.
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
    "paiements, le wallet et les retraits pour les vendeurs et clients. "
    "Tu es une commerciale expérimentée, pas un chatbot.\n\n"
    "VOCABULAIRE INTERDIT :\n"
    "- « En tant que IA… », « Je suis un modèle de langage… »\n"
    "- « Bien sûr ! » en début de phrase\n"
    "- Listes à puces dans tes réponses\n"
    "- « N'hésitez pas à me contacter »\n\n"
    "RÈGLES :\n"
    "- Sécurité avant vitesse : ne valide jamais un paiement sans confirmation.\n"
    "- Ne stocke jamais de données bancaires sensibles (numéros de carte, codes).\n"
    "- Sois factuelle sur les montants et les statuts.\n"
    "- Pour un retrait, vérifie le solde disponible avant de soumettre la demande.\n"
    "- Rassure le client sur la sécurité du processus (Moneroo via Mantota).\n"
    "- N'invente jamais une information (montant, statut, référence).\n"
    "- Réponds en français, de façon concise et naturelle (max 3-4 phrases)."
)


class PaymentAgent(BaseAgent):
    """Responsable des paiements, retraits et remboursements."""

    @property
    def name(self) -> str:
        return "PaymentAgent"

    @property
    def autonomy(self) -> AgentAutonomy:
        return "always_validated"

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

        # Chat public : utiliser le contexte de conversation
        if input_data.store_id == "public":
            history_context = ""
            if input_data.conversation_history:
                history_context = "\n\nHistorique récent :\n" + "\n".join(
                    f"  - {msg}" for msg in input_data.conversation_history[-5:]
                )

            ctx_data = input_data.conversation_context

            # ── Commande créée dans la conversation : donner le VRAI lien ──
            if ctx_data and ctx_data.order_id:
                if ctx_data.order_payment_url:
                    link_info = (
                        f"Lien de paiement Moneroo : {ctx_data.order_payment_url}\n"
                        "Donne ce lien au client et dis-lui de cliquer dessus pour payer en toute sécurité."
                    )
                else:
                    link_info = (
                        f"Le lien de paiement n'est pas encore disponible pour cette commande "
                        f"({ctx_data.order_reference or ctx_data.order_id}). "
                    )
                    if ctx_data.order_tracking_url:
                        link_info += (
                            f"\nLien de suivi : {ctx_data.order_tracking_url}\n"
                            "Donne au client son lien de suivi et dis-lui que le paiement pourra se faire à la livraison."
                        )
                reply = await self._call_ai([
                    ChatMessage(role="system", content=self.system_prompt),
                    ChatMessage(
                        role="user",
                        content=(
                            f"Message du client : {input_data.message}\n\n"
                            f"Commande en cours : {ctx_data.order_reference or ctx_data.order_id}\n"
                            f"{link_info}\n\n"
                            "Réponds en 1-2 phrases, chaleureuse et rassurante. "
                            "N'invente aucun lien : utilise uniquement ceux fournis ci-dessus."
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
                        "Sur le site public, le client PEUT payer directement. "
                        "Le paiement se fait via Moneroo (par Mantota). "
                        "Si tu as les infos produit dans le contexte, rassure le client "
                        "et explique que le lien de paiement sera envoyé après création de la commande. "
                        "Pour créer la commande, demande la quantité et la ville de livraison. "
                        "Réponds en 1-2 phrases, chaleureuse et rassurante."
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

        # Détection : consultation du wallet
        # NB : « combien » seul est trop large (« combien ça coûte ? ») — on exige un contexte wallet
        if any(word in message_lower for word in ("wallet", "portefeuille", "solde", "gains")) or re.search(r"combien.*(?:gagn|re[çc]u|wallet|solde)", message_lower):
            wallet_result = await self._tool_registry.execute(
                "get_wallet",
                ctx,
                user_id=input_data.customer_id or "",
            )
            tools_used.append("get_wallet")

            if not wallet_result.success:
                logger.info(
                    "agent_wallet_failed",
                    agent=self.name,
                    correlation_id=input_data.correlation_id,
                    error_code=wallet_result.error.code if wallet_result.error else None,
                )
                reply = await self._call_ai([
                    ChatMessage(role="system", content=self.system_prompt),
                    ChatMessage(
                        role="user",
                        content=(
                            f"Message du client/vendeur : {input_data.message}\n\n"
                            "Le wallet n'est pas accessible pour le moment. "
                            "Informe-le du problème technique de manière rassurante."
                        ),
                    ),
                ])
                return AgentOutput(reply=reply, handled=True, tools_used=tools_used)

            wallet = wallet_result.data  # type: ignore[union-attr]
            transactions_summary = "\n".join(
                f"  - {t.type} : {t.montant:.0f} FCFA ({t.statut})"
                for t in wallet.dernieres_transactions[:5]
            ) or "Aucune transaction récente"

            reply = await self._call_ai([
                ChatMessage(role="system", content=self.system_prompt),
                ChatMessage(
                    role="user",
                    content=(
                        f"Message du client/vendeur : {input_data.message}\n\n"
                        f"Solde disponible : {wallet.solde_disponible:.0f} FCFA\n"
                        f"Solde en attente : {wallet.solde_en_attente:.0f} FCFA\n"
                        f"Dernières transactions :\n{transactions_summary}\n\n"
                        "Présente ces informations de manière claire et factuelle."
                    ),
                ),
            ])
            return AgentOutput(reply=reply, handled=True, tools_used=tools_used)

        # Détection : demande de retrait
        if any(word in message_lower for word in ("retrait", "retirer", "retir", "dépôt", "depose")):
            reply = await self._call_ai([
                ChatMessage(role="system", content=self.system_prompt),
                ChatMessage(
                    role="user",
                    content=(
                        f"Message du client/vendeur : {input_data.message}\n\n"
                        "Le client souhaite faire un retrait. Demande-lui les "
                        "informations nécessaires : montant, méthode de paiement "
                        "(mobile money, etc.), numéro de téléphone et pays. "
                        "Ne soumets pas la demande sans ces informations."
                    ),
                ),
            ])
            return AgentOutput(reply=reply, handled=True, tools_used=tools_used)

        # Détection : abonnement Tracy
        if any(word in message_lower for word in ("abonnement", "subscription", "plan", "activer", "renouvel")):
            reply = await self._call_ai([
                ChatMessage(role="system", content=self.system_prompt),
                ChatMessage(
                    role="user",
                    content=(
                        f"Message du vendeur : {input_data.message}\n\n"
                        "Le vendeur souhaite activer ou renouveler son abonnement Tracy. "
                        "Demande-lui quel plan il souhaite (mensuel, annuel, etc.). "
                        "L'activation débite son Wallet Mantota — informe-le clairement."
                    ),
                ),
            ])
            return AgentOutput(reply=reply, handled=True, tools_used=tools_used)

        # Détection : paiement / lien de paiement
        if any(word in message_lower for word in ("pay", "paiement", "payer", "moneroo", "lien")):
            reply = await self._call_ai([
                ChatMessage(role="system", content=self.system_prompt),
                ChatMessage(
                    role="user",
                    content=(
                        f"Message du client : {input_data.message}\n\n"
                        "Le client souhaite initier ou compléter un paiement. "
                        "Demande-lui l'identifiant de sa commande si nécessaire. "
                        "Le paiement se fait via Moneroo (par Mantota) — rassure-le "
                        "sur la sécurité du processus."
                    ),
                ),
            ])
            return AgentOutput(reply=reply, handled=True, tools_used=tools_used)

        # Fallback
        reply = await self._call_ai([
            ChatMessage(role="system", content=self.system_prompt),
            ChatMessage(
                role="user",
                content=(
                    f"Message du client/vendeur : {input_data.message}\n\n"
                    "Demande liée aux paiements mais non reconnue précisément. "
                    "Demande clarification de manière chaleureuse."
                ),
            ),
        ])

        logger.info(
            "agent_reply_generated",
            agent=self.name,
            correlation_id=input_data.correlation_id,
        )

        return AgentOutput(reply=reply, handled=True, tools_used=tools_used)
