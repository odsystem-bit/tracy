"""CatalogAgent (docs/tracy/03-AGENTS.md).

Rôle : Gestionnaire du catalogue produit et création de boutique.
Responsabilité : Répondre aux demandes du vendeur sur son catalogue (ajout,
modification, recherche, disponibilité) et gérer la création de boutique
(physique ou en ligne) exprimées en langage naturel.
Gère aussi la configuration des règles commerciales (négociation, devise).

Outils autorisés : search_products, search_catalog, search_store, create_store,
    get_shop_config, update_shop_config.

Limites : ne modifie jamais le catalogue sans confirmation explicite du vendeur
pour les actions destructives (suppression).

Autonomie V1 : Autonome sauf actions destructives (confirmation requise).

Comportement IA (docs/tracy/05-AI_BEHAVIOR.md) :
- Ton vendeur : collègue de confiance, factuel, proactif.
- Présente un nombre limité de produits pertinents, jamais une liste exhaustive.
- Alerte proactivement sur les ruptures de stock.
- Création de boutique : demande d'abord physique ou en ligne.
  Si physique → GPS auto + photo devanture obligatoires.
  Si en ligne → pas besoin de localisation ni photo.
- Configuration boutique : guide le vendeur question par question pour définir
  ses règles de négociation (marge min, réduction premier achat, etc.).
"""

from __future__ import annotations

import json
import re

from app.agents.base import AgentAutonomy, AgentInput, AgentOutput, BaseAgent
from app.ai_gateway.base import ChatMessage
from app.logging_config import bind_context, get_logger
from app.tools.base import ToolContext

logger = get_logger(__name__)

SYSTEM_PROMPT = (
    "Tu es Tracy, une employée IA qui aide un vendeur à gérer son catalogue "
    "et à créer sa boutique. "
    "Tu es un collègue de confiance, factuel et proactif — pas un chatbot.\n\n"
    "VOCABULAIRE INTERDIT :\n"
    "- « En tant que IA… », « Je suis un modèle de langage… »\n"
    "- « Comment puis-je vous aider aujourd'hui ? »\n"
    "- Listes à puces dans tes réponses conversationnelles\n"
    "- « Bien sûr ! » en début de phrase\n\n"
    "RÈGLES :\n"
    "- Présente un nombre limité de produits pertinents, jamais une liste exhaustive.\n"
    "- Alerte proactivement sur les ruptures de stock.\n"
    "- Pour toute action destructive (suppression), demande confirmation explicite.\n"
    "- Reste factuel sur les chiffres (prix, stock, ventes).\n"
    "- Après chaque action, résume clairement ce que tu as fait.\n"
    "- N'invente jamais une information.\n"
    "- Réponds en français, de façon concise et naturelle (max 3-4 phrases).\n\n"
    "CRÉATION DE BOUTIQUE :\n"
    "- Demande TOUJOURS si la boutique est physique ou en ligne.\n"
    "- Si PHYSIQUE : la localisation GPS (auto) et une photo de la devanture sont OBLIGATOIRES.\n"
    "- Si EN LIGNE : pas besoin de GPS ni de photo de devanture.\n"
    "- Collecte le nom, la catégorie, puis les infos conditionnelles avant de finaliser.\n"
    "- Tracy connaît la localisation GPS de chaque boutique physique pour orienter les clients.\n\n"
    "CONFIGURATION DES RÈGLES COMMERCIALES :\n"
    "- Après la création de boutique OU quand le vendeur dit 'configurer', 'réglages', 'négociation'.\n"
    "- Pose UNE question à la fois, dans l'ordre :\n"
    "  1. 'En dessous de quel pourcentage de marge tu ne veux pas vendre ?' (marge min, défaut 10%)\n"
    "  2. 'Tu veux offrir une réduction aux nouveaux clients ? Si oui, combien ?' (défaut 0%)\n"
    "  3. 'Quelle est la réduction maximum que je peux accorder ?' (défaut 15%)\n"
    "  4. 'À partir de quel montant la livraison est gratuite ?' (optionnel)\n"
    "  5. 'En dessous de quel % je peux accepter directement sans te demander ?' (défaut 5%)\n"
    "  6. 'Tu as des règles spéciales ? (ex: pas de réduction sur les Nike)' (optionnel)\n"
    "- Après chaque réponse, confirme et passe à la suivante.\n"
    "- À la fin, récapitule toutes les règles et dis au vendeur qu'il peut les modifier ici ou dans Paramètres > Boutique.\n"
    "- Si le vendeur dit un pourcentage ou un montant seul, interprète selon la question posée."
)


class CatalogAgent(BaseAgent):
    """Gestionnaire du catalogue produit."""

    @property
    def name(self) -> str:
        return "CatalogAgent"

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

        message_lower = input_data.message.lower()

        # ── Onboarding vendeur : « je veux vendre sur Mantota » ──
        if re.search(
            r"vendre.*sur.*mantota|devenir.*vendeu|commencer.*[àa].*vendre|"
            r"je.*veux.*vendre|comment.*vendre|inscri.*vendeur",
            message_lower,
        ):
            reply = await self._call_ai([
                ChatMessage(role="system", content=self.system_prompt),
                ChatMessage(
                    role="user",
                    content=(
                        f"Message : {input_data.message}\n\n"
                        "La personne veut devenir vendeur sur Mantota. Explique-lui simplement :\n"
                        "1. C'est gratuit pour commencer.\n"
                        "2. Elle télécharge l'app Mantota, crée son compte et sa boutique.\n"
                        "3. Toi (Tracy) tu l'aides ensuite à vendre : tu réponds aux clients, "
                        "tu négocies selon ses règles et tu prends les commandes 24h/24.\n"
                        "Propose-lui de créer sa boutique maintenant si elle veut. "
                        "Reste chaleureuse et concise (2-3 phrases max)."
                    ),
                ),
            ])
            return AgentOutput(reply=reply, handled=True, tools_used=[])

        # ── Stats vendeur : pas de tool stats en V1 → réponse honnête ──
        if re.search(
            r"combien.*(?:j'ai|jai).*vendu|combien.*de.*commandes|"
            r"mes.*statistiques|statistiques.*de.*vente|mes.*ventes|"
            r"chiffre.*d.affaires|mes.*performances|rapport.*de.*vente",
            message_lower,
        ):
            reply = await self._call_ai([
                ChatMessage(role="system", content=self.system_prompt),
                ChatMessage(
                    role="user",
                    content=(
                        f"Message du vendeur : {input_data.message}\n\n"
                        "Le vendeur demande ses statistiques de vente. "
                        "Tu n'as pas accès aux statistiques en temps réel dans cette conversation. "
                        "N'invente AUCUN chiffre. Dis-lui que ses stats complètes "
                        "(ventes, commandes, chiffre d'affaires) sont dans son tableau de bord "
                        "sur l'app Mantota, section Boutique. Reste concise (1-2 phrases)."
                    ),
                ),
            ])
            return AgentOutput(reply=reply, handled=True, tools_used=[])


        # Handler public : pas de gestion catalogue sur le site public
        if input_data.store_id == "public":
            # Création de boutique → autorisée même sur public
            if any(word in message_lower for word in (
                "créer", "creer", "ouvrir", "nouvelle boutique",
                "lancer", "monter", "installer", "boutique physique", "boutique en ligne",
            )):
                reply = await self._call_ai([
                    ChatMessage(role="system", content=self.system_prompt),
                    ChatMessage(
                        role="user",
                        content=(
                            f"Message du vendeur : {input_data.message}\n\n"
                            "Le vendeur souhaite créer une boutique. Tu dois lui poser les "
                            "questions suivantes dans l'ordre :\n"
                            "1. La boutique est physique ou en ligne ?\n"
                            "2. Quel est le nom de la boutique ?\n"
                            "3. Quelle catégorie ? (Mode, Électronique, Alimentaire, etc.)\n"
                            "4. Si PHYSIQUE : demande la localisation GPS (bouton 'Envoyer ma position') "
                            "ET une photo de la devanture. Ces deux éléments sont OBLIGATOIRES.\n"
                            "5. Si EN LIGNE : pas besoin de localisation ni de photo.\n\n"
                            "Ne crée pas la boutique tant que tu n'as pas toutes les infos requises."
                        ),
                    ),
                ])
                return AgentOutput(reply=reply, handled=True, tools_used=[])

            # Configuration des règles → possible sur public
            if any(word in message_lower for word in (
                "configurer", "réglages", "reglages", "règles", "regles",
                "négociation", "negociation", "négocie", "negocie",
                "marge", "réduction", "reduction", "remise",
                "livraison gratuite", "auto-accept",
                "paramètres boutique", "parametres boutique",
            )):
                reply = await self._call_ai([
                    ChatMessage(role="system", content=self.system_prompt),
                    ChatMessage(
                        role="user",
                        content=(
                            f"Message du vendeur : {input_data.message}\n\n"
                            "Le vendeur veut configurer ses règles commerciales mais n'a pas "
                            "encore de boutique active. Dis-lui qu'il doit d'abord créer sa "
                            "boutique sur l'app Mantota, puis il pourra configurer ses règles "
                            "ici. Reste concise (1-2 phrases)."
                        ),
                    ),
                ])
                return AgentOutput(reply=reply, handled=True, tools_used=[])

            # Tout le reste (catalogue, prix, stock) → redirige vers l'app
            reply = await self._call_ai([
                ChatMessage(role="system", content=self.system_prompt),
                ChatMessage(
                    role="user",
                    content=(
                        f"Message du vendeur : {input_data.message}\n\n"
                        "Le vendeur est sur le site public et demande une action sur son catalogue "
                        "ou ses produits. Dis-lui que la gestion du catalogue se fait sur l'app Mantota. "
                        "S'il n'a pas encore de boutique, propose-lui de la créer ici. "
                        "Reste concise (1-2 phrases)."
                    ),
                ),
            ])
            return AgentOutput(reply=reply, handled=True, tools_used=[])

        # ── Configuration des règles commerciales ─────────────────
        if any(word in message_lower for word in (
            "configurer", "réglages", "reglages", "règles", "regles",
            "négociation", "negociation", "négocie", "negocie",
            "marge", "réduction", "reduction", "remise",
            "livraison gratuite", "auto-accept",
            "paramètres boutique", "parametres boutique",
        )):
            return await self._handle_shop_config(input_data, ctx)

        # ── Création de boutique ──────────────────────────────────
        if any(word in message_lower for word in (
            "créer", "creer", "ouvrir", "nouvelle boutique",
            "lancer", "monter", "installer", "boutique physique", "boutique en ligne",
        )):
            reply = await self._call_ai([
                ChatMessage(role="system", content=self.system_prompt),
                ChatMessage(
                    role="user",
                    content=(
                        f"Message du vendeur : {input_data.message}\n\n"
                        "Le vendeur souhaite créer une boutique. Tu dois lui poser les "
                        "questions suivantes dans l'ordre :\n"
                        "1. La boutique est physique ou en ligne ?\n"
                        "2. Quel est le nom de la boutique ?\n"
                        "3. Quelle catégorie ? (Mode, Électronique, Alimentaire, etc.)\n"
                        "4. Si PHYSIQUE : demande la localisation GPS (bouton 'Envoyer ma position') "
                        "ET une photo de la devanture. Ces deux éléments sont OBLIGATOIRES.\n"
                        "5. Si EN LIGNE : pas besoin de localisation ni de photo.\n\n"
                        "Ne crée pas la boutique tant que tu n'as pas toutes les infos requises."
                    ),
                ),
            ])
            return AgentOutput(reply=reply, handled=True, tools_used=[])

        # ── Gestion du catalogue existant ─────────────────────────
        # Étape 1 : rechercher dans le catalogue
        catalog_result = await self._tool_registry.execute(
            "search_catalog",
            ctx,
            store_id=input_data.store_id,
        )

        tools_used = ["search_catalog"]

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
                        f"Message du vendeur : {input_data.message}\n\n"
                        "Le catalogue n'est pas accessible pour le moment. "
                        "Informe le vendeur du problème technique."
                    ),
                ),
            ])
            return AgentOutput(reply=reply, handled=True, tools_used=tools_used)

        catalog = catalog_result.data  # type: ignore[union-attr]
        products_summary = "\n".join(
            f"- {p.nom} : {p.prix:.0f} FCFA (stock: {p.stock})"
            for p in catalog.products[:10]
        )
        categories_summary = ", ".join(c.nom for c in catalog.categories) or "Aucune catégorie"

        # Étape 2 : génération de la réponse via l'AI Gateway
        reply = await self._call_ai([
            ChatMessage(role="system", content=self.system_prompt),
            ChatMessage(
                role="user",
                content=(
                    f"Message du vendeur : {input_data.message}\n\n"
                    f"Catégories : {categories_summary}\n"
                    f"Produits :\n{products_summary}"
                ),
            ),
        ])

        logger.info(
            "agent_reply_generated",
            agent=self.name,
            correlation_id=input_data.correlation_id,
        )

        return AgentOutput(reply=reply, handled=True, tools_used=tools_used)

    # ── Configuration des règles commerciales ──────────────────────

    async def _handle_shop_config(
        self, input_data: AgentInput, ctx: ToolContext
    ) -> AgentOutput:
        """Gère l'intent shop_config : extraction LLM → validation → persistance.

        1. Récupère la config actuelle (lecture).
        2. Demande au LLM d'extraire les paramètres structurés du message vendeur.
        3. Si des paramètres clairs sont extraits :
           a. Valide la cohérence (marge positive, etc.).
           b. Si incohérent → avertit le vendeur, demande correction.
           c. Si cohérent → appelle update_shop_config.
           d. Confirme uniquement après succès réel.
        4. Si incomplet/ambigu → continue le flow conversationnel de clarification.
        """
        # 1. Récupérer la config actuelle pour contexte
        config_result = await self._tool_registry.execute(
            "get_shop_config",
            ctx,
            store_id=input_data.store_id,
        )
        config_context = ""
        current_config = None
        if config_result.success and config_result.data:
            cfg = config_result.data
            current_config = cfg
            config_context = (
                f"\n\nConfig actuelle :\n"
                f"- Marge min : {cfg.min_margin_percent}%\n"
                f"- Réduction premier achat : {cfg.first_order_discount_percent}%\n"
                f"- Réduction max : {cfg.max_discount_percent}%\n"
                f"- Livraison gratuite dès : {cfg.free_shipping_threshold or 'non défini'}\n"
                f"- Auto-acceptation jusqu'à : {cfg.auto_accept_below}%\n"
                f"- Règles custom : {cfg.custom_rules or 'aucune'}\n"
                f"- Devise : {cfg.currency}\n"
            )

        # 2. Extraction structurée via LLM
        extracted = await self._extract_config_params(
            input_data.message, config_context, input_data.conversation_history
        )

        # 3. Si aucun paramètre clair extrait → flow conversationnel
        if extracted is None:
            reply = await self._call_ai([
                ChatMessage(role="system", content=self.system_prompt),
                ChatMessage(
                    role="user",
                    content=(
                        f"Message du vendeur : {input_data.message}\n\n"
                        "Le vendeur veut configurer ou modifier ses règles commerciales. "
                        "Guide-le question par question selon les instructions de "
                        "CONFIGURATION DES RÈGLES COMMERCIALES."
                        f"{config_context}"
                    ),
                ),
            ])
            return AgentOutput(reply=reply, handled=True, tools_used=["get_shop_config"])

        # 4. Validation de cohérence
        coherence = self._validate_config_coherence(extracted, current_config)
        if not coherence["ok"]:
            reply = await self._call_ai([
                ChatMessage(role="system", content=self.system_prompt),
                ChatMessage(
                    role="user",
                    content=(
                        f"Message du vendeur : {input_data.message}\n\n"
                        f"Le vendeur a donné des valeurs qui semblent incohérentes :\n"
                        f"{coherence['reason']}\n\n"
                        f"Valeurs extraites : {json.dumps(extracted, ensure_ascii=False)}\n"
                        f"{config_context}\n"
                        "Explique au vendeur l'incohérence détectée de façon claire et simple, "
                        "puis demande-lui de corriger ou de confirmer. "
                        "Ne confirme AUCUN enregistrement — rien n'a été sauvegardé."
                    ),
                ),
            ])
            return AgentOutput(reply=reply, handled=True, tools_used=["get_shop_config"])

        # 5. Persistance via update_shop_config
        tools_used = ["get_shop_config"]
        persist_result = await self._persist_config(
            input_data.store_id, extracted, ctx
        )
        tools_used.append("update_shop_config")

        if persist_result["success"]:
            reply = await self._call_ai([
                ChatMessage(role="system", content=self.system_prompt),
                ChatMessage(
                    role="user",
                    content=(
                        f"Message du vendeur : {input_data.message}\n\n"
                        f"Les règles suivantes ont été ENREGISTRÉES avec succès :\n"
                        f"{json.dumps(extracted, ensure_ascii=False, indent=2)}\n"
                        f"{config_context}\n"
                        "Confirme au vendeur que c'est enregistré. Récapitule les règles "
                        "modifiées de façon claire et concise (max 3 phrases). "
                        "Précise qu'il peut modifier ses règles ici ou dans Paramètres > Boutique."
                    ),
                ),
            ])
        else:
            error_msg = persist_result.get("error_message", "une erreur est survenue")
            reply = await self._call_ai([
                ChatMessage(role="system", content=self.system_prompt),
                ChatMessage(
                    role="user",
                    content=(
                        f"Message du vendeur : {input_data.message}\n\n"
                        f"J'ai essayé d'enregistrer les règles mais ça a échoué : {error_msg}.\n"
                        "Dis clairement au vendeur que l'enregistrement n'a pas fonctionné, "
                        "et propose-lui de réessayer. Ne confirme JAMAIS un succès qui n'a pas eu lieu. "
                        "Reste concise (1-2 phrases)."
                    ),
                ),
            ])

        return AgentOutput(reply=reply, handled=True, tools_used=tools_used)

    async def _extract_config_params(
        self,
        vendor_message: str,
        config_context: str,
        conversation_history: list[str],
    ) -> dict | None:
        """Demande au LLM d'extraire les paramètres structurés du message vendeur.

        Retourne un dict avec les paramètres extraits, ou None si le message
        est ambigu/incomplet (le LLM ne peut pas extraire de valeurs claires).

        Le LLM extrait des paramètres, il ne décide pas de la règle métier.
        """
        extraction_prompt = (
            "Tu es un extracteur de paramètres de configuration commerciale. "
            "Analyse le message du vendeur et extrais les paramètres suivants "
            "si et seulement si ils sont clairs, complets et non ambigus.\n\n"
            "Paramètres possibles :\n"
            '- min_margin_percent (float, 0-100) : marge minimale en %\n'
            '- max_discount_percent (float, 0-100) : réduction maximum en %\n'
            '- first_order_discount_percent (float, 0-100) : réduction premier achat en %\n'
            '- auto_accept_below (float, 0-100) : auto-acceptation jusqu\'à ce %\n'
            '- free_shipping_threshold (float, >0) : montant de livraison gratuite\n'
            '- custom_rules (string) : règles personnalisées en texte libre\n'
            '- currency (string, 3 lettres) : code devise (XOF, XAF, etc.)\n\n'
            "RÈGLES D'EXTRACTION :\n"
            "- N'extrait QUE les paramètres explicitement donnés par le vendeur.\n"
            "- Si le vendeur dit 'ne négocie jamais plus de 5%', extrais max_discount_percent=5.0.\n"
            "- Si le vendeur dit 'marge minimum 10%', extrais min_margin_percent=10.0.\n"
            "- Si le vendeur dit 'livraison gratuite au-dessus de 20000', extrais free_shipping_threshold=20000.0.\n"
            "- Si le vendeur donne plusieurs règles dans un message, extrais-les toutes.\n"
            "- Si le vendeur dit juste 'fais une remise' sans préciser combien, NE RIEN extraire.\n"
            "- Si le vendeur dit juste 'configure' sans valeur, NE RIEN extraire.\n"
            "- Si l'information est incomplète ou ambiguë, NE RIEN extraire.\n\n"
            "Réponds UNIQUEMENT avec un JSON valide :\n"
            '- Si tu peux extraire au moins un paramètre : {"param1": valeur1, "param2": valeur2, ...}\n'
            '- Si rien n\'est extractible : {"extracted": false}\n'
        )

        history_context = ""
        if conversation_history:
            history_context = (
                "\n\nHistorique récent de la conversation :\n"
                + "\n".join(f"- {msg}" for msg in conversation_history[-5:])
            )

        raw_response = await self._call_ai([
            ChatMessage(role="system", content=extraction_prompt),
            ChatMessage(
                role="user",
                content=(
                    f"Message du vendeur : {vendor_message}\n"
                    f"{config_context}{history_context}\n\n"
                    "Extrais les paramètres. Réponds en JSON uniquement."
                ),
            ),
        ], max_tokens=300)

        return self._parse_extraction_response(raw_response)

    @staticmethod
    def _parse_extraction_response(raw: str) -> dict | None:
        """Parse la réponse JSON du LLM. Retourne un dict de params ou None."""
        # Tente d'extraire le JSON de la réponse (le LLM peut ajouter du texte)
        match = re.search(r'\{[^{}]*\}', raw, re.DOTALL)
        if not match:
            return None

        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None

        if data.get("extracted") is False:
            return None

        # Filtre les clés valides et supprime les valeurs None
        valid_keys = {
            "min_margin_percent", "max_discount_percent",
            "first_order_discount_percent", "auto_accept_below",
            "free_shipping_threshold", "custom_rules", "currency",
        }
        result = {
            k: v for k, v in data.items()
            if k in valid_keys and v is not None
        }

        if not result:
            return None

        return result

    @staticmethod
    def _validate_config_coherence(
        extracted: dict,
        current_config: object | None = None,
    ) -> dict:
        """Valide la cohérence des paramètres extraits.

        Vérifie :
        - min_margin_percent + max_discount_percent ≤ 100 (sinon marge négative)
        - auto_accept_below ≤ max_discount_percent (sinon auto-accept au-dessus du max)
        - free_shipping_threshold > 0 si présent
        """
        reasons = []

        min_margin = extracted.get("min_margin_percent")
        max_discount = extracted.get("max_discount_percent")
        auto_accept = extracted.get("auto_accept_below")
        free_shipping = extracted.get("free_shipping_threshold")

        # Si on a seulement un des deux (min_margin ou max_discount),
        # on utilise la config actuelle pour l'autre
        if current_config is not None:
            if min_margin is None and max_discount is not None:
                min_margin = current_config.min_margin_percent
            if max_discount is None and min_margin is not None:
                max_discount = current_config.max_discount_percent
            if auto_accept is not None and max_discount is None:
                max_discount = current_config.max_discount_percent

        # min_margin + max_discount ≤ 100
        if min_margin is not None and max_discount is not None:
            if min_margin + max_discount > 100:
                reasons.append(
                    f"La marge minimale ({min_margin}%) + la réduction maximum "
                    f"({max_discount}%) dépassent 100%. Cela signifie que tu vendrais "
                    f"à perte sur certaines ventes. "
                    f"Réduis la marge min ou la réduction max."
                )

        # auto_accept_below ≤ max_discount_percent
        if auto_accept is not None and max_discount is not None:
            if auto_accept > max_discount:
                reasons.append(
                    f"L'auto-acceptation est fixée à {auto_accept}% mais la réduction "
                    f"maximum est {max_discount}%. Je ne peux pas auto-accepter une "
                    f"réduction supérieure au maximum que tu autorises. "
                    f"Réduis le seuil d'auto-acceptation ou augmente la réduction max."
                )

        # free_shipping_threshold > 0
        if free_shipping is not None and free_shipping <= 0:
            reasons.append(
                "Le seuil de livraison gratuite doit être un montant positif."
            )

        if reasons:
            return {"ok": False, "reason": " ".join(reasons)}

        return {"ok": True, "reason": ""}

    async def _persist_config(
        self, store_id: str, params: dict, ctx: ToolContext
    ) -> dict:
        """Appelle update_shop_config avec les paramètres extraits.

        Retourne {"success": bool, "error_message": str?}.
        """
        try:
            result = await self._tool_registry.execute(
                "update_shop_config",
                ctx,
                store_id=store_id,
                **params,
            )
        except Exception as exc:
            logger.error(
                "shop_config_persist_error",
                agent=self.name,
                store_id=store_id,
                error=str(exc),
            )
            return {"success": False, "error_message": str(exc)}

        if not result.success:
            error_msg = (
                result.error.message if result.error else "erreur inconnue"
            )
            logger.warning(
                "shop_config_persist_failed",
                agent=self.name,
                store_id=store_id,
                error_code=result.error.code if result.error else None,
            )
            return {"success": False, "error_message": error_msg}

        return {"success": True}
