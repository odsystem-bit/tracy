"""CommercialAgent (docs/tracy/03-AGENTS.md).

Rôle : Le vendeur virtuel. Anime la conversation commerciale de bout en bout.
Responsabilité : Comprendre l'intention du client, présenter les produits
pertinents, guider vers la commande.

Outils autorisés : search_products, search_catalog, search_store,
send_catalog, send_payment_link.

Limites : ne conclut jamais un paiement lui-même ; transfère à
OrderAgent/PaymentAgent dès qu'une commande est confirmée.

Autonomie V1 : Autonome pour la conversation, jamais pour conclure un paiement.

Comportement IA (docs/tracy/05-AI_BEHAVIOR.md) :
- Chaleureuse, compétente, honnête, proactive, discrète.
- Logique de vente : comprendre → proposer → rassurer → conclure.
- Ne vend jamais un produit indisponible, ni ne surestime un stock.
"""

from __future__ import annotations

import asyncio
import difflib
import re
from typing import Any

from app.agents.base import AgentAutonomy, AgentInput, AgentOutput, BaseAgent
from app.agents.location import location_kwargs, location_note, product_line, sort_by_scope
from app.agents.order_flow import (
    QuantityCity,
    apply_order_to_context,
    create_order_from_context,
    parse_partial_order_details,
    parse_quantity_city,
)
from app.ai_gateway.base import ChatMessage
from app.core.schemas import ProductCard
from app.knowledge.mantota_facts import MANTOTA_FACTS
from app.logging_config import bind_context, get_logger
from app.negotiation.reporting import (
    connect_client_vendor,
    resolve_vendor_id,
    send_vendor_report,
    wants_vendor_contact,
)
from app.tools.base import ToolContext

logger = get_logger(__name__)

SYSTEM_PROMPT = (
    "Tu es Tracy, une vendeuse de l'équipe Mantota. Tu parles avec ton client comme une vraie "
    "commerçante africine : chaleureuse, directe et honnête. Tu ne dis jamais que tu es une IA, "
    "un modèle de langage, un assistant ou une machine.\n\n"
    "PERSONNALITÉ : directe, compétente, honnête, proche.\n\n"
    "MISSION : aider le client à trouver un produit, commander et payer en toute confiance. "
    "Toutes tes réponses doivent ramener vers cette mission.\n\n"
    "GESTION DES QUESTIONS HORS-SUJET :\n"
    "- Si le client demande qui tu es ou qui t'a créée : réponds simplement 'Je suis Tracy, la vendeuse de Mantota.' Pas d'explication technique.\n"
    "- Si le client dit un mot qui n'a rien à voir (politique, météo, devinette, remerciement général, etc.) : réponds brièvement et ramène à l'achat.\n"
    "- Ne réponds jamais longuement hors-sujet. Une phrase suffit, puis 'Dis-moi ce que tu cherches, je vais te trouver ça.'\n\n"
    "VOCABULAIRE INTERDIT :\n"
    "- 'En tant qu'IA', 'en tant qu'assistant', 'je suis une IA', 'je suis un modèle'\n"
    "- 'Plonger', 'explorer', 'découvrir', 'naviguer', 'immersif', 'journey', 'voyage'\n"
    "- 'Comment puis-je t'aider aujourd'hui ?'\n"
    "- 'N'hésite pas à me contacter'\n"
    "- 'Bien sûr' en début de phrase\n"
    "- Listes à puces, numéros, formules administratives\n"
    "- 'Je suis ravie', 'c'est un plaisir', 'merci de ta confiance' sans raison\n"
    "- 'Téléchargez l'app', 'je ne suis pas disponible', 'téléchargez Mantota'\n\n"
    "VOCABULAIRE PRIVILÉGIÉ :\n"
    "- 'Écoute, j'ai ce qu'il te faut.'\n"
    "- 'Je te le mets de côté ?'\n"
    "- 'Ça fait combien ton budget ?'\n"
    "- 'Tu veux que je te crée la commande ?'\n"
    "- 'Paiement par MoMo ou par carte ?'\n"
    "- 'T'inquiète, c'est livré.'\n\n"
    "CONTEXTE ET MÉMOIRE :\n"
    "- Tu as accès ci-dessous à des souvenirs mémorisés sur le client/boutique (préférences, produits déjà vus, budget).\n"
    "- Utilise ces souvenirs UNIQUEMENT s'ils sont pertinents par rapport au message actuel du client.\n"
    "- Si le client dit 'salut', 'bonjour', 'hummm', 'non' ou un message sans lien avec un produit, NE mentionne PAS les souvenirs.\n"
    "- Si aucun souvenir n'est fourni, base-toi uniquement sur le message actuel et les produits trouvés.\n\n"
    "RÈGLES DE VENTE :\n"
    "- 1 ou 2 questions maximum avant de proposer.\n"
    "- Si le client est direct ('Je veux un Tecno Spark 10'), propose directement.\n"
    "- Max 3 produits à la fois.\n"
    "- Ne vends jamais un produit que tu n'as pas reçu.\n"
    "- Ne dis jamais 'N/A', 'indisponible', 'je ne peux pas' sans proposer une alternative concrète.\n"
    "- Ne propose JAMAIS un produit qui n'a pas de lien avec ce que le client demande.\n"
    "- Si le client cherche un accessoire pour un vêtement, propose uniquement des accessoires (sac, bijoux, chaussures) — JAMAIS un jouet, un téléphone ou un meuble.\n"
    "- Si tu ne trouves pas de produit pertinent, dis-le simplement et demande plus de précisions.\n"
    "- Conclus chaque message par une action claire : question, proposition ou invitation à commander.\n\n"
    "EXEMPLES DE RÉPONSES HORS-SUJET À RAMENER :\n"
    "- Client : 'Quel temps fait-il ?' → Tracy : 'Je gère les ventes ici. Tu cherches quoi aujourd'hui ?'\n"
    "- Client : 'Qui t'a créée ?' → Tracy : 'Je suis Tracy, vendeuse chez Mantota. Et toi, tu cherches quoi ?'\n"
    "- Client : 'Merci beaucoup' → Tracy : 'Avec plaisir. Je te crée la commande ?'\n\n"
    "TAILLE : max 2-3 phrases. Français simple et parlé."
)

# Prompt léger pour les présentations produit — sans MANTOTA_FACTS pour réduire les tokens
_LIGHT_PROMPT = (
    "Tu es Tracy, une vendeuse de l'équipe Mantota. Tu parles avec ton client comme une vraie "
    "commerçante africaine : chaleureuse, directe et honnête.\n\n"
    "RÈGLES : max 2-3 phrases. Pas de liste numérotée. Présente les produits trouvés uniquement. "
    "Demande lequel l'intéresse. Français simple et parlé."
)

# Vocabulaire pour la correction approchée des fautes (≥ 6 lettres, sans mots
# proches de verbes courants comme « montrer » / « charger »).
_FUZZY_PRODUCT_WORDS = [
    "telephone", "téléphone", "telephones", "téléphones", "smartphone",
    "ordinateur", "television", "télévision", "refrigerateur", "réfrigérateur",
    "climatiseur", "chaussure", "chaussures", "samsung", "iphone", "infinix",
    "xiaomi", "ecouteurs", "écouteurs", "powerbank", "tablette", "matelas",
]

# Mots-clés produits pour le filtrage de mémoire (module-level)
_PRODUCT_CONTEXT_WORDS = {
    "téléphone", "téléphones", "telephone", "telephones", "phone", "samsung", "iphone", "tecno", "infinix",
    "xiaomi", "redmi", "huawei", "ecouteur", "écouteur", "ecouteurs", "écouteurs", "casque", "casques",
    "coque", "coques", "chargeur", "chargeurs", "cable", "usb", "powerbank", "powerbanks", "bluetooth",
    "montre", "montres", "sac", "sacs", "chaussure", "chaussures", "vetement", "vêtement", "vetements", "vêtements",
    "basket", "baskets", "sandale", "sandales", "mocassin", "mocassins",
    "bottine", "bottines", "sneaker", "sneakers", "soulier", "souliers", "tong", "tongs",
    "produit", "produits", "modèle", "model", "models", "prix", "fcfa", "stock", "commande",
    "lit", "lits", "table", "tables", "canape", "canapé", "canapes", "canapés",
    "meuble", "meubles", "matelas", "chaise", "chaises", "armoire", "armoires",
    "fer", "blender", "bouilloire", "machine",
    "robe", "robes", "accessoire", "accessoires", "bijoux", "bijou",
    "boucle", "boucles", "oreille", "oreilles", "collier", "bracelet", "bague",
    "chemise", "chemises", "tenue", "tenues", "costume", "costumes",
    "mariage", "soiree", "soirée",
    "parfum", "parfums", "cosmetique", "cosmétique", "maquillage", "creme",
    "ordinateur", "laptop", "tablette", "ipad", "pc",
    "nokia", "motorola", "oppo", "vivo", "realme", "honor",
    "jupe", "jupes", "pantalon", "pantalons", "short", "shorts",
    "manteau", "veste", "vestes", "pull", "pulls", "t-shirt", "tshirt",
    "lunette", "lunettes", "sac", "sacs", "sacoche",
    "enfant", "enfants", "bebe", "bébé", "jouet", "jouets",
}


class CommercialAgent(BaseAgent):
    """Le vendeur virtuel — anime la conversation commerciale."""

    @property
    def name(self) -> str:
        return "CommercialAgent"

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

        # Récupération de la mémoire client — lazy : ne bloque pas le traitement principal
        # On lance la recherche mémoire en arrière-plan et on l'attend seulement quand nécessaire
        memory_task = asyncio.create_task(self._get_client_memory(input_data, ctx))

        # Étape 1 : recherche de produits correspondant au message du client
        # (skip pour le chat public — évite le deadlock avec le serveur PHP single-process)
        tools_used = []

        # Pré-check : questions non-produit à intercepter avant la recherche auto
        _msg_lower = input_data.message.lower()

        # Contexte de conversation (produit en cours, cartes récentes, etc.)
        conv_ctx = input_data.conversation_context

        # ── Photo jointe : le client envoie une image (« tu as ça ? ») ──
        # On la fait décrire par la gateway multimodale puis on cherche le produit.
        # Sans analyse possible, on l'avoue honnêtement — jamais simuler la vision.
        if input_data.image:
            return await self._handle_image(input_data, ctx)

        # ── Numéro de téléphone nu : « 0195900616 » envoyé après « laisse ton numéro » ──
        # L'interpréteur l'a déjà stocké dans ctx.user_phone — on accuse réception
        # au lieu de le traiter comme une recherche produit (« pas trouvé »).
        if conv_ctx and conv_ctx.user_phone:
            _msg_digits = re.sub(r"\D", "", input_data.message)
            if (
                len(_msg_digits) >= 8
                and _msg_digits.endswith(conv_ctx.user_phone)
            ):
                return AgentOutput(
                    reply=(
                        "C'est noté, merci ! J'ai transmis ton numéro au vendeur — "
                        "il pourra te rappeler directement."
                    ),
                    handled=True,
                    tools_used=[],
                )

        # ── Mise en relation avec le vendeur : Tracy prévient le vendeur avec un résumé ──
        if wants_vendor_contact(input_data.message):
            _vendor_id = resolve_vendor_id(input_data.store_id, conv_ctx)
            if _vendor_id is None:
                return AgentOutput(
                    reply="Bien sûr ! De quel produit ou de quelle boutique s'agit-il ? "
                    "Je préviens tout de suite le vendeur.",
                    handled=True,
                    tools_used=[],
                )
            _phone = input_data.customer_id if (input_data.customer_id or "").lstrip("+").isdigit() else None
            _topic = f" au sujet de {conv_ctx.product_name}" if conv_ctx and conv_ctx.product_name else ""
            _price_note = (
                f" Dernier prix discuté : {conv_ctx.negotiation_last_ask:.0f} FCFA."
                if conv_ctx and conv_ctx.negotiation_last_ask else ""
            )
            _summary = (
                f"Un client souhaite vous parler directement{_topic}.{_price_note} "
                f"Dernier message : « {input_data.message[:300]} »"
            )
            _tool_ctx = ToolContext(
                agent_name=self.name,
                correlation_id=input_data.correlation_id,
                store_id=input_data.store_id,
            )
            # APK : vraie conversation in-app client↔vendeur (customer_id = id utilisateur,
            # conversation_id préfixé "app:"). Web/WhatsApp : notification seule.
            _vendor_conv_id = await connect_client_vendor(
                self._tool_registry,
                _tool_ctx,
                conv_ctx,
                input_data.store_id,
                input_data.customer_id,
                input_data.conversation_id,
                _summary,
            )
            if _vendor_conv_id is not None:
                _data = (
                    {"vendor_conversation_id": _vendor_conv_id}
                    if _vendor_conv_id != "connected"
                    else None
                )
                return AgentOutput(
                    reply=(
                        "C'est fait ! Je t'ai mis en relation avec le vendeur — "
                        "la discussion apparaît dans tes messages. Il a reçu un résumé de ta demande."
                    ),
                    handled=True,
                    tools_used=["connect_client_vendor"],
                    data=_data,
                )
            _sent = await send_vendor_report(
                self._tool_registry,
                ToolContext(
                    agent_name=self.name,
                    correlation_id=input_data.correlation_id,
                    store_id=input_data.store_id,
                ),
                conv_ctx,
                input_data.store_id,
                "contact_request",
                f"Un client souhaite vous parler directement{_topic}.{_price_note} "
                f"Dernier message : « {input_data.message[:300]} »",
                customer_phone=_phone,
            ) if conv_ctx is not None else False
            _ask_phone = "" if _phone else " Si tu veux, laisse-moi ton numéro WhatsApp pour qu'il puisse te répondre plus vite."
            return AgentOutput(
                reply=(
                    "C'est noté, j'ai prévenu le vendeur et je lui ai transmis un résumé de notre discussion. "
                    "Il te recontactera dès qu'il est disponible." + _ask_phone
                    if _sent or (conv_ctx and f"contact_request:{conv_ctx.product_id}" in conv_ctx.vendor_reports_sent)
                    else "Je n'arrive pas à joindre le vendeur pour le moment, réessaie dans quelques instants ou écris-nous via le support."
                ),
                handled=True,
                tools_used=["send_vendor_report"] if _sent else [],
            )

        # ── Détection intention "afficher les produits déjà proposés" ──
        # Si le client dit "voir", "montre", "image", "catalogue", "photo" ET
        # qu'il y a des cartes produit récentes en contexte, on les renvoie directement.
        _show_products_words = (
            "voir", "vois", "montre", "montre-moi", "montre moi",
            "image", "images", "photo", "photos", "catalogue",
            "fiche", "affiche", "afficher", "le voir", "la voir",
            "les voir", "je veux voir", "je veux le voir", "je veux la voir",
            "montre le", "montre la", "montre les",
        )
        _has_recent_cards = (
            conv_ctx is not None
            and conv_ctx.last_cards is not None
            and len(conv_ctx.last_cards) > 0
        )
        _is_show_products_intent = (
            _has_recent_cards
            and any(w in _msg_lower for w in _show_products_words)
        )
        if _is_show_products_intent:
            cards = conv_ctx.last_cards  # type: ignore[union-attr]
            products_summary = "\n".join(
                f"- {c.name} : {c.price}"
                for c in cards
            )
            history_context = ""
            if input_data.conversation_history:
                history_context = "\n\nHistorique récent :\n" + "\n".join(
                    f"  - {msg}" for msg in input_data.conversation_history[-5:]
                )
            reply = await self._call_ai([
                ChatMessage(role="system", content=_LIGHT_PROMPT),
                ChatMessage(
                    role="user",
                    content=(
                        f"Message du client : {input_data.message}\n\n"
                        f"Le client demande à voir les produits que tu viens de proposer. "
                        f"Voici les produits :\n{products_summary}\n\n"
                        f"Présente-les à nouveau brièvement et demande lequel l'intéresse."
                        f"{history_context}"
                    ),
                ),
            ], max_tokens=200)
            reply = self._polish(reply)
            return AgentOutput(reply=reply, handled=True, tools_used=[], cards=cards)

        _is_currency_q = any(re.search(p, _msg_lower) for p in (
            "devise", "devises", "monnaie", "quelle monnaie",
            "tu accepte.*paiement", "momo", "mobile money",
            "quel pays", "tu livre.*pays",
        ))
        _is_promo_q = any(p in _msg_lower for p in (
            "promotion", "promotions", "promo", "promos", "solde", "soldes",
        ))
        # "catalogue" n'est classé non-produit que s'il n'y a pas de cartes récentes
        _boutique_q_words = (
            "tu vends quoi", "tu as quoi", "catalogue", "tu livre ou",
            "frais de livraison", "tu es ouverte", "tu es ouvert",
        )
        _is_boutique_q = (
            any(p in _msg_lower for p in _boutique_q_words)
            and not _has_recent_cards
        )
        _is_non_product = _is_currency_q or _is_promo_q or _is_boutique_q

        # Acceptation d'une contre-offre ("ok", "je le prends") : on fige le dernier prix
        # annoncé par Tracy et on reste dans le flux de commande (pas de nouvelle recherche).
        _accepts_offer = bool(
            conv_ctx is not None
            and conv_ctx.product_id is not None
            and conv_ctx.negotiation_rounds > 0
            and conv_ctx.negotiation_last_ask is not None
            and conv_ctx.negotiation_product_id == conv_ctx.product_id
            and conv_ctx.task_state not in ("awaiting_qty_city", "awaiting_confirmation", "order_created")
            and _msg_lower.strip(" !.") in {
                "ok", "oui", "ouais", "ouep", "d'accord", "daccord", "d accord", "go", "vas-y",
                "vas y", "parfait", "super", "c'est bon", "c est bon", "volontiers",
                "je le prends", "je la prends",
            }
        )
        if _accepts_offer and conv_ctx.negotiated_price is None:
            conv_ctx.negotiated_price = conv_ctx.negotiation_last_ask
            await send_vendor_report(
                self._tool_registry, ctx, conv_ctx, input_data.store_id, "sale",
                f"Le client a accepté {conv_ctx.product_name} à {conv_ctx.negotiated_price:.0f} FCFA "
                f"(prix affiché {(conv_ctx.product_price or 0):.0f} FCFA).",
            )

        # Si un produit est déjà en contexte et le message contient quantité+ville,
        # ne pas faire de recherche auto — laisser le handler qty+city créer la commande
        _has_qty_city = (
            conv_ctx is not None
            and conv_ctx.product_name is not None
            and conv_ctx.product_id is not None
            and (
                parse_quantity_city(_msg_lower) is not None
                or conv_ctx.task_state in ("awaiting_qty_city", "awaiting_confirmation")
            )
        )

        if input_data.store_id and input_data.store_id != "public" and not _is_non_product and not _has_qty_city and not _accepts_offer:
            search_result = await self._tool_registry.execute(
                "search_products",
                ctx,
                query=input_data.message,
                store_id=input_data.store_id,
                country=input_data.country_code,
            )
            tools_used = ["search_products"]

            if not search_result.success:
                logger.info(
                    "agent_no_product_found",
                    agent=self.name,
                    correlation_id=input_data.correlation_id,
                    error_code=search_result.error.code if search_result.error else None,
                )
                # T-002 : indiquer honnêtement qu'aucun produit ne correspond
                reply = await self._call_ai([
                    ChatMessage(role="system", content=self.system_prompt),
                    ChatMessage(
                        role="user",
                        content=(
                            f"Message du client : {input_data.message}\n\n"
                            "Aucun produit ne correspond à cette demande dans la boutique. "
                            "Informe honnêtement le client et propose une alternative si possible."
                        ),
                    ),
                ])
                reply = self._polish(reply)
                return AgentOutput(reply=reply, handled=True, tools_used=tools_used)

            products = search_result.data.products  # type: ignore[union-attr]
            cards = [
                ProductCard(
                    id=p.id,
                    name=p.nom,
                    price=f"{p.prix:,.0f}".replace(",", " ") + " F",
                    raw_price=p.prix,
                    stock=p.stock,
                    image_url=p.image_url,
                    store_id=p.store_id,
                    category=p.category,
                    description=p.description,
                )
                for p in products
            ]
            products_summary = "\n".join(
                f"- {p.nom} : {p.prix:.0f} FCFA (stock: {p.stock})"
                for p in products
            )

            # Étape 2 : génération de la réponse via l'AI Gateway
            history_context = ""
            if input_data.conversation_history:
                history_context = "\n\nHistorique récent :\n" + "\n".join(
                    f"  - {msg}" for msg in input_data.conversation_history[-5:]
                )

            # Sauvegarde des faits pertinents — fire-and-forget
            if products:
                asyncio.create_task(
                    self._save_client_fact(
                        input_data, ctx,
                        "produit_interet",
                        ", ".join(p.nom for p in products[:3]),
                        "observed",
                    )
                )

            # Attend la mémoire client (lancée en parallèle de la recherche produit)
            memory_context = await memory_task

            reply = await self._call_ai([
                ChatMessage(role="system", content=_LIGHT_PROMPT),
                ChatMessage(
                    role="user",
                    content=(
                        f"Message du client : {input_data.message}\n\n"
                        f"Souvenirs du client :\n{memory_context}\n\n"
                        f"Produits disponibles :\n{products_summary}"
                        f"{history_context}"
                    ),
                ),
            ], max_tokens=300)

            logger.info(
                "agent_reply_generated",
                agent=self.name,
                correlation_id=input_data.correlation_id,
                products_count=len(products),
            )

            reply = self._polish(reply)
            return AgentOutput(reply=reply, handled=True, tools_used=tools_used, cards=cards)

        # Chat public : recherche possible, mais toujours une réponse générée par GPT
        text = input_data.message.lower().strip()

        # Détection des messages simples (salutations, remplissages, négations courtes)
        simple_greetings = {
            "salut", "bonjour", "bonsoir", "bjr", "hey", "coucou", "yo",
            "hello", "hi", "cc", "bon",
        }
        simple_fillers = {
            "hummm", "hmm", "hum", "hmmm", "euh", "hein", "bof",
            "ok", "daccord", "d'accord", "oui", "non", "yes", "no",
            "nah", "na", "voila", "voilà", "merci",
        }
        product_context_words = {
            "téléphone", "téléphones", "telephone", "telephones", "phone", "phones", "portable", "portables",
            "samsung", "iphone", "tecno", "infinix",
            "xiaomi", "redmi", "huawei", "ecouteur", "écouteur", "ecouteurs", "écouteurs", "casque", "casques",
            "coque", "coques", "chargeur", "chargeurs", "cable", "usb", "powerbank", "powerbanks", "bluetooth",
            "montre", "montres", "sac", "sacs", "chaussure", "chaussures", "vetement", "vêtement", "vetements", "vêtements",
            "basket", "baskets", "sandale", "sandales", "mocassin", "mocassins",
            "bottine", "bottines", "sneaker", "sneakers", "soulier", "souliers", "tong", "tongs",
            "produit", "produits", "modèle", "model", "models", "prix", "fcfa", "stock", "commande",
            "lit", "lits", "table", "tables", "canape", "canapé", "canapes", "canapés",
            "meuble", "meubles", "matelas", "chaise", "chaises", "armoire", "armoires",
            "fer", "blender", "bouilloire", "machine",
            "robe", "robes", "accessoire", "accessoires", "bijoux", "bijou",
            "boucle", "boucles", "oreille", "oreilles", "collier", "bracelet", "bague",
            "chemise", "chemises", "tenue", "tenues", "costume", "costumes",
            "mariage", "soiree", "soirée",
            "parfum", "parfums", "cosmetique", "cosmétique", "maquillage", "creme",
            "ordinateur", "laptop", "tablette", "ipad", "pc",
            "nokia", "motorola", "oppo", "vivo", "realme", "honor",
            "jupe", "jupes", "pantalon", "pantalons", "short", "shorts",
            "manteau", "veste", "vestes", "pull", "pulls", "t-shirt", "tshirt",
            "lunette", "lunettes", "sac", "sacs", "sacoche",
            "enfant", "enfants", "bebe", "bébé", "jouet", "jouets",
        }
        is_simple_message = (
            text in simple_greetings
            or text in simple_fillers
            or (len(text) <= 5 and not re.search(r"\d", text) and not any(w in text for w in product_context_words))
        )

        # ── Le message nomme un produit précis parmi les cartes proposées → le verrouiller ──
        # "Je veux acheter iPhone 12 Pro" alors que 3 cartes ont été proposées :
        # on sélectionne la carte nommée pour alimenter le flux de commande.
        if conv_ctx and conv_ctx.last_cards and not conv_ctx.product_name:
            _named = [
                c for c in conv_ctx.last_cards
                if c.name.lower() in text
                or all(w in text for w in c.name.lower().split() if len(w) > 2)
            ]
            if len(_named) == 1:
                card = _named[0]
                conv_ctx.product_id = str(card.id)
                conv_ctx.product_name = card.name
                conv_ctx.product_mentioned = card.name
                conv_ctx.product_price = card.raw_price
                conv_ctx.product_store_id = card.store_id
                if conv_ctx.task_state not in ("awaiting_qty_city", "awaiting_confirmation", "order_created"):
                    conv_ctx.task_state = "product_found"

        # ── Follow-up contextuel AVANT le simple_message short-circuit ──
        # Si un produit est en contexte, "oui", "ok", "je le prends" etc. sont des follow-ups
        confirm_words = {"oui", "ok", "ouais", "ouep", "volontiers", "go", "parfait", "super", "génial", "genial", "daccord", "d'accord", "c'est bon", "c est bon", "vas y", "vas-y", "vasy"}
        # Détection de confirmation dans une phrase : "oui je confirme", "ok je valide"…
        _CONFIRM_RE = re.compile(
            r"\b(?:oui|ok|ouais|ouep|go|parfait|super|g[ée]nial|d['\s]?accord|daccord|"
            r"confirm\w*|valid\w*|volontiers|c['\s]est bon|exact)\b",
            re.IGNORECASE,
        )
        _in_order_flow = bool(
            conv_ctx
            and conv_ctx.task_state in (
                "awaiting_qty_city", "awaiting_confirmation", "order_created",
                "awaiting_multi_confirm",
            )
        )

        # ── Commande multi-produits en attente : confirmation + ville → création ──
        if conv_ctx and conv_ctx.task_state == "awaiting_multi_confirm" and conv_ctx.pending_multi_ids:
            _picked = [
                c for c in (conv_ctx.last_cards or [])
                if str(c.id) in conv_ctx.pending_multi_ids
            ]
            _mcity = conv_ctx.pending_city or conv_ctx.user_city
            _myes = text in confirm_words or bool(_CONFIRM_RE.search(text))
            _mno = conv_ctx.last_user_confirmation == "no" or text in {
                "non", "nan", "annule", "annuler", "laisse", "laisse tomber", "oublie",
            }
            if _mno:
                conv_ctx.task_state = None
                conv_ctx.pending_action = None
                conv_ctx.pending_multi_ids = []
                conv_ctx.pending_quantity = None
                conv_ctx.pending_city = None
                return AgentOutput(
                    reply="Pas de souci, j'ai annulé. Dis-moi si tu changes d'avis !",
                    handled=True,
                    tools_used=[],
                )
            if not _mcity:
                return AgentOutput(
                    reply="Parfait ! Il me manque juste ta ville de livraison pour créer les commandes.",
                    handled=True,
                    tools_used=[],
                    cards=_picked or None,
                )
            if not _myes:
                _mtotal = sum(c.raw_price for c in _picked)
                return AgentOutput(
                    reply=(
                        f"Total pour ta sélection : {_mtotal:,.0f} FCFA, livraison à {_mcity}. "
                        "Tu confirmes ? Je crée les commandes tout de suite."
                    ),
                    handled=True,
                    tools_used=[],
                    cards=_picked or None,
                )
            # Confirmation + ville présentes → créer une commande par produit
            _created: list[tuple[str, object]] = []
            _mtotal = 0.0
            _mqty = conv_ctx.pending_quantity or 1
            for _pid in conv_ctx.pending_multi_ids:
                _card = next((c for c in (conv_ctx.last_cards or []) if str(c.id) == _pid), None)
                if _card is None:
                    continue
                conv_ctx.product_id = str(_card.id)
                conv_ctx.product_name = _card.name
                conv_ctx.product_price = _card.raw_price
                conv_ctx.product_store_id = _card.store_id
                _o = await create_order_from_context(
                    self._tool_registry, ctx, conv_ctx, input_data, _mqty, _mcity,
                )
                if _o is not None:
                    _created.append((_card.name, _o))
                    _mtotal += _o.amount or (_card.raw_price * _mqty)
            conv_ctx.pending_multi_ids = []
            conv_ctx.pending_quantity = None
            conv_ctx.pending_city = None
            if _created:
                _last_o = _created[-1][1]
                conv_ctx.task_state = "order_created"
                conv_ctx.order_id = _last_o.order_id
                conv_ctx.order_reference = _last_o.reference
                conv_ctx.order_payment_url = _last_o.payment_url
                conv_ctx.order_tracking_url = _last_o.tracking_url
                _lines = "\n".join(
                    f"- {name} (réf {_o.reference or _o.order_id})" for name, _o in _created
                )
                _links = ""
                if _last_o.payment_url:
                    _links = f"\nLien de paiement : {_last_o.payment_url}"
                elif _last_o.tracking_url:
                    _links = f"\nLien de suivi : {_last_o.tracking_url}"
                return AgentOutput(
                    reply=(
                        f"C'est fait ! J'ai créé tes commandes :\n{_lines}\n\n"
                        f"Total : {_mtotal:,.0f} FCFA{_links}"
                    ),
                    handled=True,
                    tools_used=["create_order"] * len(_created),
                    cards=_picked or None,
                )
            conv_ctx.task_state = None
            return AgentOutput(
                reply="Désolé, je n'ai pas réussi à créer les commandes. Réessaie dans un instant.",
                handled=True,
                tools_used=[],
            )

        # ── Plusieurs produits nommés (« iPhone 12 et l'ordinateur, les deux feront combien ») ──
        _PRICE_OR_ORDER_RE = re.compile(
            r"\b(?:combien|fera|feront|ferait|font|fait|co[uû]te(?:nt|ra|ront)?|total|ensemble|"
            r"les\s+(?:deux|\d+)|tous|prends?|je\s+veux|je\s+voudrais|commande|ach[èe]te)\b",
            re.IGNORECASE,
        )
        _COMPARE_RE = re.compile(
            r"\b(?:lequel|laquelle|mieux|meilleur|meilleure|\bvs\b|diff[ée]rence|"
            r"compar[ée]r?|plut[ôo]t|entre\s+les)\b",
            re.IGNORECASE,
        )
        if (
            conv_ctx
            and len(conv_ctx.last_named_ids) >= 2
            and conv_ctx.last_cards
            and conv_ctx.task_state not in ("order_created", "awaiting_multi_confirm")
            and _PRICE_OR_ORDER_RE.search(text)
            and not _COMPARE_RE.search(text)
        ):
            _picked = [
                c for c in conv_ctx.last_cards
                if str(c.id) in conv_ctx.last_named_ids
            ][:4]
            if len(_picked) >= 2:
                _mtotal = sum(c.raw_price for c in _picked)
                conv_ctx.pending_multi_ids = [str(c.id) for c in _picked]
                conv_ctx.task_state = "awaiting_multi_confirm"
                conv_ctx.pending_action = "awaiting_multi_confirm"
                _mlines = "\n".join(f"- {c.name} : {c.raw_price:,.0f} FCFA" for c in _picked)
                return AgentOutput(
                    reply=(
                        f"Voici ta sélection :\n{_mlines}\n\n"
                        f"Ça fait {_mtotal:,.0f} FCFA au total. "
                        "Tu confirmes ? Et donne-moi ta ville de livraison pour créer les commandes."
                    ),
                    handled=True,
                    tools_used=[],
                    cards=_picked,
                )

        # ── Commande déjà créée : "oui", "je suis prêt", "ok" → rappeler les liens ──
        # Évite de redemander quantité/ville ou de créer une 2e commande.
        if conv_ctx and conv_ctx.order_id and conv_ctx.task_state == "order_created":
            _ack_or_ready = text in confirm_words or bool(
                re.search(r"\b(pr[eê]ts?|pres|pay|paie|paiement|finalis|allez|aller|envoie|confirm)\b", text)
            )
            if _ack_or_ready:
                links = ""
                if conv_ctx.order_payment_url:
                    links += f"\nLien de paiement : {conv_ctx.order_payment_url}"
                if conv_ctx.order_tracking_url:
                    links += f"\nLien de suivi : {conv_ctx.order_tracking_url}"
                _history = ""
                if input_data.conversation_history:
                    _history = "\n\nHistorique récent :\n" + "\n".join(
                        f"  - {msg}" for msg in input_data.conversation_history[-5:]
                    )
                reply = await self._call_ai([
                    ChatMessage(role="system", content=self.system_prompt),
                    ChatMessage(
                        role="user",
                        content=(
                            f"Message du client : {input_data.message}\n\n"
                            f"La commande du client est déjà créée :\n"
                            f"Produit : {conv_ctx.product_name}\n"
                            f"Référence : {conv_ctx.order_reference or conv_ctx.order_id}"
                            f"{links}\n\n"
                            f"Rappelle-lui que sa commande est confirmée et donne-lui le lien utile "
                            f"(paiement si présent, sinon suivi). 1-2 phrases, chaleureux. "
                            f"NE mentionne JAMAIS l'app Mantota."
                            f"{_history}"
                        ),
                    ),
                ], max_tokens=120)
                reply = self._polish(reply)
                return AgentOutput(reply=reply, handled=True, tools_used=[])

        if conv_ctx and conv_ctx.product_name and is_simple_message and not _in_order_flow:
            # Messages qui confirment un achat
            if text in confirm_words or any(p in text for p in ["je le prends", "je la prends", "je veux celui", "je le veut", "je la veut"]):
                history_context = ""
                if input_data.conversation_history:
                    history_context = "\n\nHistorique récent :\n" + "\n".join(
                        f"  - {msg}" for msg in input_data.conversation_history[-5:]
                    )
                _deal_price = (
                    conv_ctx.negotiated_price
                    if conv_ctx.negotiated_price is not None
                    and conv_ctx.negotiation_product_id == conv_ctx.product_id
                    else conv_ctx.product_price
                )
                pub_ctx = (
                    "Tu es sur le site public de Mantota. Le client n'est pas encore connecté. "
                    "Réponds de façon naturelle, chaleureuse et concise, comme une vraie vendeuse. "
                    "Sur le site, on discute, on montre les produits et on peut commander et payer directement. "
                    if input_data.store_id == "public" else
                    "Tu es Tracy, la vendeuse IA de cette boutique Mantota. "
                    "Réponds de façon naturelle, chaleureuse et concise."
                )
                reply = await self._call_ai([
                    ChatMessage(role="system", content=self.system_prompt),
                    ChatMessage(
                        role="user",
                        content=(
                            f"Message du client : {input_data.message}\n\n"
                            f"{pub_ctx}\n\n"
                            f"Le client confirme qu'il veut acheter : {conv_ctx.product_name} (prix: {_deal_price or 'N/A'}).\n\n"
                            f"Accueille sa décision avec enthousiasme et demande-lui la quantité et sa ville de livraison "
                            f"pour finaliser la commande. Réponds en 1-2 phrases."
                            f"{history_context}"
                        ),
                    ),
                ], max_tokens=150)
                reply = self._polish(reply)
                conv_ctx.task_state = "awaiting_qty_city"
                conv_ctx.pending_action = "awaiting_qty_city"
                _confirm_cards = conv_ctx.last_cards if conv_ctx and conv_ctx.last_cards else None
                return AgentOutput(reply=reply, handled=True, tools_used=[], cards=_confirm_cards)

        # ── Follow-up : quantité + ville de livraison quand produit en contexte ──
        # NB : pas de collecte si la commande est déjà créée (order_created)
        if (
            conv_ctx
            and conv_ctx.product_name
            and conv_ctx.product_id
            and conv_ctx.task_state != "order_created"
        ):
            qty_city = parse_quantity_city(text)
            history_context = ""
            if input_data.conversation_history:
                history_context = "\n\nHistorique récent :\n" + "\n".join(
                    f"  - {msg}" for msg in input_data.conversation_history[-5:]
                )
            pub_ctx = (
                "Tu es sur le site public de Mantota. "
                "Réponds de façon naturelle, chaleureuse et concise. "
                if input_data.store_id == "public" else
                "Tu es Tracy, la vendeuse IA de cette boutique Mantota. "
                "Réponds de façon naturelle, chaleureuse et concise."
            )
            if not qty_city:
                # Quantité et ville peuvent arriver dans des messages séparés :
                # on les accumule dans le contexte de conversation.
                # NB : "tu livres a cotonou ?" est une question, pas une info de commande.
                _is_question = "?" in text or any(
                    p in text for p in ("combien", "est-ce", "tu livre", "vous livrez")
                )
                partial = None if _is_question else parse_partial_order_details(text)
                if partial is not None:
                    if partial.quantity:
                        conv_ctx.pending_quantity = partial.quantity
                    if partial.city:
                        conv_ctx.pending_city = partial.city
                _pq = conv_ctx.pending_quantity
                _pc = conv_ctx.pending_city

                # Annulation explicite pendant la collecte
                if (
                    conv_ctx.task_state in ("awaiting_qty_city", "awaiting_confirmation")
                    and text in {"non", "nan", "annule", "annuler", "laisse", "laisse tomber", "oublie"}
                ):
                    conv_ctx.pending_quantity = None
                    conv_ctx.pending_city = None
                    conv_ctx.task_state = None
                    conv_ctx.pending_action = None
                    reply = await self._call_ai([
                        ChatMessage(role="system", content=self.system_prompt),
                        ChatMessage(
                            role="user",
                            content=(
                                f"Message du client : {input_data.message}\n\n"
                                f"{pub_ctx}\n\n"
                                f"Le client annule sa commande en cours ({conv_ctx.product_name}). "
                                f"Rassure-le en 1 phrase : la commande est abandonnée, tu restes disponible."
                                f"{history_context}"
                            ),
                        ),
                    ], max_tokens=100)
                    reply = self._polish(reply)
                    return AgentOutput(reply=reply, handled=True, tools_used=[])

                if _pq and _pc:
                    # Toutes les infos sont collectées : "oui" valide, sinon on récapitule
                    if conv_ctx.task_state == "awaiting_confirmation" and _CONFIRM_RE.search(text):
                        qty_city = QuantityCity(quantity=_pq, city=_pc)
                    else:
                        conv_ctx.task_state = "awaiting_confirmation"
                        conv_ctx.pending_action = "awaiting_confirmation"
                        _total = (conv_ctx.product_price or 0) * _pq
                        reply = await self._call_ai([
                            ChatMessage(role="system", content=self.system_prompt),
                            ChatMessage(
                                role="user",
                                content=(
                                    f"Message du client : {input_data.message}\n\n"
                                    f"{pub_ctx}\n\n"
                                    f"Récapitulatif de la commande à confirmer :\n"
                                    f"Produit : {conv_ctx.product_name}\n"
                                    f"Quantité : {_pq}\n"
                                    f"Ville de livraison : {_pc}\n"
                                    f"Montant total : {_total:,.0f} FCFA\n\n"
                                    f"Récapitule la commande en 1-2 phrases et demande au client de confirmer "
                                    f"pour la finaliser. NE mentionne JAMAIS l'app Mantota."
                                    f"{history_context}"
                                ),
                            ),
                        ], max_tokens=150)
                        reply = self._polish(reply)
                        return AgentOutput(reply=reply, handled=True, tools_used=[])
                elif (
                    partial is not None
                    or (
                        # "je veux acheter iPhone 12 Pro" → demander directement qté+ville
                        # « prend » sans s inclus : faute de frappe très fréquente
                        re.search(r"\b(?:je\s+)?(?:veux|voudrais|souhaite|prends?|commande|ach[eè]te)\b", text)
                        and conv_ctx.product_name.lower() in text
                    )
                    or (
                        conv_ctx.task_state in ("awaiting_qty_city", "awaiting_confirmation")
                        and _CONFIRM_RE.search(text)
                    )
                ):
                    # Une info collectée mais il en manque encore une → la demander
                    conv_ctx.task_state = "awaiting_qty_city"
                    conv_ctx.pending_action = "awaiting_qty_city"
                    if not _pq and not _pc:
                        _missing = "la quantité souhaitée et ta ville de livraison"
                    elif not _pq:
                        _missing = "la quantité souhaitée"
                    else:
                        _missing = "ta ville de livraison"
                    _already = ""
                    if _pq:
                        _already += f"Quantité déjà notée : {_pq}.\n"
                    if _pc:
                        _already += f"Ville déjà notée : {_pc}.\n"
                    reply = await self._call_ai([
                        ChatMessage(role="system", content=self.system_prompt),
                        ChatMessage(
                            role="user",
                            content=(
                                f"Message du client : {input_data.message}\n\n"
                                f"{pub_ctx}\n\n"
                                f"Le client commande {conv_ctx.product_name} (prix: {conv_ctx.product_price or 'N/A'} FCFA).\n"
                                f"{_already}"
                                f"Demande-lui {_missing} en 1 phrase naturelle et chaleureuse. "
                                f"NE mentionne JAMAIS l'app Mantota."
                                f"{history_context}"
                            ),
                        ),
                    ], max_tokens=120)
                    reply = self._polish(reply)
                    return AgentOutput(reply=reply, handled=True, tools_used=[])
            if qty_city:
                order = await create_order_from_context(
                    self._tool_registry, ctx, conv_ctx, input_data,
                    qty_city.quantity, qty_city.city,
                )
                if order:
                    apply_order_to_context(conv_ctx, order)
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
                                f"{pub_ctx}\n\n"
                                f"Commande créée avec succès !\n"
                                f"Produit : {conv_ctx.product_name}\n"
                                f"Quantité : {order.quantity}\n"
                                f"Ville de livraison : {order.city}\n"
                                f"Référence : {order.reference or order.order_id}\n"
                                f"Montant total : {order.amount or 'N/A'} FCFA"
                                f"{payment_info}"
                                f"\n\nConfirme la commande au client de façon naturelle et chaleureuse (1-2 phrases). "
                                f"Si tu as un lien de paiement, dis au client de cliquer dessus pour payer. "
                                f"NE mentionne JAMAIS l'app Mantota."
                                f"{history_context}"
                            ),
                        ),
                    ], max_tokens=200)
                    reply = self._polish(reply)
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

                # Fallback : si la création échoue, demander les infos de contact
                reply = await self._call_ai([
                    ChatMessage(role="system", content=self.system_prompt),
                    ChatMessage(
                        role="user",
                        content=(
                            f"Message du client : {input_data.message}\n\n"
                            f"{pub_ctx}\n\n"
                            f"Le client veut commander {qty_city.quantity}x {conv_ctx.product_name} à livrer à {qty_city.city}. "
                            f"Le produit coûte {conv_ctx.product_price or 'N/A'} FCFA. "
                            f"Confirme la commande et demande son numéro de téléphone pour finaliser. "
                            f"Réponds en 1-2 phrases. NE mentionne JAMAIS l'app Mantota."
                            f"{history_context}"
                        ),
                    ),
                ], max_tokens=150)
                reply = self._polish(reply)
                return AgentOutput(reply=reply, handled=True, tools_used=[])

        # ── Follow-up questions contextuel (combien, disponible, comment je paie) ──
        if conv_ctx and conv_ctx.product_name:
            question_phrases = ["combien", "c est combien", "c'est combien", "le prix", "disponible", "en stock", "comment je paie", "je peux payer", "je paie", "comment payer"]
            if any(p in text for p in question_phrases):
                history_context = ""
                if input_data.conversation_history:
                    history_context = "\n\nHistorique récent :\n" + "\n".join(
                        f"  - {msg}" for msg in input_data.conversation_history[-5:]
                    )
                pub_ctx = (
                    "Tu es sur le site public de Mantota. Le client n'est pas encore connecté. "
                    "Réponds de façon naturelle, chaleureuse et concise, comme une vraie vendeuse. "
                    "Sur le site, on discute, on montre les produits et on peut commander et payer directement. "
                    if input_data.store_id == "public" else
                    "Tu es Tracy, la vendeuse IA de cette boutique Mantota. "
                    "Réponds de façon naturelle, chaleureuse et concise."
                )
                reply = await self._call_ai([
                    ChatMessage(role="system", content=self.system_prompt),
                    ChatMessage(
                        role="user",
                        content=(
                            f"Message du client : {input_data.message}\n\n"
                            f"{pub_ctx}\n\n"
                            f"Le client pose une question sur le produit : {conv_ctx.product_name} (prix: {conv_ctx.product_price or 'N/A'}).\n\n"
                            f"Réponds à sa question de façon naturelle et concise (1-2 phrases). "
                            f"Si il demande le prix, rappelle le prix. Si il demande la disponibilité, dis-le. "
                            f"Si il demande comment payer, explique que tu vas créer la commande et envoyer un lien de paiement."
                            f"{history_context}"
                        ),
                    ),
                ], max_tokens=150)
                reply = self._polish(reply)
                _q_cards = conv_ctx.last_cards if conv_ctx and conv_ctx.last_cards else None
                return AgentOutput(reply=reply, handled=True, tools_used=[], cards=_q_cards)

        # ── Follow-up : "fouille dans les boutiques", "cherche partout" ──
        # Le client demande de chercher plus largement après une recherche infructueuse
        if conv_ctx and conv_ctx.product_mentioned:
            search_again_phrases = [
                "fouille", "cherche partout", "cherche dans les boutique", "cherche dans les magasins",
                "cherche encore", "recherche", "recherche partout", "essaie encore", "essaie ailleurs",
                "trouve le", "trouve la", "trouve dans", "cherche dans toutes",
            ]
            if any(p in text for p in search_again_phrases):
                # Relancer la recherche avec le produit mentionné dans le contexte
                search_result = await self._tool_registry.execute(
                    "search_products",
                    ctx,
                    query=conv_ctx.product_mentioned,
                    store_id=None,
                    limit=5,
                )
                sa_pub_ctx = (
                    "Tu es sur le site public de Mantota. Réponds de façon naturelle, chaleureuse et concise. "
                    if input_data.store_id == "public" else
                    "Tu es Tracy, la vendeuse IA de cette boutique Mantota. Réponds de façon naturelle, chaleureuse et concise. "
                )
                if search_result.success and search_result.data.products:
                    products = search_result.data.products
                    cards = [
                        ProductCard(
                            id=p.id, name=p.nom,
                            price=f"{p.prix:,.0f}".replace(",", " ") + " F",
                            raw_price=p.prix, stock=p.stock,
                            image_url=p.image_url, store_id=p.store_id,
                            category=p.category, description=p.description,
                        )
                        for p in products[:5]
                    ]
                    products_summary = "\n".join(
                        f"- {p.nom} : {p.prix:.0f} FCFA (stock: {p.stock})"
                        for p in products[:5]
                    )
                    history_context = ""
                    if input_data.conversation_history:
                        history_context = "\n\nHistorique récent :\n" + "\n".join(
                            f"  - {msg}" for msg in input_data.conversation_history[-5:]
                        )
                    reply = await self._call_ai([
                        ChatMessage(role="system", content=self.system_prompt),
                        ChatMessage(
                            role="user",
                            content=(
                                f"Message du client : {input_data.message}\n\n"
                                f"Produits trouvés :\n{products_summary}\n\n"
                                f"{sa_pub_ctx}\n\n"
                                "Le client t'a demandé de chercher dans toutes les boutiques. "
                                "Présente ces produits de façon naturelle et chaleureuse. "
                                "Demande lequel l'intéresse."
                                f"{history_context}"
                            ),
                        ),
                    ])
                    reply = self._polish(reply)
                    return AgentOutput(reply=reply, handled=True, tools_used=["search_products"], cards=cards)
                else:
                    history_context = ""
                    if input_data.conversation_history:
                        history_context = "\n\nHistorique récent :\n" + "\n".join(
                            f"  - {msg}" for msg in input_data.conversation_history[-5:]
                        )
                    reply = await self._call_ai([
                        ChatMessage(role="system", content=self.system_prompt),
                        ChatMessage(
                            role="user",
                            content=(
                                f"Message du client : {input_data.message}\n\n"
                                f"{sa_pub_ctx}\n\n"
                                f"Tu as cherché '{conv_ctx.product_mentioned}' dans toutes les boutiques mais n'as rien trouvé. "
                                "Dis-le honnêtement au client et demande-lui s'il veut chercher autre chose. "
                                "Reste concise (1-2 phrases). NE mentionne JAMAIS l'app Mantota."
                                f"{history_context}"
                            ),
                        ),
                    ])
                    reply = self._polish(reply)
                    return AgentOutput(reply=reply, handled=True, tools_used=["search_products"])

        # ── Gestion de l'intent app_download (avant la recherche produit) ──
        download_phrases = [
            'télécharger', 'telecharger', 'download', 'installer', 'application',
            'play store', 'app store', 'apk',
            'où télécharger', 'ou telecharger', 'donne moi le lien', 'donne le lien',
            'je veux l app', 'je veux mantota', 'lien de l app', 'lien app',
        ]
        # Éviter les faux positifs : "app" seul est trop générique, il faut au moins un autre mot-clé
        has_download_intent = any(p in text for p in download_phrases)
        # "app" seul n'est pas suffisant, mais "l app", "l'app", "l application" oui
        if not has_download_intent and ('l app' in text or "l'app" in text or 'l application' in text):
            has_download_intent = True
        if has_download_intent:
            from app.config import get_settings
            settings = get_settings()
            dl_ctx = input_data.conversation_context
            product_info = ""
            if dl_ctx and dl_ctx.product_name:
                product_info = f"\n\nLe client s'intéresse au produit : {dl_ctx.product_name} (prix: {dl_ctx.product_price or 'N/A'})."
            dl_history = ""
            if input_data.conversation_history:
                dl_history = "\n\nHistorique récent :\n" + "\n".join(
                    f"  - {msg}" for msg in input_data.conversation_history[-5:]
                )
            reply = await self._call_ai([
                ChatMessage(role="system", content=self.system_prompt),
                ChatMessage(
                    role="user",
                    content=(
                        f"Message du client : {input_data.message}\n\n"
                        f"Le client demande où télécharger l'app Mantota ou demande le lien de l'app."
                        f"{product_info}"
                        f"\n\nDonne les liens officiels de téléchargement :\n"
                        f"- Android (Play Store) : {settings.mantota_play_store_url}\n"
                        f"- iOS (App Store) : {settings.mantota_app_store_url}\n"
                        f"- APK direct : {settings.mantota_apk_url}\n"
                        f"Présente les liens de façon naturelle et chaleureuse (1-2 phrases). "
                        f"Si le client s'intéressait à un produit, mentionne qu'il pourra le retrouver dans l'app."
                        f"{dl_history}"
                    ),
                ),
            ])
            reply = self._polish(reply)
            return AgentOutput(reply=reply, handled=True, tools_used=[])

        history_context = ""
        if input_data.conversation_history:
            history_context = "\n\nHistorique récent :\n" + "\n".join(
                f"  - {msg}" for msg in input_data.conversation_history[-5:]
            )

        if input_data.store_id == "public":
            public_context = (
                "Tu es sur le site public de Mantota. Le client n'est pas encore connecté. "
                "Réponds de façon naturelle, chaleureuse et concise, comme une vraie vendeuse. "
                "Sur le site, on discute, on montre les produits et on peut commander et payer directement. "
                "Quand le client veut acheter, demande-lui la quantité et sa ville de livraison, "
                "puis crée la commande et envoie le lien de paiement. "
                "Ne mentionne JAMAIS l'app Mantota, le téléchargement d'une application, ni le fait que tu n'es pas disponible. "
                "Si tu ne trouves pas de produit, dis-le honnêtement et demande plus de détails. NE dis JAMAIS 'téléchargez l'app' ou 'je ne suis pas disponible'. "
                "Tu es TOUJOURS disponible pour aider le client sur le site. "
                "Ne commence pas chaque phrase par 'Écoute' ou 'Pour'. "
                "Pour les produits, montre UNIQUEMENT ceux que tu as trouvés via la recherche. "
                "Si tu ne trouves rien, dis-le honnêtement et demande plus de détails (marque, modèle, type). "
                "Ne cite JAMAIS un produit que tu n'as pas trouvé, ne fais pas de liste numérotée, ne dis pas '1.' ou '2.'. "
                "Si le client refuse un produit proposé, excuse-toi et recentre-toi sur ses vraies préférences (téléphone, écouteur, etc.). "
                "Si le client te demande ce qu'il a dit au début, regarde l'historique fourni et réponds avec ses propres mots, sans forcer la vente. "
                "Pose une seule question à la fois.\n"
                "\nFAITS OFFICIELS MANTOTA :\n" + MANTOTA_FACTS + "\n"
            )
        else:
            public_context = (
                "Tu es Tracy, la vendeuse IA de cette boutique Mantota. "
                "Réponds de façon naturelle, chaleureuse et concise. "
                "Pour les produits, montre UNIQUEMENT ceux que tu as trouvés via la recherche. "
                "Si tu ne trouves rien, dis-le honnêtement et demande plus de détails. "
                "Ne cite JAMAIS un produit que tu n'as pas trouvé, ne fais pas de liste numérotée. "
                "Pose une seule question à la fois.\n"
                "\nFAITS OFFICIELS MANTOTA :\n" + MANTOTA_FACTS + "\n"
            )

        # ── Court-circuit : messages simples (salut, hummm, non, ok, merci) ──
        # Réponses pré-définies → AUCUN appel OpenAI → réponse instantanée
        # Skip aussi la recherche mémoire (pas nécessaire pour un simple "bonjour")
        if is_simple_message:
            memory_task.cancel()
            _simple_replies = {
                "salut": "Salut ! Tu cherches quoi aujourd'hui ?",
                "bonjour": "Bonjour ! Qu'est-ce que tu cherches aujourd'hui ?",
                "bonsoir": "Bonsoir ! Tu cherches quoi aujourd'hui ?",
                "bjr": "Bonjour ! Qu'est-ce que tu cherches ?",
                "hey": "Hey ! Tu cherches quoi aujourd'hui ?",
                "coucou": "Coucou ! Qu'est-ce que tu cherches ?",
                "yo": "Yo ! Tu cherches quoi aujourd'hui ?",
                "hello": "Hello ! Qu'est-ce que tu cherches ?",
                "hi": "Hi ! Tu cherches quoi aujourd'hui ?",
                "cc": "Coucou ! Qu'est-ce que tu cherches ?",
                "bon": "Bon, qu'est-ce que tu cherches ?",
                "ok": "D'accord ! Tu cherches quoi aujourd'hui ?",
                "daccord": "D'accord ! Tu cherches quoi ?",
                "d'accord": "D'accord ! Tu cherches quoi ?",
                "oui": "Parfait ! Qu'est-ce que tu cherches ?",
                "ouais": "Ouais ! Tu cherches quoi ?",
                "ouep": "Ouep ! Tu cherches quoi ?",
                "volontiers": "Avec plaisir ! Tu cherches quoi ?",
                "go": "Go ! Qu'est-ce que tu cherches ?",
                "parfait": "Parfait ! Tu cherches quoi d'autre ?",
                "super": "Super ! Tu cherches quoi ?",
                "génial": "Génial ! Tu cherches quoi ?",
                "genial": "Génial ! Tu cherches quoi ?",
                "non": "D'accord. Qu'est-ce que tu cherches alors ?",
                "yes": "Parfait ! Qu'est-ce que tu cherches ?",
                "no": "D'accord. Qu'est-ce que tu cherches alors ?",
                "nah": "D'accord. Qu'est-ce que tu cherches ?",
                "na": "D'accord. Qu'est-ce que tu cherches ?",
                "merci": "Avec plaisir ! Tu as besoin d'autre chose ?",
                "hummm": "Hmm, dis-moi ce que tu cherches exactement.",
                "hmm": "Hmm, qu'est-ce que tu cherches ?",
                "hum": "Hum, qu'est-ce que tu cherches ?",
                "hmmm": "Hmm, dis-moi ce que tu cherches.",
                "euh": "Euh, pas de souci. Tu cherches quoi ?",
                "hein": "Tu cherches quoi exactement ?",
                "bof": "Bon, qu'est-ce que tu cherches ?",
                "voila": "Voilà ! Tu cherches quoi d'autre ?",
                "voilà": "Voilà ! Tu cherches quoi d'autre ?",
            }
            _reply = _simple_replies.get(text)
            if _reply:
                return AgentOutput(reply=_reply, handled=True, tools_used=[])
            # Fallback pour messages ≤ 5 chars non reconnus
            if len(text) <= 5:
                return AgentOutput(reply="Qu'est-ce que tu cherches aujourd'hui ?", handled=True, tools_used=[])

        search_phrases = [
            'je veux', 'je voudrais', 'j\'aimerais', 'jaimerais', 'je cherche',
            'donne moi', 'montre-moi', 'montre moi', 'montre', 'montrer',
            'propose', 'proposer', 'disponible', 'quel', 'quelle', 'model', 'modele',
            'version', 'budget', 'prix', 'combien', 'prendre', 'prends',
            'acheter', 'achete', 'trouve', 'produit',
            'téléphone', 'telephone', 'phone', 'portable', 'portables', 'samsung', 'iphone', 'tecno', 'infinix',
            'xiaomi', 'redmi', 'huawei', 'ecouteur', 'écouteur', 'casque', 'coque',
            'chargeur', 'cable', 'usb', 'powerbank', 'montre', 'sac', 'chaussure',
            'basket', 'baskets', 'sandale', 'sandales', 'mocassin', 'mocassins',
            'bottine', 'bottines', 'sneaker', 'sneakers', 'soulier', 'souliers',
            'vetement', 'vêtement',
            'lit', 'table', 'tables', 'canape', 'canapé', 'canapes', 'canapés',
            'meuble', 'meubles', 'matelas', 'chaise', 'chaises', 'armoire', 'armoires',
            'fer', 'fer a repasser', 'blender', 'bouilloire', 'machine',
            'robe', 'robes', 'accessoire', 'accessoires', 'bijoux', 'bijou',
            'boucle', 'boucles', 'oreille', 'oreilles', 'doreil', 'doreille',
            'collier', 'bracelet', 'bague', 'montre', 'montres',
            'chemise', 'chemises', 'tenue', 'tenues', 'costume', 'costumes',
            'mariage', 'soiree', 'soirée', 'soirees', 'soirées',
            'parfum', 'cosmetique', 'cosmétique', 'maquillage', 'creme',
            'ordinateur', 'laptop', 'tablette', 'ipad', 'pc',
            'nokia', 'motorola', 'oppo', 'vivo', 'realme',
            'jupe', 'pantalon', 'short', 'manteau', 'veste', 'pull', 'tshirt',
            'lunette', 'sacoche',
            'enfant', 'bebe', 'bébé', 'jouet',
            'autre', 'autre chose', 'différent', 'different', 'pas celui',
        ]

        # Corrections de typos courantes sur les produits
        typo_corrections = {
            'xanape': 'canapé', 'canape': 'canapé', 'canapes': 'canapés',
            'television': 'télévision',
            'ecouteur': 'écouteur', 'ecouteurs': 'écouteurs',
            'vetement': 'vêtement', 'vetements': 'vêtements',
            'samsang': 'samsung', 'samsng': 'samsung',
            'iphon': 'iphone', 'iphoone': 'iphone',
            'techo': 'tecno', 'infenix': 'infinix',
            'xiomi': 'xiaomi', 'redme': 'redmi',
            'powrbank': 'powerbank', 'pwrbank': 'powerbank',
            'cask': 'casque', 'casq': 'casque',
            'tablee': 'table', 'tabe': 'table',
            'lie': 'lit', 'litt': 'lit',
            'matela': 'matelas', 'matelat': 'matelas',
            'chais': 'chaise', 'chaisee': 'chaise',
            'armoir': 'armoire',
            'meubl': 'meuble', 'meublee': 'meuble',
            'doreil': 'd\'oreilles', 'doreille': 'd\'oreilles', 'doreilles': 'd\'oreilles',
            'accessoir': 'accessoire', 'accessoirs': 'accessoires',
            'vaas': 'vas', 'vaasy': 'vas y',
            'robee': 'robe', 'roobes': 'robes',
            'bijou': 'bijoux', 'colier': 'collier',
            'chaussur': 'chaussure', 'chaussures': 'chaussures',
            'bottine': 'bottines',
            'chherche': 'cherche', 'chhercher': 'chercher',
            'ooui': 'oui', 'ouui': 'oui',
            'quooi': 'quoi', 'quoid': 'quoi',
            'cest': 'c\'est', 'Cest': 'C\'est',
            'merd': 'merde',
            'comprend': 'comprends', 'compren': 'comprends',
            'tenuee': 'tenue', 'tenues': 'tenues',
            'chemisee': 'chemise', 'chemises': 'chemises',
            'soiree': 'soirée', 'soirees': 'soirées',
            'mariagee': 'mariage',
            # Marque : en Afrique de l'Ouest « techno » = Tecno (Transsion)
            'techno': 'tecno', 'tekno': 'tecno',
            # « coordonnées » et ses fautes fréquentes
            'coodoner': 'coordonnées', 'coodonnees': 'coordonnées',
            'coodonees': 'coordonnées', 'coordonées': 'coordonnées',
            'coordoner': 'coordonnées', 'coordonner': 'coordonnées',
            'coordonnes': 'coordonnées', 'coordonnees': 'coordonnées',
            'cordonées': 'coordonnées', 'cordonner': 'coordonnées',
            'coordonné': 'coordonnées', 'coordonnée': 'coordonnées',
            # « boutique » mal orthographiée
            'boutisue': 'boutique', 'boutiquez': 'boutique',
            'boutiqe': 'boutique', 'butique': 'boutique',
            # « téléphone » mal orthographié
            'telpehone': 'téléphone', 'telphone': 'téléphone', 'telepone': 'téléphone',
            'telefone': 'téléphone', 'telephonne': 'téléphone', 'tlphone': 'téléphone',
        }
        def _fix_typos(value: str) -> str:
            for typo, correct in typo_corrections.items():
                value = re.sub(r"(?<![\wÀ-ÿ])" + re.escape(typo) + r"(?![\wÀ-ÿ])", correct, value)
            # Filet générique : faute non listée sur un mot-produit clé
            # (« telpehone », « ordinatuer »…) → correction approchée.
            def _fuzzy(m: re.Match[str]) -> str:
                word = m.group(0)
                if len(word) < 6 or word in _FUZZY_PRODUCT_WORDS:
                    return word
                close = difflib.get_close_matches(word, _FUZZY_PRODUCT_WORDS, n=1, cutoff=0.85)
                return close[0] if close else word
            return re.sub(r"[a-zà-ÿ]+", _fuzzy, value)

        text = _fix_typos(text)
        # Abréviations par mot entier (pas de remplacement intra-mot)
        word_abbreviations = {
            'tél': 'téléphone', 'frigo': 'réfrigérateur', 'clim': 'climatiseur',
            'ordi': 'ordinateur', 'tab': 'tablette',
            'sneak': 'sneakers', 'basket': 'baskets',
            'fringues': 'vêtements', 'fringue': 'vêtement',
            'wai': 'oui', 'wé': 'oui', 'ouais': 'oui',
            'cho': 'chose', 'nan': 'non',
            'koi': 'quoi', 'kwa': 'quoi',
            'cmt': 'comment', 'cv': 'ça va',
            'tkt': 't\'inquiète', 'bcp': 'beaucoup', 'bn': 'bonne nuit',
            'cc': 'coucou', 'slt': 'salut',
            'stp': 's\'il te plaît', 'svp': 's\'il vous plaît',
        }
        for abbrev, full in word_abbreviations.items():
            text = re.sub(r'\b' + re.escape(abbrev) + r'\b', full, text)

        stop_word_pattern = (
            r"\b(je|j'ai|jai|fjai|ai|tu|veux|vuex|vue|voudrais|aimerais|cherche|donne|moi|montre|montrer|propose|proposer|disponible|"
            r"quel|quelle|quil|qu'il|quoi|model|modele|version|budget|prix|combien|prendre|prends|commande|commander|acheter|achete|es|as|suis|"
            r"trouve|trouve-moi|une|un|des|le|la|les|de|du|pour|qui|est|sont|et|ou|en|ca|sa|aller|ici|y|a|en|pas|plus|moins|"
            r"juste|seulement|alors|donc|maintenant|apres|avant|apresdemain|ok|daccord|d'accord|peux|peut|me|te|se|"
            r"fais|fait|fais-moi|fait-moi|voir|vois|voix|image|images|photo|photos|dis|dis-moi|"
            r"encore|aussi|sinon|peutetre|peut-etre|voila|voilà|bien|sur|sur|souvent|assez|trop|"
            r"ce|ces|cet|ca|sa|ça|ci|la|bas|merci|salut|bonjour|bonsoir|bjr|hey|coucou|svp|bon|mais|bof|hein|euh|"
            r"non|nas|n'a|na|spas|s'pas|va|vas|vaas|avais|avait|donner|donné|te|aller|ira|irait|peuvent|vont|avec|cela|cette|ceux|celui)\b"
        )

        # Détecte le budget et retire le montant du texte de recherche
        max_price = None
        min_price = None
        search_text = text
        # Gamme de prix "entre X et Y"
        range_match = re.search(r"entre\s+(\d[\d\s\.]{2,8})\s*(?:et|and|-|à|a)\s*(\d[\d\s\.]{2,8})", text, re.IGNORECASE)
        if range_match:
            try:
                min_val = float(range_match.group(1).replace(" ", "").replace(".", ""))
                max_val = float(range_match.group(2).replace(" ", "").replace(".", ""))
                if min_val >= 100 and max_val >= min_val:
                    min_price = min_val
                    max_price = max_val * 1.1
                    search_text = search_text[:range_match.start()] + " " + search_text[range_match.end():]
                    search_text = re.sub(r"\s+", " ", search_text).strip()
            except ValueError:
                pass
        if not max_price:
            # Budget : « 100000 », « 100k », « 100 k », « 100 milles », « 5000 f »
            price_match = re.search(
                r"(?<!\w)(\d[\d\s\.]{0,8})\s*(k|milles?|f|fcfa|francs|f cfa)\b|"
                r"(?<!\w)(\d[\d\s\.]{2,8})(?!\w)",
                text,
                re.IGNORECASE,
            )
            if price_match:
                raw_price = (price_match.group(1) or price_match.group(3) or "").replace(" ", "").replace(".", "")
                suffix = (price_match.group(2) or "").lower()
                try:
                    price_value = float(raw_price)
                    if suffix.startswith("k") or suffix.startswith("mille"):
                        price_value *= 1000
                    if price_value >= 1000:
                        max_price = price_value * 1.1
                        # Retire le montant du texte pour ne pas polluer la requête
                        search_text = search_text[:price_match.start()] + " " + search_text[price_match.end():]
                        search_text = re.sub(r"\s+", " ", search_text).strip()
                except ValueError:
                    max_price = None

        # Détection de couleur
        colors = {
            "rouge", "noir", "noire", "blanc", "blanche", "bleu", "bleue",
            "vert", "verte", "jaune", "rose", "violet", "violette",
            "marron", "gris", "grise", "orange", "beige", "or", "argent",
            "kaki", "camel", "bordeaux", "turquoise", "multicolore",
        }
        detected_colors = [w for w in text.split() if w in colors]

        # Détection de taille
        size_patterns = re.findall(r"\b(?:taille\s+)?(xs|s|m|l|xl|xxl|xxxl)\b", text, re.IGNORECASE)
        numeric_sizes = re.findall(r"\b(?:taille\s+)?(\d{2})\b", text)
        detected_sizes = [s.upper() for s in size_patterns] + numeric_sizes

        # Détection de tri
        sort_ascending = any(p in text for p in ("moins cher", "le moins cher", "par prix croissant", "pas cher"))
        sort_descending = any(p in text for p in ("le plus cher", "plus cher", "par prix decroissant", "par prix décroissant"))

        # Nettoie la requête
        # Détection multi-sujets AVANT stop_word removal: "telephone et aussi robe" → 2 recherches
        multi_queries = []
        if re.search(r"\b(?:et aussi|et|aussi|plus|également)\b", search_text, re.IGNORECASE):
            parts = re.split(r"\b(?:et aussi|et|aussi|plus|également)\b", search_text, flags=re.IGNORECASE)
            parts = [re.sub(stop_word_pattern, " ", p) for p in parts]
            parts = [re.sub(r"\s+", " ", p).strip() for p in parts if p.strip() and len(p.strip()) >= 3]
            if len(parts) >= 2:
                multi_queries = parts
        # « A ou B ou C » = liste d'alternatives explicites (marques, modèles)
        # → une recherche par option. « A ou B » seul reste une seule requête
        # (ambigu : « sac à main ou bandoulière » = un seul produit).
        if not multi_queries and len(re.findall(r"\bou\b", search_text, re.IGNORECASE)) >= 2:
            parts = re.split(r"\bou\b", search_text, flags=re.IGNORECASE)
            parts = [re.sub(stop_word_pattern, " ", p) for p in parts]
            parts = [re.sub(r"\s+", " ", p).strip() for p in parts if p.strip() and len(p.strip()) >= 3]
            if len(parts) >= 2:
                multi_queries = parts

        query = re.sub(stop_word_pattern, " ", search_text)
        query = re.sub(r"\s+", " ", query).strip()

        # Affirmation / mot court dans un contexte produit → reprend le dernier produit évoqué
        affirmation_words = {"oui", "yes", "yep", "ok", "d'accord", "daccord", "bien sûr", "bien sur", "c'est bon", "ca marche", "ça marche"}
        # Ne considère l'historique que pour les 3 derniers messages (pas toute la conversation)
        recent_history = " ".join(input_data.conversation_history[-3:]).lower() if input_data.conversation_history else ""
        has_product_context = any(w in recent_history for w in product_context_words)

        is_affirmation = text in affirmation_words or any(text.startswith(a + " ") for a in affirmation_words)

        # Fallback : si le message ne contient qu'un prix, une affirmation, ou un mot court dans un contexte produit,
        # on reprend le dernier produit évoqué par le client, en privilégiant le candidat le plus riche.
        fallback_mode = (
            not query
            or re.match(r"^\d+(\s*f(cfa)?)?$", query)
            or (is_affirmation and has_product_context)
            or (query and " " not in query and has_product_context)
        )
        if fallback_mode and input_data.conversation_history:
            best_candidate = ""
            for msg in reversed(input_data.conversation_history):
                if msg.lower().startswith("user:"):
                    last_user = msg.split(":", 1)[1].strip().lower()
                    candidate = re.sub(stop_word_pattern, " ", last_user)
                    candidate = re.sub(r"\s+", " ", candidate).strip()
                    # Ignore les prix restants
                    candidate = re.sub(r"\b\d{3,7}\b", " ", candidate).strip()
                    candidate = re.sub(r"\s+", " ", candidate).strip()
                    if not candidate or re.match(r"^\d+(\s*f(cfa)?)?$", candidate):
                        continue
                    # Garde le candidat le plus riche s'il contient le mot actuel
                    if not best_candidate or (query in candidate and len(candidate) > len(best_candidate)):
                        best_candidate = candidate
                    if best_candidate and query and query in best_candidate and len(best_candidate.split()) >= 2:
                        break
            if best_candidate and (not query or (query in best_candidate and len(best_candidate) > len(query))):
                query = best_candidate

        # Demande vague ("liste moi ce que tu as", "tout ce que tu trouves", budget seul)
        # sans produit explicite → reprend le dernier produit cité par le client.
        _listing_intent = re.search(
            r"\b(liste|lister|fouille|propose|proposer|montre|tout ce que|ce que tu as|ce que tu trouve|"
            r"donne.*choix|je ferai le choix|je choisi)|\d{3,7}\s*(f|fcfa|francs)?\b",
            text,
        )
        if (
            _listing_intent
            and not any(w in product_context_words for w in query.split())
            and input_data.conversation_history
        ):
            for msg in reversed(input_data.conversation_history[-8:]):
                if not msg.lower().startswith("user:"):
                    continue
                prev = _fix_typos(msg.split(":", 1)[1].strip().lower())
                found = [w for w in re.findall(r"[\wÀ-ÿ'-]+", prev) if w in product_context_words]
                if found:
                    query = " ".join(dict.fromkeys(found))
                    break

        # Détection de "autre" / "un autre" → re-chercher dans la même catégorie
        autre_phrases = ["autre", "un autre", "autre chose", "different", "différent", "pas celui", "pas celui-la", "pas celui là", "autre modele", "autre modèle"]
        is_autre_request = any(p in text for p in autre_phrases)
        if is_autre_request and input_data.conversation_history:
            # Cherche le dernier produit/catégorie mentionné dans l'historique
            for msg in reversed(input_data.conversation_history):
                if msg.lower().startswith("user:"):
                    last_user = msg.split(":", 1)[1].strip().lower()
                    # Applique les corrections de typos
                    last_user = _fix_typos(last_user)
                    candidate = re.sub(stop_word_pattern, " ", last_user)
                    candidate = re.sub(r"\s+", " ", candidate).strip()
                    candidate = re.sub(r"\b\d{3,7}\b", " ", candidate).strip()
                    candidate = re.sub(r"\s+", " ", candidate).strip()
                    # Retire "autre" du candidat
                    candidate = re.sub(r"\b(autre|autre chose|different|différent|pas celui la|pas celui)\b", " ", candidate).strip()
                    candidate = re.sub(r"\s+", " ", candidate).strip()
                    if candidate and len(candidate) >= 3:
                        query = candidate
                        break

        # Recherche de boutiques si le client en parle explicitement
        store_phrases = [
            "boutique", "magasin", "store", "shop", "vendeur",
            "adresse", "situé", "située", "localisé", "localisée",
            "près", "proche", "loin", "côté", "cote",
            "qui vend", "qui le vend", "qui les vend", "qui vend ca", "qui vend ça",
            "quelle boutique", "quel magasin", "qui propose",
        ]

        # Détecte si le client demande quelle boutique vend le produit proposé
        store_attribution_phrases = [
            "qui vend", "qui le vend", "qui les vend", "qui vend ca", "qui vend ça",
            "quelle boutique", "quel magasin", "qui propose",
            "boutique qui", "magasin qui", "la boutique qui", "le magasin qui",
            # Coordonnées / localisation de la boutique (ex. « donne moi les
            # coordonnées de la boutique » — doit citer nom + adresse, jamais refuser)
            "coordonnées", "coordonnee", "coordonnes",
            "adresse de la boutique", "adresse du magasin", "adresse de boutique",
            "adresse de sa boutique", "adresse de leur boutique",
            "contact de la boutique", "contact du magasin",
            "numéro de la boutique", "numero de la boutique",
            "localisée", "localiser la boutique", "localisation",
            "où se trouve", "ou se trouve", "où se situe", "ou se situe",
            "où est la boutique", "ou est la boutique",
            "où est le magasin", "ou est le magasin",
            "infos de la boutique", "info de la boutique",
        ]
        is_store_attribution = any(p in text for p in store_attribution_phrases)

        # Attend la mémoire client (lancée en arrière-plan au début de handle())
        memory_context = await memory_task

        if is_store_attribution:
            # Récupère le store_id depuis la mémoire client
            store_id_from_memory = None
            if memory_context:
                for line in memory_context.split("\n"):
                    if "derniere_boutique_id" in line.lower():
                        # Extract the value after the colon
                        parts = line.split(":", 1)
                        if len(parts) > 1:
                            store_id_from_memory = parts[1].strip().strip()
                            break
            # Repli : boutique du premier produit affiché dans la conversation
            # (la mémoire longue est écrite en fire-and-forget et peut être vide).
            if not store_id_from_memory and conv_ctx and conv_ctx.last_cards:
                _card_store = next((c.store_id for c in conv_ctx.last_cards if c.store_id), None)
                if _card_store:
                    store_id_from_memory = str(_card_store)

            if store_id_from_memory:
                try:
                    store_result = await self._tool_registry.execute(
                        "search_store",
                        ctx,
                        store_id=store_id_from_memory,
                    )
                    if store_result.success and store_result.data.stores:
                        store = store_result.data.stores[0]
                        store_name = store.nom
                        store_ville = store.ville or ""
                        reply = await self._call_ai([
                            ChatMessage(role="system", content=self.system_prompt),
                            ChatMessage(
                                role="user",
                                content=(
                                    f"Message du client : {input_data.message}\n\n"
                                    f"Infos boutique : {store_name} ({store_ville or 'adresse non précisée'})\n\n"
                                    f"{public_context}\n\n"
                                    f"Le client demande la boutique du produit proposé ou ses coordonnées. "
                                    f"Réponds en citant le nom et l'adresse : {store_name}"
                                    f"{', ' + store_ville if store_ville else ''}. "
                                    f"Reste concise (1 phrase)."
                                    f"{history_context}"
                                ),
                            ),
                        ])
                        reply = self._polish(reply)
                        if store.latitude is not None and store.longitude is not None:
                            reply += (
                                f"\n📍 Itinéraire : https://www.google.com/maps?q="
                                f"{store.latitude},{store.longitude}"
                            )
                        return AgentOutput(reply=reply, handled=True, tools_used=["search_store"])
                except Exception as exc:
                    logger.warning("store_info_failed", error=str(exc), correlation_id=input_data.correlation_id)
            
            # Fallback: cherche par nom de produit dans l'historique
            store_attribution_query = query
            if not store_attribution_query and input_data.conversation_history:
                for msg in reversed(input_data.conversation_history):
                    if msg.lower().startswith("user:"):
                        last_user = msg.split(":", 1)[1].strip().lower()
                        last_user = _fix_typos(last_user)
                        candidate = re.sub(stop_word_pattern, " ", last_user)
                        candidate = re.sub(r"\s+", " ", candidate).strip()
                        candidate = re.sub(r"\b\d{3,7}\b", " ", candidate).strip()
                        candidate = re.sub(r"\s+", " ", candidate).strip()
                        if candidate and len(candidate) >= 3:
                            store_attribution_query = candidate
                            break
            if store_attribution_query:
                store_result = await self._tool_registry.execute(
                    "search_store",
                    ctx,
                    query=store_attribution_query,
                )
                if store_result.success and store_result.data.stores:
                    stores = store_result.data.stores[:3]
                    store_summary = "\n".join(
                        f"- {s.nom} ({s.ville or 'adresse non précisée'})"
                        for s in stores
                    )
                    reply = await self._call_ai([
                        ChatMessage(role="system", content=self.system_prompt),
                        ChatMessage(
                            role="user",
                            content=(
                                f"Message du client : {input_data.message}\n\n"
                                f"Boutiques qui pourraient vendre ce produit :\n{store_summary}\n\n"
                                f"{public_context}\n\n"
                                "Le client demande la boutique du produit proposé ou ses coordonnées. "
                                "Réponds en citant le nom de la boutique et son adresse entre parenthèses. "
                                "Si plusieurs boutiques correspondent, cite la plus pertinente. "
                                "Reste concise (1-2 phrases)."
                            ),
                        ),
                    ])
                    reply = self._polish(reply)
                    return AgentOutput(reply=reply, handled=True, tools_used=["search_store"])
                else:
                    reply = await self._call_ai([
                        ChatMessage(role="system", content=self.system_prompt),
                        ChatMessage(
                            role="user",
                            content=(
                                f"Message du client : {input_data.message}\n\n"
                                f"{public_context}\n\n"
                                "Le client demande quelle boutique vend le produit que tu viens de proposer. "
                                "Dis que tu n'as pas l'information exacte sur la boutique, mais que le produit est disponible sur Mantota. "
                                "Reste concise (1 phrase)."
                            ),
                        ),
                    ])
                    reply = self._polish(reply)
                    return AgentOutput(reply=reply, handled=True, tools_used=[])

        if any(p in text for p in store_phrases):
            store_query = query
            if any(w in text for w in ("vetement", "vêtement", "habit", "mode")):
                store_query = "vetement"
            elif "restaurant" in text or "manger" in text or "repas" in text:
                store_query = "restaurant"
            elif (
                "boutique" in text
                and any(w in text for w in ("liste", "donne", "montre", "quelques", "disponible"))
            ):
                store_query = ""
            elif store_query and ("boutique" in store_query or "magasin" in store_query) and store_query.strip() in ("boutique", "magasin", "store"):
                store_query = ""
            elif not store_query:
                store_query = ""

            # On envoie une requête sans accent pour matcher les niches
            store_query = store_query.replace("é", "e").replace("è", "e").replace("ê", "e").replace("à", "a")

            store_result = await self._tool_registry.execute(
                "search_store",
                ctx,
                query=store_query,
            )
            if store_result.success and store_result.data.stores:
                stores = store_result.data.stores[:5]
                store_summary = "\n".join(
                    f"- {s.nom} ({s.ville or 'adresse non précisée'})"
                    for s in stores
                )
                reply = await self._call_ai([
                    ChatMessage(role="system", content=self.system_prompt),
                    ChatMessage(
                        role="user",
                        content=(
                            f"Message du client : {input_data.message}\n\n"
                            f"Souvenirs du client :\n{memory_context}\n\n"
                            f"Boutiques disponibles :\n{store_summary}\n\n"
                            f"{public_context}\n\n"
                            "Présente ces boutiques au client de façon naturelle, en 1 ou 2 phrases. "
                            "Ne donne pas de liste numérotée. "
                            "Ne mentionne que les boutiques listées ci-dessus. "
                            "Demande au client celle qui l'intéresse."
                        ),
                    ),
                ])
                reply = self._polish(reply)
                return AgentOutput(reply=reply, handled=True, tools_used=["search_store"])

        # Détecte un refus de produit pour ne pas le re-proposer
        rejection_phrases = [
            "pas demander", "pas demandé", "pas demande",
            "je ne veux pas", "je n'veux pas", "je veux pas",
            "pas de", "pas ca", "pas ça", "pas du",
            "je n'aime pas", "je n'aime pas", "n'aime pas",
            "pas sac", "pas telephone", "pas téléphone",
            "je n'ai pas", "je nai pas", "j'ai pas", "jai pas",
            "ce n'est pas", "c'est pas",
        ]
        rejected_product = any(r in text for r in rejection_phrases)

        # Détecte un rappel de conversation pour répondre depuis l'historique/mémoire
        recall_phrases = [
            "au debut", "au début", "rappelle", "souviens",
            "qu'est-ce que j'ai dit", "qu'est ce que j'ai dit",
            "qu'ai-je dit", "qu'ai je dit",
            "tu me rappelles", "tu me rapelle",
            "ce que j'ai dit",
            "tu me connais", "tu connais", "tu sais ce que je",
            "tu te souviens", "tu te rapelle", "tu te rappelles",
        ]
        recall_mode = any(r in text for r in recall_phrases)

        rejected_search = rejected_product and any(w in query for w in product_context_words)
        if rejected_search:
            query = ""

        # Mots vagues qui ne doivent pas être envoyés à la recherche produit.
        # Inclut les mots-outils et verbes de conversation : la recherche
        # mot-par-mot ferait sinon ILIKE '%dit%' → matche « traditionnelle ».
        vague_words = {
            # fillers déjà connus
            "truc", "chose", "machin", "genre", "aller", "irait", "ira", "peuvent",
            "vont", "avec", "cela", "cette", "ceux", "celui", "pourra", "pourrait",
            "va", "vas",
            # pronoms & déterminants
            "je", "jai", "j'", "tu", "il", "elle", "on", "nous", "vous", "ils",
            "elles", "moi", "toi", "lui", "eux", "leur", "leurs", "mien", "tien",
            "un", "une", "les", "des", "du", "de", "d'", "la", "le", "au", "aux",
            "en", "y", "ce", "cet", "ces", "mon", "ma", "mes", "ton", "ta", "tes",
            "son", "sa", "ses", "quel", "quels", "quelle", "quelles", "quoi",
            "autre", "autres", "meme", "même", "tout", "tous", "toute", "toutes",
            "rien", "personne", "chaque",
            # conjonctions & adverbes
            "et", "ou", "ni", "mais", "donc", "or", "car", "si", "comme", "que",
            "qui", "quand", "comment", "pourquoi", "combien", "pour", "par",
            "dans", "sur", "sous", "chez", "vers", "entre", "sans", "aussi",
            "tres", "très", "trop", "assez", "plutot", "plutôt", "presque",
            "encore", "toujours", "jamais", "parfois", "souvent", "deja", "déjà",
            "alors", "ensuite", "enfin", "juste", "seulement", "meme", "peu",
            "beaucoup", "moins", "plus", "tellement", "vraiment", "ensemble",
            "ici", "la", "là", "partout", "ailleurs", "dedans", "dehors",
            "oui", "non", "pas", "peut", "peut-être", "peutetre",
            # verbes de conversation courants (jamais des noms de produits)
            "suis", "es", "est", "sommes", "etes", "êtes", "sont", "être", "etre",
            "ai", "as", "a", "avons", "avez", "ont", "avoir", "avais", "avait",
            "dit", "dits", "dis", "dise", "dites", "dire", "disait", "disent",
            "voulais", "voulait", "vouloir", "voudrais", "voudrait", "veut",
            "veulent", "veux", "aimerais", "aimerait", "souhaite", "souhaiter",
            "peux", "pourrais", "pouvez", "pouvoir", "doit", "dois", "devoir",
            "fais", "fait", "faites", "faire", "faisons", "font", "fera",
            "ferait", "feront", "ferons", "donne", "donnes", "donnez", "donner",
            "prend", "prends", "prenez", "prendre", "prenais", "prenait",
            "cherche", "cherches", "cherchez", "chercher", "cherchais",
            "trouve", "trouves", "trouvez", "trouver", "montre", "montres",
            "montrez", "montrer", "montre-moi", "voir", "vois", "voyez",
            "envoie", "envoies", "envoyez", "envoyer", "envoyais",
            "laisse", "laisses", "laissez", "laisser", "oublie", "oublies",
            "essaie", "essaye", "essayez", "essayer", "essai", "essais",
            "ecoute", "écoute", "ecoutes", "écoutes", "regarde", "regardes",
            "attends", "attendez", "viens", "venez", "reponds", "réponds",
            "besoin", "envie", "merci", "stp", "svp", "plait", "plaît",
            "bonjour", "salut", "bonsoir", "coucou", "hello", "wsh", "slt",
            "cc", "yo", "hey", "ok", "ouais", "ouep", "daccord", "dac",
            "bon", "bonne", "bah", "ben", "bref", "du", "coup", "genre",
        } - product_context_words
        # Retire les mots vagues de la query
        query = " ".join(w for w in query.split() if w not in vague_words).strip()
        
        # Détecte les demandes d'accessoire/complément : si le client dit
        # "aller avec", "pour", "qui ira", on ne cherche pas le produit principal
        accessory_request_patterns = ["aller avec", "pour aller", "qui ira", "qui irait", "pour aller avec", "avec cette", "avec ma", "avec la", "avec le"]
        is_accessory_request = any(p in text.lower() for p in accessory_request_patterns)
        if is_accessory_request:
            # Retire les mots produit de la query (robe, téléphone, etc.)
            query = " ".join(w for w in query.split() if w not in product_context_words).strip()
        
        query_has_real_product = any(w in product_context_words for w in query.split()) if query else False
        
        # Doit-on lancer une recherche ?
        # Cas spécial: "le moins cher" / "le plus cher" sans produit → recherche générale triée
        _is_sort_only = (
            ("le moins cher" in text or "le plus cher" in text)
            and not query_has_real_product
        )
        search_triggered = (
            not recall_mode
            and not rejected_search
            and (
                any(p in text for p in search_phrases)
                or re.search(r"\b\d{2,7}\b", text)
                or (query and has_product_context)
                or _is_sort_only
            )
            and (query_has_real_product or _is_sort_only)
        )

        if not search_triggered:
            # Questions ouvertes : toujours GPT
            # ... (géré ci-dessous)
            pass
        else:
            # Lance la recherche avec fallback par mot + variantes accentuées/pluriel
            products = None
            if _is_sort_only and not query:
                query = "produit"
            if multi_queries:
                queries = multi_queries
            else:
                queries = [query]
            # Si la query contient 'accessoire', on ne cherche que ce mot
            # pour éviter de remonter le produit qu'on veut accessoriser
            accessory_terms = {"accessoire", "accessoires", "bijoux", "bijou", "sac", "sacs", "chaussure", "chaussures", "boucle", "boucles", "collier", "bracelet", "bague"}
            search_words = query.split()
            if any(w in accessory_terms for w in search_words):
                search_words = [w for w in search_words if w in accessory_terms or w not in product_context_words]
            for w in search_words:
                if len(w) <= 2:
                    continue
                variants = {w}
                # Pluriel — ne jamais tronquer un mot finissant par s
                if not w.endswith("s"):
                    variants.add(w + "s")
                # Variantes accentuées
                if "é" not in w and "è" not in w and "e" in w:
                    # 1er e seulement
                    first = w.replace("e", "é", 1)
                    variants.add(first)
                    if not w.endswith("s"):
                        variants.add(first + "s")
                    # tous les e sauf le dernier caractère (ex: téléphone)
                    all_but_last = "".join(
                        "é" if i < len(w) - 1 and c == "e" else c
                        for i, c in enumerate(w)
                    )
                    if all_but_last != w and all_but_last != first:
                        variants.add(all_but_last)
                        if not w.endswith("s"):
                            variants.add(all_but_last + "s")
                # Déaccentue pour matcher l'anglais/sans accent
                if "é" in w or "è" in w:
                    variants.add(w.replace("é", "e").replace("è", "e"))
                # Synonymes — "portable" = "téléphone" en français d'Afrique
                synonyms = {
                    "portable": {"telephone", "téléphone", "phone", "smartphone"},
                    "portables": {"telephone", "téléphone", "telephones", "téléphones", "phone", "phones", "smartphone", "smartphones"},
                    "chaussure": {"baskets", "sandales", "sneakers", "bottines", "mocassins", "souliers"},
                    "chaussures": {"baskets", "sandales", "sneakers", "bottines", "mocassins", "souliers"},
                }
                if w in synonyms:
                    variants.update(synonyms[w])
                queries.extend(variants)
            seen_ids = set()
            # Lance toutes les recherches en parallèle au lieu de séquentiellement
            async def _search_one(q: str):
                if not q:
                    return None
                search_kwargs = {"query": q, "store_id": None, "limit": 5}
                if max_price is not None:
                    search_kwargs["max_price"] = max_price
                if min_price is not None:
                    search_kwargs["min_price"] = min_price
                search_kwargs.update(location_kwargs(input_data))
                try:
                    return await self._tool_registry.execute("search_products", ctx, **search_kwargs)
                except Exception:
                    return None

            results = await asyncio.gather(*[_search_one(q) for q in queries])
            tools_used = ["search_products"]
            products = None
            for search_result in results:
                if search_result and search_result.success:
                    for p in search_result.data.products:  # type: ignore[union-attr]
                        if p.id not in seen_ids:
                            if products is None:
                                products = []
                            products.append(p)
                            seen_ids.add(p.id)

            # Tri des résultats par prix si demandé
            if products:
                if sort_ascending:
                    products.sort(key=lambda p: p.prix)
                elif sort_descending:
                    products.sort(key=lambda p: p.prix, reverse=True)
                else:
                    products = sort_by_scope(products)

            if products:
                cards = [
                    ProductCard(
                        id=p.id,
                        name=p.nom,
                        price=f"{p.prix:,.0f}".replace(",", " ") + " F",
                        raw_price=p.prix,
                        stock=p.stock,
                        image_url=p.image_url,
                        store_id=p.store_id,
                        category=p.category,
                        description=p.description,
                    )
                    for p in products[:5]
                ]
                products_summary = "\n".join(product_line(p) for p in products[:5])
                location_info = location_note(products[:5], input_data)

                # Sauvegarde des faits pertinents — fire-and-forget (ne bloque pas la réponse)
                save_tasks = [
                    self._save_client_fact(
                        input_data, ctx,
                        "produit_interet",
                        ", ".join(p.nom for p in products[:3]),
                        "observed",
                    ),
                ]
                if products and products[0].store_id:
                    save_tasks.append(
                        self._save_client_fact(
                            input_data, ctx,
                            "derniere_boutique_id",
                            str(products[0].store_id),
                            "observed",
                        )
                    )
                if max_price:
                    budget_label = f"{max_price:.0f} FCFA"
                    if min_price:
                        budget_label = f"{min_price:.0f} - {max_price:.0f} FCFA"
                    save_tasks.append(
                        self._save_client_fact(
                            input_data, ctx,
                            "budget_max",
                            budget_label,
                            "observed",
                        )
                    )
                brand = self._extract_brand(text)
                if brand:
                    save_tasks.append(
                        self._save_client_fact(input_data, ctx, "marque_interet", brand, "observed")
                    )
                asyncio.ensure_future(asyncio.gather(*save_tasks, return_exceptions=True))  # fire-and-forget

                relevant_memory = self._filter_relevant_memory(memory_context, query)
                # Enrichit le prompt avec les critères détectés
                criteria_info = ""
                if detected_colors:
                    criteria_info += f"Couleur recherchée : {', '.join(detected_colors)}. "
                if detected_sizes:
                    criteria_info += f"Taille recherchée : {', '.join(detected_sizes)}. "
                if min_price and max_price:
                    criteria_info += f"Budget : entre {min_price:.0f} et {max_price:.0f} FCFA. "
                elif max_price:
                    criteria_info += f"Budget max : {max_price:.0f} FCFA. "
                if sort_ascending:
                    criteria_info += "Tri : du moins cher au plus cher. "
                elif sort_descending:
                    criteria_info += "Tri : du plus cher au moins cher. "
                criteria_info += location_info
                reply = await self._call_ai([
                    ChatMessage(role="system", content=_LIGHT_PROMPT),
                    ChatMessage(
                        role="user",
                        content=(
                            f"Message du client : {input_data.message}\n\n"
                            f"Souvenirs du client :\n{relevant_memory}\n\n"
                            f"Produits disponibles :\n{products_summary}\n\n"
                            f"{criteria_info}\n"
                            "Présente ces produits au client, de façon naturelle. "
                            "Ne fais pas de liste numérotée. "
                            "Si le client a demandé une couleur ou taille spécifique, mentionne-la dans ta présentation. "
                            "Si le client a proposé un prix, compares-le au prix affiché et expliques que c'est le prix sur le site. "
                            "Demande lequel l'intéresse."
                        ),
                    ),
                ], max_tokens=300)
                reply = self._polish(reply)
                return AgentOutput(reply=reply, handled=True, tools_used=tools_used, cards=cards)

            # Aucun produit trouvé — SANS mémoire pour éviter de mentionner d'anciens produits
            kb_context = await self._knowledge_context(ctx, input_data.message)
            if kb_context:
                tools_used.append("search_knowledge")
                no_product_hint = (
                    "Le message ressemble à une question d'information. Réponds UNIQUEMENT à partir "
                    "de la base de connaissances ci-dessous ; si elle ne contient pas la réponse, "
                    "dis-le honnêtement sans inventer."
                )
            else:
                no_product_hint = (
                    "Aucun produit ne correspond à cette recherche sur le site public. "
                    "Réponds de façon naturelle : dis que tu n'as pas trouvé, demande plus de détails "
                    "(marque, modèle, type, nom de boutique) et propose de chercher à nouveau. "
                    "NE mentionne JAMAIS un produit d'une recherche précédente."
                )
            reply = await self._call_ai([
                ChatMessage(role="system", content=_LIGHT_PROMPT),
                ChatMessage(
                    role="user",
                    content=(
                        f"Message du client : {input_data.message}\n\n"
                        f"{public_context}\n\n"
                        f"{kb_context}\n\n"
                        f"{no_product_hint}"
                        f"{history_context}"
                    ),
                ),
            ], max_tokens=200)
            reply = self._polish(reply)
            return AgentOutput(reply=reply, handled=True, tools_used=tools_used)

        # Détection "tu vends quoi" / "tu as quoi" → recherche générale
        catalog_phrases = [
            "tu vends quoi", "tu vend quoi", "tu as quoi", "tu as quoi ici",
            "c'est quoi ton catalogue", "montre ton catalogue", "tu proposes quoi",
            "quels produits", "quelle categorie", "quelles categories",
            "tu as quelles categories", "tu fais quoi",
        ]
        is_catalog_request = any(p in text for p in catalog_phrases)
        if is_catalog_request:
            # Lance une recherche générale pour montrer ce qui existe
            general_result = await self._tool_registry.execute(
                "search_products",
                ctx,
                query="a",
                store_id=None,
                limit=5,
            )
            if general_result.success and general_result.data.products:
                cats = list(set(p.category for p in general_result.data.products if p.category))
                products_summary = "\n".join(
                    f"- {p.nom} : {p.prix:.0f} FCFA ({p.category})"
                    for p in general_result.data.products[:5]
                )
                cats_text = ", ".join(cats) if cats else "divers produits"
                reply = await self._call_ai([
                    ChatMessage(role="system", content=_LIGHT_PROMPT),
                    ChatMessage(
                        role="user",
                        content=(
                            f"Message du client : {input_data.message}\n\n"
                            f"Catégories disponibles : {cats_text}\n"
                            f"Produits disponibles :\n{products_summary}\n\n"
                            f"{public_context}\n\n"
                            "Le client demande ce que tu vends. Présente les catégories disponibles "
                            "et quelques produits phares. Reste concise (2-3 phrases). "
                            "Demande ce qui l'intéresse."
                            f"{history_context}"
                        ),
                    ),
                ], max_tokens=200)
                reply = self._polish(reply)
                cards = [
                    ProductCard(
                        id=p.id, name=p.nom,
                        price=f"{p.prix:,.0f}".replace(",", " ") + " F",
                        raw_price=p.prix, stock=p.stock,
                        image_url=p.image_url, store_id=p.store_id,
                        category=p.category, description=p.description,
                    )
                    for p in general_result.data.products[:5]
                ]
                return AgentOutput(reply=reply, handled=True, tools_used=["search_products"], cards=cards)

        # Détection "promotions" / "promos"
        promo_phrases = [
            "promotion", "promotions", "promo", "promos", "solde", "soldes",
            "reduction", "réduction", "offre", "offres", "bon plan",
        ]
        is_promo_request = any(p in text for p in promo_phrases)
        if is_promo_request:
            try:
                campaign_result = await self._tool_registry.execute(
                    "get_campaign",
                    ctx,
                    store_id=input_data.store_id,
                )
                if campaign_result.success and campaign_result.data:
                    reply = await self._call_ai([
                        ChatMessage(role="system", content=self.system_prompt),
                        ChatMessage(
                            role="user",
                            content=(
                                f"Message du client : {input_data.message}\n\n"
                                f"Campagnes actives : {campaign_result.data}\n\n"
                                f"{public_context}\n\n"
                                "Le client demande les promotions. Présente les offres disponibles "
                                "de façon naturelle. Reste concise (2-3 phrases)."
                                f"{history_context}"
                            ),
                        ),
                    ])
                    reply = self._polish(reply)
                    return AgentOutput(reply=reply, handled=True, tools_used=["get_campaign"])
            except Exception:
                pass
            # Fallback si pas de campagne trouvée
            reply = await self._call_ai([
                ChatMessage(role="system", content=self.system_prompt),
                ChatMessage(
                    role="user",
                    content=(
                        f"Message du client : {input_data.message}\n\n"
                        f"{public_context}\n\n"
                        "Le client demande des promotions. Dis-lui que tu n'as pas de promotion "
                        "active en ce moment, mais demande-lui ce qu'il cherche pour l'aider à trouver "
                        "le meilleur rapport qualité-prix. "
                        "Reste concise (1-2 phrases) et demande ce qu'il cherche."
                        f"{history_context}"
                    ),
                ),
            ])
            reply = self._polish(reply)
            return AgentOutput(reply=reply, handled=True, tools_used=[])

        # Détection "devises" / "monnaie" / "pays"
        currency_phrases = [
            "devise", "devises", "monnaie", "quelle monnaie",
            "fcfa", "xof", "xaf", "naira", "usd", "eur", "dollar",
            "tu accepte.*paiement", "momo", "mobile money",
            "quel pays", "tu livre.*pays", "quel.*devise",
        ]
        is_currency_request = any(re.search(p, text) for p in currency_phrases)
        if is_currency_request and re.search(r"\d{3,}", text) and not re.search(r"devise|monnaie|accepte|quel", text):
            is_currency_request = False
        if is_currency_request:
            try:
                curr_result = await self._tool_registry.execute(
                    "get_currencies",
                    ctx,
                )
                if curr_result.success and curr_result.data:
                    curr_list = ", ".join(
                        f"{c.code} ({c.symbol}) — {c.name}"
                        for c in curr_result.data.currencies[:8]
                    )
                    reply = await self._call_ai([
                        ChatMessage(role="system", content=self.system_prompt),
                        ChatMessage(
                            role="user",
                            content=(
                                f"Message du client : {input_data.message}\n\n"
                                f"Devises supportées : {curr_list}\n\n"
                                f"{public_context}\n\n"
                                "Le client demande quelles devises/monnaies sont acceptées. "
                                "Présente les devises disponibles de façon claire. "
                                "Reste concise (2-3 phrases)."
                                f"{history_context}"
                            ),
                        ),
                    ])
                    reply = self._polish(reply)
                    return AgentOutput(reply=reply, handled=True, tools_used=["get_currencies"])
            except Exception:
                pass

        # Détection de frustration
        frustration_phrases = [
            "merd", "merde", "tu ne comprend", "tu comprend pas", "tu ne comprends pas",
            "tu comprends rien", "tu comprend rien", "nul", "inutile", "ça sert a rien",
            "ca sert a rien", "perdu", "j'abandonne", "j abandonne",
        ]
        is_frustrated = any(p in text for p in frustration_phrases)
        if is_frustrated:
            reply = await self._call_ai([
                ChatMessage(role="system", content=self.system_prompt),
                ChatMessage(
                    role="user",
                    content=(
                        f"Message du client : {input_data.message}\n\n"
                        f"{public_context}\n\n"
                        "Le client est frustré et pense que tu ne comprends pas sa demande. "
                        "Présente tes excuses, reformule ce que tu as compris de sa demande, "
                        "et demande-lui de clarifier. Sois empathique et concise (1-2 phrases)."
                        f"{history_context}"
                    ),
                ),
            ])
            reply = self._polish(reply)
            return AgentOutput(reply=reply, handled=True, tools_used=[])

        # ── Follow-up contextuel : "ok", "oui", "je le prends", "combien" etc. ──
        fu_ctx = input_data.conversation_context
        if fu_ctx and fu_ctx.product_name:
            followup_confirm = [
                'je le prends', 'je la prends', 'je veux celui', 'vas y', 'vas-y',
                'go', 'oui', 'ok', 'd accord', 'd\'accord', 'parfait', 'super',
                'génial', 'genial', 'volontiers', 'c est bon', 'c\'est bon',
            ]
            followup_question = [
                'combien', 'c est combien', 'c\'est combien', 'le prix', 'disponible',
                'en stock', 'comment je paie', 'je peux payer', 'je paie',
            ]
            followup_download = [
                'télécharger', 'telecharger', 'download', 'lien', 'app',
                'où télécharger', 'ou telecharger', 'installer',
            ]
            
            if any(p in text for p in followup_confirm):
                reply = await self._call_ai([
                    ChatMessage(role="system", content=_LIGHT_PROMPT),
                    ChatMessage(
                        role="user",
                        content=(
                            f"Message du client : {input_data.message}\n\n"
                            f"Le client confirme qu'il veut acheter : {fu_ctx.product_name} (prix: {fu_ctx.product_price or 'N/A'}).\n\n"
                            f"Accueille sa décision avec enthousiasme et demande-lui la quantité et sa ville de livraison "
                            f"pour finaliser la commande. Réponds en 1-2 phrases."
                            f"{history_context}"
                        ),
                    ),
                ], max_tokens=150)
                reply = self._polish(reply)
                _fu_cards = conv_ctx.last_cards if conv_ctx and conv_ctx.last_cards else None
                return AgentOutput(reply=reply, handled=True, tools_used=[], cards=_fu_cards)

            if any(p in text for p in followup_question):
                reply = await self._call_ai([
                    ChatMessage(role="system", content=_LIGHT_PROMPT),
                    ChatMessage(
                        role="user",
                        content=(
                            f"Message du client : {input_data.message}\n\n"
                            f"Le client pose une question sur le produit : {fu_ctx.product_name} (prix: {fu_ctx.product_price or 'N/A'}).\n\n"
                            f"Réponds à sa question de façon naturelle et concise (1-2 phrases). "
                            f"Si il demande le prix, rappelle le prix. Si il demande la disponibilité, dis-le. "
                            f"Si il demande comment payer, explique que tu vas créer la commande et envoyer un lien de paiement."
                            f"{history_context}"
                        ),
                    ),
                ], max_tokens=150)
                reply = self._polish(reply)
                _fq_cards = conv_ctx.last_cards if conv_ctx and conv_ctx.last_cards else None
                return AgentOutput(reply=reply, handled=True, tools_used=[], cards=_fq_cards)

        # Questions ouvertes : toujours GPT
        ordering_phrases = [
            'commander ici', 'commande ici', 'je peux commander', 'je peut commander',
            'je veux commander', 'je voudrais commander', 'passer commande', 'passe commande',
            'payer ici', 'acheter ici', 'je commande', 'je passe commande',
        ]
        if any(p in text for p in ordering_phrases):
            reply = await self._call_ai([
                ChatMessage(
                    role="system",
                    content=(
                        "Tu es Tracy, une vendeuse de l'équipe Mantota. Tu parles comme une vraie commerçante, "
                        "chaleureuse et directe. Le client est sur le site public de Mantota. "
                        "Sur le site public, le client PEUT commander et payer directement. "
                        "Quand le client veut commander, demande-lui la quantité et sa ville de livraison. "
                        "Ne mentionne JAMAIS l'app Mantota. "
                        "Réponds en UNE OU DEUX PHRASES maximum."
                    ),
                ),
                ChatMessage(
                    role="user",
                    content=(
                        f"Message du client : {input_data.message}\n\n"
                        f"Souvenirs du client :\n{memory_context}"
                        f"{history_context}"
                    ),
                ),
            ])
            reply = self._polish(reply)
            return AgentOutput(reply=reply, handled=True, tools_used=[])

        first_user_message = ""
        if recall_mode:
            for msg in (input_data.conversation_history or []):
                if msg.lower().startswith("user:"):
                    first_user_message = msg.split(":", 1)[1].strip()
                    break
        recall_hint = (
            f"\n\nLe client demande un rappel. "
            f"Son premier message était : \"{first_user_message}\". "
            f"Réponds en citant ce premier message et dis ce qu'il cherchait."
            if recall_mode and first_user_message
            else ""
        )

        relevant_memory = self._filter_relevant_memory(memory_context, query) if query else memory_context
        reply = await self._call_ai([
            ChatMessage(role="system", content=self.system_prompt),
            ChatMessage(
                role="user",
                content=(
                    f"Message du client : {input_data.message}\n\n"
                    f"Souvenirs du client :\n{relevant_memory}\n\n"
                    f"{public_context}"
                    f"{history_context}"
                    f"{recall_hint}"
                ),
            ),
        ], max_tokens=300)

        logger.info(
            "agent_reply_generated_public",
            agent=self.name,
            correlation_id=input_data.correlation_id,
        )

        reply = self._polish(reply)
        _fallback_cards = conv_ctx.last_cards if conv_ctx and conv_ctx.last_cards else None
        return AgentOutput(reply=reply, handled=True, tools_used=[], cards=_fallback_cards)

    async def _handle_image(self, input_data: AgentInput, ctx: ToolContext) -> AgentOutput:
        """Traite un message contenant une photo.

        1. Un fournisseur IA capable de vision décrit le produit visible.
        2. La description sert de requête à search_products.
        3. Si l'analyse est impossible, réponse honnête — on ne prétend pas avoir vu.
        """
        caption = ""
        try:
            img = input_data.image or ""
            if not img.startswith("data:"):
                img = f"data:image/jpeg;base64,{img}"
            response = await self._ai_gateway.complete_vision(
                [
                    ChatMessage(
                        role="user",
                        content=(
                            "Décris en une courte phrase le produit principal visible "
                            "sur cette image (type, marque, couleur, modèle si lisible). "
                            "Réponds UNIQUEMENT avec la description, sans préambule. "
                            "Si ce n'est pas un produit, réponds 'pas de produit'."
                        ),
                        images=[img],
                    ),
                ],
                max_tokens=60,
            )
            caption = (response.content or "").strip().strip('"').strip("'")
        except Exception as exc:
            logger.warning(
                "image_describe_failed",
                error=str(exc),
                correlation_id=input_data.correlation_id,
            )

        if not caption or caption.lower().rstrip(".") == "pas de produit":
            return AgentOutput(
                reply=(
                    "J'ai bien reçu ta photo, mais je n'arrive pas à identifier "
                    "le produit dessus. Décris-le-moi en quelques mots "
                    "(ex: chaussures Nike noires, téléphone Samsung…) et je le cherche !"
                ),
                handled=True,
                tools_used=[],
            )

        search_kwargs: dict[str, Any] = {
            "query": caption,
            "store_id": None if input_data.store_id == "public" else input_data.store_id,
            "limit": 5,
        }
        search_kwargs.update(location_kwargs(input_data))
        try:
            result = await self._tool_registry.execute("search_products", ctx, **search_kwargs)
        except Exception as exc:
            logger.warning("image_search_failed", error=str(exc), correlation_id=input_data.correlation_id)
            result = None

        if result and result.success and result.data.products:  # type: ignore[union-attr]
            products = sort_by_scope(list(result.data.products))[:5]  # type: ignore[union-attr]
            cards = [
                ProductCard(
                    id=p.id,
                    name=p.nom,
                    price=f"{p.prix:,.0f}".replace(",", " ") + " F",
                    raw_price=p.prix,
                    stock=p.stock,
                    image_url=p.image_url,
                    store_id=p.store_id,
                    category=p.category,
                    description=p.description,
                )
                for p in products
            ]
            products_summary = "\n".join(product_line(p) for p in products)
            location_info = location_note(products, input_data)
            reply = await self._call_ai([
                ChatMessage(role="system", content=_LIGHT_PROMPT),
                ChatMessage(
                    role="user",
                    content=(
                        f"Le client a envoyé une photo (description : {caption}) "
                        f"avec le message : {input_data.message}\n\n"
                        f"Produits trouvés :\n{products_summary}\n\n"
                        f"{location_info}"
                        "Dis brièvement ce que tu vois sur la photo, puis présente les produits "
                        "proches en 1-2 phrases, sans liste numérotée. "
                        "Si aucun ne correspond vraiment, dis-le honnêtement. "
                        "Demande lequel l'intéresse."
                    ),
                ),
            ], max_tokens=250)
            reply = self._polish(reply)
            return AgentOutput(reply=reply, handled=True, tools_used=["search_products"], cards=cards)

        return AgentOutput(
            reply=(
                f"Sur ta photo, je vois : {caption}. "
                "Je n'ai pas trouvé exactement ça en boutique pour l'instant. "
                "Tu veux que je cherche quelque chose de similaire ?"
            ),
            handled=True,
            tools_used=["search_products"],
        )

    async def _get_client_memory(self, input_data: AgentInput, ctx: ToolContext) -> str:
        """Récupère les souvenirs client récents pour ancrer la réponse."""
        entity_id = input_data.customer_id or input_data.store_id
        if not entity_id:
            return ""
        try:
            search_result = await self._tool_registry.execute(
                "search_memory",
                ctx,
                scope="client",
                entity_id=entity_id,
            )
            if search_result.success and search_result.data.entries:
                # Garde les 8 derniers, triés par updated_at desc côté Mantota
                return "\n".join(
                    f"  - {e.key} : {e.value}" for e in search_result.data.entries[:8]
                )
        except Exception as exc:
            logger.warning("memory_search_failed", error=str(exc), correlation_id=input_data.correlation_id)
        return ""

    def _filter_relevant_memory(self, memory_context: str, query: str) -> str:
        """Ne garde que les souvenirs pertinents par rapport à la requête courante.
        
        Si la requête contient un mot-clé produit (lit, canapé, téléphone...),
        on ne garde que les souvenirs qui contiennent un mot en commun.
        Si la requête ne contient pas de mot-clé produit, on retourne la mémoire complète.
        """
        if not memory_context or not query:
            return "" if not query else memory_context
        
        query_words = set(query.lower().split())
        # Mots produits dans la requête
        product_words_in_query = query_words & _PRODUCT_CONTEXT_WORDS
        
        if not product_words_in_query:
            # Pas de mot produit dans la requête → pas de mémoire pertinente
            return ""
        
        # La requête contient un mot produit → filtre les souvenirs
        # qui contiennent au moins un mot en commun avec la requête
        relevant_lines = []
        for line in memory_context.split("\n"):
            line_lower = line.lower()
            # Garde les souvenirs de budget/marque seulement si ils mentionnent
            # un mot de la requête ou un mot produit commun
            if any(w in line_lower for w in product_words_in_query):
                relevant_lines.append(line)
            elif "budget" in line_lower and product_words_in_query:
                # Ne garde le budget que si un produit de la même catégorie est dans la mémoire
                # et que la requête correspond à cette catégorie
                pass  # On ne garde pas le budget si la catégorie change
            elif any(w in line_lower for w in query_words):
                relevant_lines.append(line)
        
        return "\n".join(relevant_lines) if relevant_lines else ""

    async def _save_client_fact(
        self,
        input_data: AgentInput,
        ctx: ToolContext,
        key: str,
        value: str,
        source: str = "observed",
    ) -> None:
        """Enregistre un fait utile sur le client pour les prochains échanges."""
        entity_id = input_data.customer_id or input_data.store_id
        if not entity_id or not value.strip():
            return
        try:
            await self._tool_registry.execute(
                "save_memory",
                ctx,
                scope="client",
                entity_id=entity_id,
                key=key,
                value=value,
                source=source,
            )
        except Exception as exc:
            logger.warning("memory_save_failed", error=str(exc), correlation_id=input_data.correlation_id)

    def _extract_brand(self, text: str) -> str:
        """Extrait la marque éventuelle du message."""
        brands = ["samsung", "iphone", "tecno", "infinix", "xiaomi", "redmi", "huawei"]
        for brand in brands:
            if brand in text:
                return brand
        return ""


    def _polish(self, text: str) -> str:
        """Assainit la réponse : mots interdits, longueur, action finale."""
        import re

        # Normalise les apostrophes
        text = text.replace("'", "'").strip()

        # Intercepte les messages d'indisponibilité ou de téléchargement d'app
        # que GPT génère parfois malgré les instructions
        unavailable_patterns = [
            r"t[ée]l[ée]charge[sz]?\s+l['\s]?app",
            r"t[ée]l[ée]charge[sz]?\s+mantota",
            r"je ne suis pas disponible",
            r"pas disponible pour le moment",
            r"t[ée]l[ée]charge[sz]?\s+l'application",
            r"download the app",
            r"download mantota",
        ]
        if any(re.search(p, text, re.IGNORECASE) for p in unavailable_patterns):
            text = "Je n'ai pas trouvé ce que tu cherches pour le moment. Peux-tu me donner plus de détails (marque, modèle, type) ? Je vais chercher à nouveau."

        # Supprime les intros bannies en début de réponse
        text = re.sub(r"^(Salut|Bonjour|Hey|Coucou)[,!?\s]*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"^(Écoute|Ecoute|écoute|ecoute),?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"^(D'accord|Daccord|d'accord|daccord),?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"^(Pour)\s+", "", text, flags=re.IGNORECASE)

        # Liste des mots/suffixes à bannir
        forbidden = [
            "en tant qu'ia", "en tant qu'assistant", "je suis une ia", "je suis un modèle",
            "plonger", "plonge", "explorer", "explore", "découvrir", "découvre", "découvrir",
            "naviguer", "navigue", "immersif", "journey", "voyage",
            "n'hésite pas", "bien sûr", "je suis ravie", "c'est un plaisir",
            "merci de ta confiance", "comment puis-je t'aider aujourd'hui",
        ]
        for word in forbidden:
            text = re.sub(rf"\b{re.escape(word)}\b", "", text, flags=re.IGNORECASE)

        # Nettoie les espaces multiples et virgules restantes
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"\s,", ",", text)
        text = re.sub(r",,+", ",", text)
        text = re.sub(r"\s+\.", ".", text)
        text = text.strip()

        # Découpe en phrases
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]

        # Garde max 2-3 phrases
        if len(sentences) > 3:
            sentences = sentences[:3]

        # S'assure qu'il y a une phrase d'action à la fin si possible
        closing = ["Je te crée la commande ?", "Tu veux que je te trouve ça ?", "Dis-moi ce que tu cherches.", "Je te le mets de côté ?"]
        last_sentence = sentences[-1] if sentences else ""
        has_call_to_action = any(c in last_sentence for c in ["?", "!", "intéresse", "choix", "penses", "fais-moi", "fais savoir", "lequel", "laquelle"])
        has_forbidden = any(c in last_sentence for c in ["commande", "trouve", "côté"])
        if sentences and not (has_call_to_action or has_forbidden):
            sentences.append("Dis-moi ce que tu cherches.")

        # Garde max 3 phrases après ajout
        sentences = sentences[:3]
        return " ".join(sentences)
