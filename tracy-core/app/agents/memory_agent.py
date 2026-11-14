"""MemoryAgent (docs/tracy/03-AGENTS.md).

Rôle : Gardien de la mémoire de Tracy.
Responsabilité : Décider quelles informations méritent d'être mémorisées, les
organiser, et les restituer aux autres agents au bon moment (voir 06-MEMORY.md).

Outils autorisés : save_memory, search_memory, update_memory, delete_memory.

Limites : ne mémorise jamais d'information non confirmée ou sensible sans règle
explicite (voir confidentialité, 06-MEMORY.md).

Autonomie V1 : Autonome selon les règles strictes de 06-MEMORY.md.

Comportement IA (docs/tracy/05-AI_BEHAVIOR.md) :
- Discrète, factuelle, respecte la confidentialité.
- Vérifie les critères : utile, durable, fiable, confirmée.
- Droit à l'oubli : exécute sans condition ni justification.
"""

from __future__ import annotations

from app.agents.base import AgentAutonomy, AgentInput, AgentOutput, BaseAgent
from app.ai_gateway.base import ChatMessage
from app.logging_config import bind_context, get_logger
from app.tools.base import ToolContext

logger = get_logger(__name__)

SYSTEM_PROMPT = (
    "Tu es Tracy, une employée IA chaleureuse et honnête. Tu gères la mémoire "
    "de Tracy : tu décides quelles informations méritent d'être mémorisées, les "
    "organises, et les restitues au bon moment. Tu es une commerciale expérimentée, "
    "pas un chatbot.\n\n"
    "VOCABULAIRE INTERDIT :\n"
    "- « En tant que IA… », « Je suis un modèle de langage… »\n"
    "- « Bien sûr ! » en début de phrase\n"
    "- Listes à puces dans tes réponses\n\n"
    "RÈGLES DE MÉMORISATION (06-MEMORY.md) :\n"
    "- Une information doit être utile, durable, fiable et confirmée avant d'être enregistrée.\n"
    "- Ne mémorise jamais de données bancaires, codes OTP, mots de passe.\n"
    "- Ne mémorise jamais d'informations personnelles non liées à l'activité commerciale.\n"
    "- Respecte le droit à l'oubli : supprime sans condition ni justification.\n"
    "- Chaque boutique a sa propre mémoire, totalement isolée des autres.\n"
    "- Ne révèle jamais les mémoires d'un autre client ou boutique.\n"
    "- N'invente jamais une information mémorisée.\n"
    "- Réponds en français, de façon concise et naturelle (max 3-4 phrases)."
)


class MemoryAgent(BaseAgent):
    """Gardien de la mémoire de Tracy."""

    @property
    def name(self) -> str:
        return "MemoryAgent"

    @property
    def autonomy(self) -> AgentAutonomy:
        return "full"

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

        # Détection : oubli / suppression
        if any(word in message_lower for word in ("oublie", "efface", "supprim", "effacer", "plus garder", "droit")):
            reply = await self._call_ai([
                ChatMessage(role="system", content=self.system_prompt),
                ChatMessage(
                    role="user",
                    content=(
                        f"Message du client/vendeur : {input_data.message}\n\n"
                        "L'utilisateur demande la suppression d'une information "
                        "mémorisée. Confirme sa demande et demande-lui quelles "
                        "informations il souhaite supprimer. Le droit à l'oubli "
                        "est absolu — aucune justification n'est requise."
                    ),
                ),
            ])
            return AgentOutput(reply=reply, handled=True, tools_used=tools_used)

        # Détection : auto-save quand l'utilisateur partage des infos personnelles
        # (nom, préférences, goûts) sans demander explicitement de mémoriser
        import re
        auto_save_patterns = [
            (r"je m'appelle (\w+)", "nom_client", "observed"),
            (r"mon nom est (\w+)", "nom_client", "observed"),
            (r"je m'appelle ([\w-]+)", "nom_client", "observed"),
            (r"j'aime (?:les |la |le )?(\w+)", "preference_client", "observed"),
            (r"je cherche (?:un |une |des )?(\w+)", "recherche_client", "observed"),
            (r"je veux (?:un |une |des )?(\w+)", "besoin_client", "observed"),
        ]
        auto_saved = False
        for pattern, key_prefix, source in auto_save_patterns:
            match = re.search(pattern, input_data.message, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                if len(value) >= 2:
                    try:
                        await self._tool_registry.execute(
                            "save_memory",
                            ctx,
                            scope="client",
                            entity_id=input_data.customer_id or input_data.store_id,
                            key=key_prefix,
                            value=value,
                            source=source,
                        )
                        tools_used.append("save_memory")
                        auto_saved = True
                    except Exception:
                        pass

        # Détection : recherche / consultation de mémoire
        if any(word in message_lower for word in ("souviens", "mémoire", "préférence", "rappelle", "tu te rappelles", "tu sais", "tu connais", "qu'est-ce que j'ai", "ce que j'ai dit")):
            # Extrait des mots-clés pertinents de la query pour la recherche
            search_query = input_data.message
            if "nom" in message_lower:
                search_query = "nom"
            elif any(w in message_lower for w in ("préférence", "j'aime", "aime", "goût")):
                search_query = "preference"
            elif any(w in message_lower for w in ("cherche", "veux", "besoin")):
                search_query = "recherche"
            # Si la query est longue (> 20 chars), utilise quand même la phrase complète
            # car Mantota fait un ILIKE sur key et value
            if len(search_query) > 30:
                # Raccourcit aux mots importants
                words = [w for w in search_query.split() if len(w) > 2 and w.lower() not in ("les", "des", "une", "que", "qui", "dans", "pour", "avec", "the")]
                search_query = " ".join(words[:3]) if words else search_query

            search_result = await self._tool_registry.execute(
                "search_memory",
                ctx,
                scope="client",
                entity_id=input_data.customer_id or input_data.store_id,
                query=search_query,
            )
            tools_used.append("search_memory")

            if search_result.success:
                entries = search_result.data  # type: ignore[union-attr]
                # Si 0 résultat avec query, refait sans query (récupère tout)
                if not entries.entries:
                    fallback_result = await self._tool_registry.execute(
                        "search_memory",
                        ctx,
                        scope="client",
                        entity_id=input_data.customer_id or input_data.store_id,
                    )
                    if fallback_result.success and fallback_result.data:
                        entries = fallback_result.data
                entries_summary = "\n".join(
                    f"  - {e.key} : {e.value} (source: {e.source})"
                    for e in entries.entries[:10]
                ) or "Aucune mémoire trouvée"

                reply = await self._call_ai([
                    ChatMessage(role="system", content=self.system_prompt),
                    ChatMessage(
                        role="user",
                        content=(
                            f"Message du client/vendeur : {input_data.message}\n\n"
                            f"Mémoires trouvées :\n{entries_summary}\n\n"
                            "Utilise ces informations pour personnaliser ta réponse. "
                            "Ne révèle jamais les mémoires d'un autre client ou boutique."
                        ),
                    ),
                ])
                return AgentOutput(reply=reply, handled=True, tools_used=tools_used)

        # Si auto-save a été fait, confirme et redirige
        if auto_saved:
            # Recherche aussi les mémoires existantes pour enrichir la réponse
            search_result = await self._tool_registry.execute(
                "search_memory",
                ctx,
                scope="client",
                entity_id=input_data.customer_id or input_data.store_id,
                query=input_data.message,
            )
            tools_used.append("search_memory")
            entries_summary = ""
            if search_result.success and search_result.data:
                entries_summary = "\n".join(
                    f"  - {e.key} : {e.value}" for e in search_result.data.entries[:5]
                )
            reply = await self._call_ai([
                ChatMessage(role="system", content=self.system_prompt),
                ChatMessage(
                    role="user",
                    content=(
                        f"Message du client/vendeur : {input_data.message}\n\n"
                        f"Informations enregistrées :\n{entries_summary or 'Nouvelle information sauvegardée'}\n\n"
                        "L'utilisateur a partagé des informations personnelles (nom, préférences, etc.). "
                        "Confirme que tu as bien noté l'info de façon naturelle et brève (1 phrase). "
                        "Ne dis pas 'j'ai mémorisé' — dis plutôt 'Enchanté Jean' ou 'Noté, tu aimes les téléphones Samsung'. "
                        "Puis demande ce qu'il cherche aujourd'hui."
                    ),
                ),
            ])
            return AgentOutput(reply=reply, handled=True, tools_used=tools_used)

        # Détection : mémorisation / enregistrement
        if any(word in message_lower for word in ("mémorise", "enregistre", "sauvegarde", "retiens", "note", "rappelle-toi")):
            reply = await self._call_ai([
                ChatMessage(role="system", content=self.system_prompt),
                ChatMessage(
                    role="user",
                    content=(
                        f"Message du client/vendeur : {input_data.message}\n\n"
                        "L'utilisateur souhaite que tu mémorises une information. "
                        "Vérifie les critères : utile, durable, fiable, confirmée. "
                        "Si l'information est confirmée par l'utilisateur, propose "
                        "de l'enregistrer. Si elle n'est pas confirmée, demande "
                        "validation explicite avant de mémoriser."
                    ),
                ),
            ])
            return AgentOutput(reply=reply, handled=True, tools_used=tools_used)

        # Fallback : recherche de contexte pertinent
        search_result = await self._tool_registry.execute(
            "search_memory",
            ctx,
            scope="store",
            entity_id=input_data.store_id,
            query=input_data.message,
        )
        tools_used.append("search_memory")

        context_info = ""
        if search_result.success:
            entries = search_result.data  # type: ignore[union-attr]
            if entries.entries:
                context_info = "\n\nContexte mémorisé pour cette boutique :\n" + "\n".join(
                    f"  - {e.key} : {e.value}" for e in entries.entries[:5]
                )

        reply = await self._call_ai([
            ChatMessage(role="system", content=self.system_prompt),
            ChatMessage(
                role="user",
                content=(
                    f"Message du client/vendeur : {input_data.message}\n\n"
                    "Demande liée à la mémoire. Identifie ce que l'utilisateur "
                    "souhaite (mémoriser, consulter, supprimer) et réponds "
                    f"de manière appropriée.{context_info}"
                ),
            ),
        ])

        logger.info(
            "agent_reply_generated",
            agent=self.name,
            correlation_id=input_data.correlation_id,
        )

        return AgentOutput(reply=reply, handled=True, tools_used=tools_used)
