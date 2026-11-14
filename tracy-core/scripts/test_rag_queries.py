#!/usr/bin/env python3
"""Script de test manuel du RAG — envoie 15 questions test au tool search_knowledge.

Affiche pour chaque question :
  - la question
  - les chunks retournés (title, score, extrait du contenu)
  - la classification de pertinence (correct / ambiguous / incorrect)

Usage :
    .venv/bin/python scripts/test_rag_queries.py
    .venv/bin/python scripts/test_rag_queries.py --country-id 1
    .venv/bin/python scripts/test_rag_queries.py --top-k 3

Ne modifie rien en base — lecture seule.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from typing import Any

# ── 15 questions test couvrant les 5 catégories du corpus Bénin ──

TEST_QUERIES: list[dict[str, Any]] = [
    # Quartiers / villes
    {"query": "Quels sont les principaux quartiers de Cotonou ?", "category": None},
    {"query": "C'est quoi Dantokpa ?", "category": None},
    {"query": "Tu livres à Ganvié ?", "category": None},
    # Marchés
    {"query": "Où se trouve le marché Ouando ?", "category": None},
    {"query": "Quels marchés il y a à Porto-Novo ?", "category": None},
    # Paiements
    {"query": "Je peux payer en MoMo ?", "category": None},
    {"query": "Comment on paye sur Mantota ?", "category": None},
    {"query": "Tu acceptes les cartes bancaires ?", "category": None},
    # Livraison
    {"query": "C'est quoi Zem ?", "category": None},
    {"query": "Tu livres où au Bénin ?", "category": None},
    {"query": "Combien de temps pour livrer à Parakou ?", "category": None},
    # Expressions
    {"query": "Comment on dit bienvenue en langue locale ?", "category": None},
    {"query": "Qu'est-ce qu'on dit pour négocier un prix ?", "category": None},
    # Hors corpus (devrait donner incorrect ou ambiguous)
    {"query": "Quelle est la recette du igname pilé ?", "category": None},
    {"query": "Comment créer un compte sur la plateforme ?", "category": None},
]


# ── Couleurs ANSI pour la console ──

class Color:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"


RELEVANCE_COLOR = {
    "correct": Color.GREEN,
    "ambiguous": Color.YELLOW,
    "incorrect": Color.RED,
}


def print_separator(char: str = "─", length: int = 80) -> None:
    print(char * length)


def print_table_header() -> None:
    print_separator("═")
    print(f"{'#':<3} {'Question':<45} {'Relevance':<12} {'Chunks':<7} {'Top score':<10}")
    print_separator("═")


def print_table_row(idx: int, query: str, relevance: str, chunk_count: int, top_score: float | None) -> None:
    color = RELEVANCE_COLOR.get(relevance, "")
    score_str = f"{top_score:.4f}" if top_score is not None else "—"
    # Truncate query for table
    q_short = query[:43] + ".." if len(query) > 45 else query
    print(f"{idx:<3} {q_short:<45} {color}{relevance:<12}{Color.RESET} {chunk_count:<7} {score_str:<10}")


async def run_tests(country_id: int | None, top_k: int) -> None:
    from app.config import get_settings
    from app.mantota_client.client import MantotaClient
    from app.rag.embeddings import EmbeddingService
    from app.rag.retriever import KnowledgeRetriever
    from app.tools.base import ToolContext
    from app.tools.search_knowledge import SearchKnowledgeTool

    settings = get_settings()

    if not settings.openai_api_key:
        print(f"{Color.RED}Erreur : OPENAI_API_KEY non configurée.{Color.RESET}")
        print("Définissez OPENAI_API_KEY dans le .env pour générer les embeddings des requêtes.")
        sys.exit(1)

    if not settings.mantota_api_key:
        print(f"{Color.RED}Erreur : MANTOTA_API_KEY non configurée.{Color.RESET}")
        print("Définissez MANTOTA_API_KEY dans le .env pour appeler l'API bot.")
        sys.exit(1)

    # Initialise les composants
    embedding_service = EmbeddingService(
        api_key=settings.openai_api_key,
        timeout=settings.ai_timeout,
        retry_max=settings.ai_retry_max,
    )
    mantota_client = MantotaClient(
        base_url=settings.mantota_api_url,
        api_key=settings.mantota_api_key,
        timeout=settings.mantota_timeout,
    )
    retriever = KnowledgeRetriever(embedding_service, mantota_client)
    tool = SearchKnowledgeTool(retriever)

    ctx = ToolContext(agent_name="CommercialAgent", correlation_id="rag-test-manual")

    print(f"\n{Color.BOLD}╔══════════════════════════════════════════════════════════════════════════╗{Color.RESET}")
    print(f"{Color.BOLD}║  Test RAG — 15 questions test sur le corpus Bénin                         ║{Color.RESET}")
    print(f"{Color.BOLD}╚══════════════════════════════════════════════════════════════════════════╝{Color.RESET}")
    print(f"  Mantota API : {settings.mantota_api_url}")
    print(f"  Country ID  : {country_id or 'global'}")
    print(f"  Top-K       : {top_k}")
    print()

    # Tableau récapitulatif
    print_table_header()

    results_detail: list[dict[str, Any]] = []

    for i, q in enumerate(TEST_QUERIES, 1):
        try:
            result = await tool.execute(
                ctx,
                query=q["query"],
                country_id=country_id,
                category=q.get("category"),
                top_k=top_k,
            )
        except Exception as e:
            print(f"{i:<3} {q['query'][:43]:<45} {Color.RED}ERREUR{'':<6}{Color.RESET} {str(e)[:30]}")
            results_detail.append({"query": q["query"], "error": str(e)})
            continue

        if not result.success:
            print(f"{i:<3} {q['query'][:43]:<45} {Color.RED}{result.error.code:<12}{Color.RESET} {'—':<7} {'—':<10}")
            results_detail.append({"query": q["query"], "error": result.error.code})
            continue

        data = result.data
        top_score = data.chunks[0]["score"] if data.chunks else None
        print_table_row(i, q["query"], data.relevance, len(data.chunks), top_score)

        results_detail.append({
            "query": q["query"],
            "relevance": data.relevance,
            "chunks": data.chunks,
            "formatted_context": data.formatted_context,
            "top_score": top_score,
        })

    print_separator("═")
    print()

    # Détail par question
    for i, r in enumerate(results_detail, 1):
        print_separator("─")
        print(f"{Color.BOLD}Question {i}/{len(results_detail)} : \"{r['query']}\"{Color.RESET}")

        if "error" in r:
            print(f"  {Color.RED}Erreur : {r['error']}{Color.RESET}")
            continue

        color = RELEVANCE_COLOR.get(r["relevance"], "")
        print(f"  Pertinence : {color}{Color.BOLD}{r['relevance']}{Color.RESET}")
        print(f"  Top score  : {r['top_score']:.4f}" if r["top_score"] else "  Top score  : —")
        print(f"  Chunks     : {len(r['chunks'])}")

        if r["chunks"]:
            print()
            for j, chunk in enumerate(r["chunks"], 1):
                score = chunk.get("score", 0)
                title = chunk.get("title", "—")
                content = chunk.get("content", "")
                category = chunk.get("category", "—")

                # Couleur du score selon le seuil
                if score >= 0.85:
                    score_color = Color.GREEN
                elif score >= 0.60:
                    score_color = Color.YELLOW
                else:
                    score_color = Color.RED

                print(f"  {Color.DIM}┌─ Chunk {j} ───────────────────────────────────────{Color.RESET}")
                print(f"  {Color.DIM}│{Color.RESET} Title   : {title}")
                print(f"  {Color.DIM}│{Color.RESET} Category: {category}")
                print(f"  {Color.DIM}│{Color.RESET} Score   : {score_color}{score:.4f}{Color.RESET}")
                print(f"  {Color.DIM}│{Color.RESET} Content : {content[:150]}{'...' if len(content) > 150 else ''}")
                print(f"  {Color.DIM}└───────────────────────────────────────────────────{Color.RESET}")
        else:
            print(f"\n  {Color.RED}Aucun chunk retourné.{Color.RESET}")

        # Affiche le contexte formaté (extrait)
        ctx_text = r.get("formatted_context", "")
        if ctx_text:
            print(f"\n  {Color.CYAN}Contexte formaté (extrait) :{Color.RESET}")
            for line in ctx_text[:300].split("\n"):
                print(f"  {Color.DIM}{line}{Color.RESET}")
            if len(ctx_text) > 300:
                print(f"  {Color.DIM}...{Color.RESET}")

        print()

    # Statistiques finales
    print_separator("═")
    print(f"{Color.BOLD}Statistiques finales{Color.RESET}")
    print_separator("─")

    relevance_counts = {"correct": 0, "ambiguous": 0, "incorrect": 0, "error": 0}
    for r in results_detail:
        if "error" in r:
            relevance_counts["error"] += 1
        else:
            relevance_counts[r["relevance"]] = relevance_counts.get(r["relevance"], 0) + 1

    total = len(results_detail)
    for level in ["correct", "ambiguous", "incorrect", "error"]:
        count = relevance_counts[level]
        if count > 0:
            color = RELEVANCE_COLOR.get(level, Color.RED)
            pct = (count / total) * 100
            print(f"  {color}{level:<12}{Color.RESET} : {count}/{total} ({pct:.0f}%)")

    print_separator("═")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Test RAG — 15 questions test sur le corpus Bénin")
    parser.add_argument("--country-id", type=int, default=None, help="ID du pays pour filtrer (ex: 1 pour le Bénin)")
    parser.add_argument("--top-k", type=int, default=5, help="Nombre de chunks à récupérer par question (défaut: 5)")
    args = parser.parse_args()

    asyncio.run(run_tests(country_id=args.country_id, top_k=args.top_k))


if __name__ == "__main__":
    main()
