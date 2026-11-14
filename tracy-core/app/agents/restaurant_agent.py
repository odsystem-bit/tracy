"""RestaurantAgent (docs/tracy/03-AGENTS.md).

Rôle : L'assistante restaurant. Gère les commandes de repas de bout en bout.
Responsabilité : Présenter les restaurants, afficher les menus, prendre les
commandes multi-plats, suivre les livraisons.

Outils autorisés : search_restaurants, get_restaurant_menu,
create_restaurant_order, track_restaurant_order.

Autonomie V1 : Autonome pour la conversation et la prise de commande restaurant.
"""

from __future__ import annotations

from app.agents.base import AgentAutonomy, AgentInput, AgentOutput, BaseAgent
from app.ai_gateway.base import ChatMessage
from app.logging_config import bind_context, get_logger
from app.tools.base import ToolContext

logger = get_logger(__name__)

SYSTEM_PROMPT = (
    "Tu es Tracy, une employée IA chaleureuse et experte en restauration. Tu aides "
    "les clients à commander des repas depuis les restaurants partenaires de MANTOTA.\n\n"
    "PERSONNALITÉ : chaleureuse, gourmande, efficace, honnête.\n\n"
    "VOCABULAIRE INTERDIT :\n"
    "- « En tant que IA… », « Je suis un modèle de langage… »\n"
    "- « Bien sûr ! » en début de phrase\n"
    "- Listes à puces dans tes réponses (tu parles, tu ne rédiges pas un document)\n"
    "- « Téléchargez l'app », « je ne suis pas disponible », « téléchargez Mantota »\n\n"
    "VOCABULAIRE PRIVILÉGIÉ :\n"
    "- Phrases courtes et appétissantes\n"
    "- Mentionne les plats de façon alléchante (« Le poulet braisé est croustillant, servi avec de l'attiéké »)\n\n"
    "LOGIQUE DE COMMANDE RESTAURANT :\n"
    "- Demande si le client veut livrer ou retirer sur place.\n"
    "- Présente les catégories du menu (entrées, plats, desserts, boissons).\n"
    "- Accepte plusieurs plats dans une seule commande (panier multi-plats).\n"
    "- Confirme le récapitulatif avant de passer la commande.\n"
    "- Informe sur le temps de préparation et la livraison estimée (30-60 min).\n"
    "- Si le restaurant est fermé, informe le client et propose les horaires.\n"
    "- N'invente jamais un plat qui n'est pas dans le menu fourni.\n"
    "- Réponds en français, de façon concise et naturelle (max 3-4 phrases)."
)


class RestaurantAgent(BaseAgent):
    """L'assistante restaurant — gère les commandes de repas."""

    @property
    def name(self) -> str:
        return "RestaurantAgent"

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

        message_lower = input_data.message.lower()
        tools_used: list[str] = []

        # Détection horaires / ouvert / fermé
        is_hours_request = any(w in message_lower for w in (
            "horaire", "ouvert", "fermé", "ferme", "heure.*ouverture",
            "quelle heure", "quand.*ouvert", "quand.*ferm",
        ))

        # Étape 1 : si le client mentionne un restaurant spécifique, afficher le menu
        # Sinon, rechercher les restaurants disponibles
        menu_result = None
        restaurants_result = None

        # Essayer d'abord de chercher un menu si on a un store_id qui ressemble à un restaurant
        if input_data.store_id and input_data.store_id != "0":
            menu_search = await self._tool_registry.execute(
                "get_restaurant_menu",
                ctx,
                restaurant_id=input_data.store_id,
            )
            tools_used.append("get_restaurant_menu")
            if menu_search.success:
                menu_result = menu_search.data

        # Si pas de menu trouvé, chercher la liste des restaurants
        if menu_result is None:
            rest_search = await self._tool_registry.execute(
                "search_restaurants",
                ctx,
            )
            tools_used.append("search_restaurants")
            if rest_search.success:
                restaurants_result = rest_search.data

        # Préparer le contexte pour l'AI
        if menu_result:
            # Construire le résumé du menu
            menu_text = self._format_menu(menu_result)
            is_open = menu_result.is_open_now
            hours_text = self._format_hours(menu_result) if is_hours_request else ""

            context_msg = (
                f"Message du client : {input_data.message}\n\n"
                f"Restaurant : {menu_result.shop_name}\n"
                f"Statut : {'Ouvert' if is_open else 'Fermé'}\n"
                f"Adresse : {menu_result.address or 'N/A'}\n"
            )
            if hours_text:
                context_msg += f"Horaires :\n{hours_text}\n"
            context_msg += f"\nMenu disponible :\n{menu_text}"

            if not is_open:
                context_msg += "\n\nAttention : le restaurant est actuellement fermé. Informe le client."
            if is_hours_request:
                context_msg += "\n\nLe client demande les horaires. Présente-les clairement."

        elif restaurants_result and restaurants_result.restaurants:
            rest_list = "\n".join(
                f"- {r.shop_name} ({'Ouvert' if r.is_open_now else 'Fermé'})"
                + (f" — {r.address}" if r.address else "")
                for r in restaurants_result.restaurants[:5]
            )
            context_msg = (
                f"Message du client : {input_data.message}\n\n"
                f"Restaurants disponibles :\n{rest_list}\n\n"
                "Demande au client quel restaurant l'intéresse, "
                "ou présente les options."
            )
            if is_hours_request:
                context_msg += "\n\nLe client demande les horaires. Demande-lui quel restaurant l'intéresse pour te donner les horaires exacts."
        else:
            context_msg = (
                f"Message du client : {input_data.message}\n\n"
                "Aucun restaurant n'est disponible pour le moment. "
                "Informe le client et propose de revenir plus tard."
            )

        # Historique
        history_context = ""
        if input_data.conversation_history:
            history_context = "\n\nHistorique récent :\n" + "\n".join(
                f"  - {msg}" for msg in input_data.conversation_history[-5:]
            )

        reply = await self._call_ai([
            ChatMessage(role="system", content=self.system_prompt),
            ChatMessage(role="user", content=context_msg + history_context),
        ])

        logger.info(
            "agent_reply_generated",
            agent=self.name,
            correlation_id=input_data.correlation_id,
            has_menu=menu_result is not None,
            has_restaurants=restaurants_result is not None,
        )

        return AgentOutput(reply=reply, handled=True, tools_used=tools_used)

    def _format_menu(self, menu) -> str:
        """Formate le menu en texte lisible pour l'AI."""
        lines = []
        for cat in menu.categories:
            lines.append(f"[{cat.name}]")
            for item in cat.items:
                desc = f" — {item.description}" if item.description else ""
                veg = " (végétarien)" if item.is_vegetarian else ""
                halal = " (halal)" if item.is_halal else ""
                lines.append(f"  {item.name} : {item.price:.0f} FCFA{desc}{veg}{halal}")
        return "\n".join(lines) if lines else "Menu vide"
