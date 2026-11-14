"""VendorCopilot — assistant du vendeur (mode vendeur uniquement).

Rôle : donner au vendeur des FAITS fiables sur sa boutique :
- ventes du mois et revenus (route /bot/vendors/{id}/stats),
- alertes de stock (ruptures et stock faible, via le catalogue),
- comptes-rendus des discussions de Tracy avec ses clients (négociations,
  accords de prix, demandes de contact).

Outils autorisés : get_vendor_stats, get_vendor_reports, search_catalog.

Limites : lecture seule ; n'invente jamais un chiffre ; refuse hors mode vendeur.
Autonomie V1 : conversation_only.
"""

from __future__ import annotations

import json
import re

from app.agents.base import AgentAutonomy, AgentInput, AgentOutput, BaseAgent
from app.ai_gateway.base import ChatMessage
from app.logging_config import bind_context, get_logger
from app.tools.base import ToolContext

logger = get_logger(__name__)

LOW_STOCK_THRESHOLD = 3

_STATS_RE = re.compile(
    r"vendu|commandes?|statistiques?|ventes?|chiffre|performance|revenus?|gagn[ée]|rapport",
    re.IGNORECASE,
)
_STOCK_RE = re.compile(r"stock|rupture|[ée]puis|r[ée]approvision|plus\s+de\s+\w+\s+en", re.IGNORECASE)
_REPORTS_RE = re.compile(
    r"r[ée]sum[ée]|compte.?rendu|discussion|conversation|clients?\s+(?:disent|ont|veulent|demandent)|"
    r"que\s+disent|n[ée]goci|messages?\s+des\s+clients|demandes?\s+de\s+contact|veulent\s+me\s+parler",
    re.IGNORECASE,
)
_BRIEFING_RE = re.compile(r"point\s+du\s+jour|briefing|quoi\s+de\s+neuf|r[ée]sum[ée]\s+du\s+jour|bilan", re.IGNORECASE)

SYSTEM_PROMPT = (
    "Tu es Tracy, la collaboratrice du vendeur : factuelle, proactive, claire. "
    "Tu lui fais le point à partir des FAITS fournis uniquement.\n\n"
    "RÈGLES :\n"
    "- N'invente JAMAIS un chiffre, un client ou une discussion. Si une donnée manque, dis-le.\n"
    "- Va à l'essentiel : chiffres clés d'abord, puis ce qui demande son attention "
    "(ruptures, clients qui veulent lui parler, négociations en attente).\n"
    "- Propose une action concrète quand c'est utile (réapprovisionner, rappeler un client).\n"
    "- Pas de « En tant que IA ». Réponse courte (max 6 phrases), listes courtes autorisées."
)


class VendorCopilot(BaseAgent):
    """Point de situation et alertes pour le vendeur."""

    @property
    def name(self) -> str:
        return "VendorCopilot"

    @property
    def autonomy(self) -> AgentAutonomy:
        return "conversation_only"

    @property
    def _raw_system_prompt(self) -> str:
        return SYSTEM_PROMPT

    async def handle(self, input_data: AgentInput) -> AgentOutput:
        bind_context(agent=self.name)
        if not input_data.store_id or input_data.store_id == "public" or not input_data.store_id.isdigit():
            return AgentOutput(
                reply=(
                    "Ces informations sont réservées aux vendeurs connectés à leur boutique. "
                    "Connecte-toi à ton espace vendeur et je te fais le point."
                ),
                handled=True,
                tools_used=[],
            )

        text = input_data.message
        briefing = bool(_BRIEFING_RE.search(text))
        want_stats = briefing or bool(_STATS_RE.search(text))
        want_stock = briefing or bool(_STOCK_RE.search(text))
        want_reports = briefing or bool(_REPORTS_RE.search(text))
        if not (want_stats or want_stock or want_reports):
            want_stats = want_stock = want_reports = True

        ctx = ToolContext(
            agent_name=self.name,
            correlation_id=input_data.correlation_id,
            store_id=input_data.store_id,
        )
        tools_used: list[str] = []
        facts: list[str] = []

        if want_stats:
            res = await self._tool_registry.execute("get_vendor_stats", ctx, vendor_id=input_data.store_id)
            tools_used.append("get_vendor_stats")
            if res.success and res.data:
                facts.append("VENTES DU MOIS (source Mantota) :\n" + json.dumps(res.data, ensure_ascii=False)[:1500])
            else:
                facts.append("VENTES DU MOIS : indisponibles pour le moment.")

        if want_stock:
            res = await self._tool_registry.execute("search_catalog", ctx, store_id=input_data.store_id)
            tools_used.append("search_catalog")
            if res.success and res.data:
                out = [p for p in res.data.products if p.stock <= 0]
                low = [p for p in res.data.products if 0 < p.stock <= LOW_STOCK_THRESHOLD]
                if not out and not low:
                    facts.append("STOCK : aucun produit en rupture ni en stock faible.")
                else:
                    lines = [f"- RUPTURE : {p.nom}" for p in out[:10]]
                    lines += [f"- Stock faible : {p.nom} ({p.stock} restant)" for p in low[:10]]
                    facts.append("STOCK :\n" + "\n".join(lines))
            else:
                facts.append("STOCK : catalogue indisponible pour le moment.")

        if want_reports:
            res = await self._tool_registry.execute("get_vendor_reports", ctx, vendor_id=input_data.store_id, limit=8)
            tools_used.append("get_vendor_reports")
            reports = (res.data or {}).get("reports", []) if res.success else None
            if reports is None:
                facts.append("COMPTES-RENDUS CLIENTS : indisponibles pour le moment.")
            elif not reports:
                facts.append("COMPTES-RENDUS CLIENTS : aucune discussion à signaler.")
            else:
                lines = [
                    f"- [{r.get('kind')}] {r.get('summary')}"
                    + (f" (tél. {r['customer_phone']})" if r.get("customer_phone") else "")
                    for r in reports
                ]
                facts.append("COMPTES-RENDUS CLIENTS (du plus récent au plus ancien) :\n" + "\n".join(lines))

        history = ""
        if input_data.conversation_history:
            history = "\n\nHistorique récent :\n" + "\n".join(f"  - {m}" for m in input_data.conversation_history[-4:])

        reply = await self._call_ai([
            ChatMessage(role="system", content=self.system_prompt),
            ChatMessage(
                role="user",
                content=f"Message du vendeur : {text}\n\nFAITS :\n" + "\n\n".join(facts) + history,
            ),
        ])
        return AgentOutput(reply=reply, handled=True, tools_used=tools_used)
