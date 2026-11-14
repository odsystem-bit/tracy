#!/usr/bin/env python3
"""Scan complet de maturité de Tracy — évalue la robustesse sur tous les axes."""

import asyncio
import httpx
import json
import time

TRACY_URL = "http://127.0.0.1:8001"
API_KEY = "tracy-dev-key-2026"

# ── Critères d'évaluation ──
# Chaque test a un poids et un score (0=fail, 0.5=partial, 1=pass)

RESULTS = []

async def send(client, text, conv_id, store_id="public"):
    try:
        resp = await client.post(
            f"{TRACY_URL}/chat",
            json={"store_id": store_id, "customer_id": "scan_user", "text": text, "conversation_id": conv_id},
            headers={"X-Api-Key": API_KEY},
            timeout=60,
        )
        if resp.status_code != 200:
            return {"text": f"HTTP {resp.status_code}", "agent": "ERROR", "tools_used": [], "cards": []}
        return resp.json()
    except Exception as e:
        return {"text": str(e), "agent": "ERROR", "tools_used": [], "cards": []}

def record(category, test_name, expected, actual, score, weight=1):
    RESULTS.append({
        "category": category,
        "test": test_name,
        "expected": expected,
        "actual": actual,
        "score": score,
        "weight": weight,
    })
    status = "✅" if score == 1 else "⚠️" if score > 0 else "❌"
    print(f"  {status} {test_name}: {actual} (score={score})")

async def main():
    async with httpx.AsyncClient() as client:
        print("=" * 70)
        print("SCAN COMPLET DE MATURITÉ DE TRACY")
        print("=" * 70)

        # ═══════════════════════════════════════════════════════════
        # 1. INTENT ROUTING (12 intents)
        # ═══════════════════════════════════════════════════════════
        print("\n📊 1. INTENT ROUTING")
        intent_tests = [
            ("salut comment ça va", "CommercialAgent", "salutation"),
            ("je cherche un telephone", "CommercialAgent", "recherche produit"),
            ("tu peux me faire un prix", "NegotiationAgent", "négociation"),
            ("je veux commander", "OrderAgent", "commande"),
            ("comment je paie", "PaymentAgent", "paiement"),
            ("mon colis n'est pas arrivé", "SupportAgent", "support"),
            ("tu me rappelles ce que j'ai dit", "MemoryAgent", "mémoire"),
            ("je veux manger", "RestaurantAgent", "restaurant"),
            ("lance une campagne de relance", "CampaignAgent", "campagne"),
            ("ajoute un produit dans mon catalogue", "CatalogAgent", "catalog"),
            ("je veux parler à un humain", "SupportAgent", "human escalation"),
            ("quelle monnaie tu accepte", "CommercialAgent", "devises"),
        ]
        for msg, expected_agent, label in intent_tests:
            r = await send(client, msg, f"scan_intent_{label}")
            score = 1 if r["agent"] == expected_agent else 0
            record("Intent Routing", label, expected_agent, r["agent"], score, weight=2)

        # ═══════════════════════════════════════════════════════════
        # 2. RECHERCHE PRODUIT (critères avancés)
        # ═══════════════════════════════════════════════════════════
        print("\n📊 2. RECHERCHE PRODUIT")
        search_tests = [
            ("telephone entre 5000 et 50000", "search_products", "gamme de prix"),
            ("ecouteur noir", "search_products", "couleur+produit"),
            ("le moins cher", "search_products", "tri ascendant"),
            ("tu as quoi en electronique", "search_products", "catégorie"),
            ("montre-moi un sac et un chargeur", "search_products", "multi-requête"),
        ]
        for msg, expected_tool, label in search_tests:
            r = await send(client, msg, f"scan_search_{label}")
            tools = r.get("tools_used", [])
            score = 1 if expected_tool in tools else 0
            record("Recherche Produit", label, expected_tool, str(tools), score, weight=2)

        # ═══════════════════════════════════════════════════════════
        # 3. NÉGOCIATION
        # ═══════════════════════════════════════════════════════════
        print("\n📊 3. NÉGOCIATION")
        neg_tests = [
            ("c'est trop cher", "NegotiationAgent", "trop cher"),
            ("moins cher", "NegotiationAgent", "moins cher"),
            ("tu peux baisser le prix", "NegotiationAgent", "baisse prix"),
        ]
        for msg, expected_agent, label in neg_tests:
            r = await send(client, msg, f"scan_neg_{label}", store_id="1")
            score = 1 if r["agent"] == expected_agent else 0
            record("Négociation", label, expected_agent, r["agent"], score, weight=2)

        # ═══════════════════════════════════════════════════════════
        # 4. SUPPORT APRÈS-VENTE
        # ═══════════════════════════════════════════════════════════
        print("\n📊 4. SUPPORT APRÈS-VENTE")
        support_tests = [
            ("mon colis n'est pas arrivé", "SupportAgent", "colis non livré"),
            ("le produit est défectueux", "SupportAgent", "produit défectueux"),
            ("je veux un remboursement", "SupportAgent", "remboursement"),
            ("parler à un humain", "SupportAgent", "human escalation"),
        ]
        for msg, expected_agent, label in support_tests:
            r = await send(client, msg, f"scan_support_{label}")
            score = 1 if r["agent"] == expected_agent else 0
            record("Support", label, expected_agent, r["agent"], score, weight=2)

        # ═══════════════════════════════════════════════════════════
        # 5. RESTAURANT
        # ═══════════════════════════════════════════════════════════
        print("\n📊 5. RESTAURANT")
        rest_tests = [
            ("je veux manger", "RestaurantAgent", "faim"),
            ("c'est quoi les horaires", "RestaurantAgent", "horaires"),
            ("tu as du poulet", "RestaurantAgent", "plat spécifique"),
            ("menu du restaurant", "RestaurantAgent", "menu"),
        ]
        for msg, expected_agent, label in rest_tests:
            r = await send(client, msg, f"scan_rest_{label}")
            score = 1 if r["agent"] == expected_agent else 0
            record("Restaurant", label, expected_agent, r["agent"], score, weight=1.5)

        # ═══════════════════════════════════════════════════════════
        # 6. CAMPAGNE & CATALOG
        # ═══════════════════════════════════════════════════════════
        print("\n📊 6. CAMPAGNE & CATALOG")
        camp_tests = [
            ("lance une campagne de relance", "CampaignAgent", "campagne"),
            ("statistiques de campagne", "CampaignAgent", "stats campagne"),
            ("ajoute un produit", "CatalogAgent", "ajout produit"),
            ("modifie le prix", "CatalogAgent", "modif prix"),
        ]
        for msg, expected_agent, label in camp_tests:
            r = await send(client, msg, f"scan_camp_{label}")
            score = 1 if r["agent"] == expected_agent else 0
            record("Campagne/Catalog", label, expected_agent, r["agent"], score, weight=1.5)

        # ═══════════════════════════════════════════════════════════
        # 7. MÉMOIRE
        # ═══════════════════════════════════════════════════════════
        print("\n📊 7. MÉMOIRE")
        conv_mem = "scan_memory"
        r1 = await send(client, "je m'appelle Jean et j'aime les telephones Samsung", conv_mem)
        r2 = await send(client, "tu te souviens de mon nom", conv_mem)
        score_mem = 1 if "Jean" in r2.get("text", "") or "jean" in r2.get("text", "").lower() else 0.5
        record("Mémoire", "rappel nom", "Jean", r2.get("text", "")[:80], score_mem, weight=1.5)

        r3 = await send(client, "tu me rappelles ce que j'aime", conv_mem)
        score_pref = 1 if "samsung" in r3.get("text", "").lower() or "telephone" in r3.get("text", "").lower() else 0.5
        record("Mémoire", "rappel préférence", "Samsung/téléphone", r3.get("text", "")[:80], score_pref, weight=1.5)

        # ═══════════════════════════════════════════════════════════
        # 8. CONVERSATION FLOW (greeting → search → negotiate → order)
        # ═══════════════════════════════════════════════════════════
        print("\n📊 8. CONVERSATION FLOW")
        conv_flow = "scan_flow"
        steps = [
            ("bonjour", "CommercialAgent", "salutation"),
            ("je cherche un ecouteur", "CommercialAgent", "recherche"),
            ("c'est trop cher", "NegotiationAgent", "négociation"),
            ("ok je le prends", "OrderAgent", "commande"),
        ]
        flow_scores = []
        for msg, expected_agent, label in steps:
            r = await send(client, msg, conv_flow, store_id="1")
            score = 1 if r["agent"] == expected_agent else 0.5
            flow_scores.append(score)
            record("Conversation Flow", label, expected_agent, r["agent"], score, weight=2)

        # ═══════════════════════════════════════════════════════════
        # 9. EDGE CASES (typos, slang, messages courts)
        # ═══════════════════════════════════════════════════════════
        print("\n📊 9. EDGE CASES")
        edge_tests = [
            ("bjr", None, "salutation courte"),
            ("ok", None, "message court"),
            ("merci", None, "remerciement"),
            ("telefon", "CommercialAgent", "typo téléphone"),
            ("c combien", "CommercialAgent", "argot prix"),
            ("nn je veux pas", None, "négation"),
        ]
        for msg, expected_agent, label in edge_tests:
            r = await send(client, msg, f"scan_edge_{label}")
            if expected_agent:
                score = 1 if r["agent"] == expected_agent else 0.5
            else:
                score = 1 if r["agent"] != "ERROR" else 0
            record("Edge Cases", label, str(expected_agent), r["agent"], score, weight=1)

        # ═══════════════════════════════════════════════════════════
        # 10. MULTI-PAYS / DEVISES
        # ═══════════════════════════════════════════════════════════
        print("\n📊 10. MULTI-PAYS / DEVISES")
        curr_tests = [
            ("quelle monnaie tu accepte", "get_currencies", "devises"),
            ("tu accepte le naira", "get_currencies", "naira"),
            ("tu livre dans quels pays", None, "pays livraison"),
        ]
        for msg, expected_tool, label in curr_tests:
            r = await send(client, msg, f"scan_curr_{label}")
            tools = r.get("tools_used", [])
            if expected_tool:
                score = 1 if expected_tool in tools else 0
            else:
                score = 1 if r["agent"] != "ERROR" else 0
            record("Multi-pays", label, str(expected_tool), str(tools), score, weight=1.5)

        # ═══════════════════════════════════════════════════════════
        # 11. BOUTIQUES RÉELLES
        # ═══════════════════════════════════════════════════════════
        print("\n📊 11. BOUTIQUES RÉELLES")
        real_tests = [
            ("1", "je cherche un chargeur", "CommercialAgent", "recherche store 1"),
            ("1", "quelle monnaie tu accepte", "CommercialAgent", "devises store 1"),
            ("2", "montre-moi ton catalogue", "CatalogAgent", "catalog store 2"),
            ("2", "tu as des promotions", "CommercialAgent", "promos store 2"),
        ]
        for sid, msg, expected_agent, label in real_tests:
            r = await send(client, msg, f"scan_real_{label}", store_id=sid)
            score = 1 if r["agent"] == expected_agent else 0.5
            record("Boutiques Réelles", label, expected_agent, r["agent"], score, weight=1.5)

        # ═══════════════════════════════════════════════════════════
        # 12. QUALITÉ DES RÉPONSES (longueur, pertinence)
        # ═══════════════════════════════════════════════════════════
        print("\n📊 12. QUALITÉ DES RÉPONSES")
        quality_tests = [
            ("je cherche un telephone", "réponse < 300 chars", "recherche"),
            ("salut", "réponse < 150 chars", "salutation"),
            ("tu peux me faire un prix", "réponse < 300 chars", "négociation"),
        ]
        for msg, criteria, label in quality_tests:
            r = await send(client, msg, f"scan_qual_{label}")
            reply_len = len(r.get("text", ""))
            if "300" in criteria:
                score = 1 if reply_len < 300 else 0.5
            elif "150" in criteria:
                score = 1 if reply_len < 150 else 0.5
            else:
                score = 1
            record("Qualité Réponses", f"{label} ({reply_len} chars)", criteria, f"{reply_len} chars", score, weight=1)

        # ═══════════════════════════════════════════════════════════
        # CALCUL DU SCORE GLOBAL
        # ═══════════════════════════════════════════════════════════
        print("\n" + "=" * 70)
        print("RÉSULTATS PAR CATÉGORIE")
        print("=" * 70)

        categories = {}
        for r in RESULTS:
            cat = r["category"]
            if cat not in categories:
                categories[cat] = {"total_score": 0, "total_weight": 0, "tests": 0, "passed": 0}
            categories[cat]["total_score"] += r["score"] * r["weight"]
            categories[cat]["total_weight"] += r["weight"]
            categories[cat]["tests"] += 1
            if r["score"] == 1:
                categories[cat]["passed"] += 1

        total_score = 0
        total_weight = 0
        for cat, data in categories.items():
            pct = (data["total_score"] / data["total_weight"]) * 100 if data["total_weight"] > 0 else 0
            print(f"  {cat}: {pct:.1f}% ({data['passed']}/{data['tests']} tests passés)")
            total_score += data["total_score"]
            total_weight += data["total_weight"]

        global_pct = (total_score / total_weight) * 100 if total_weight > 0 else 0
        print(f"\n{'=' * 70}")
        print(f"  SCORE GLOBAL DE MATURITÉ: {global_pct:.1f}%")
        print(f"{'=' * 70}")

        # Interprétation
        if global_pct >= 80:
            print("  → Tracy est MÛRE et prête pour les utilisateurs réels ✅")
        elif global_pct >= 60:
            print("  → Tracy est à 60% de maturité — quelques ajustements nécessaires ⚠️")
        elif global_pct >= 40:
            print("  → Tracy nécessite plus d'entraînement avant production ❌")
        else:
            print("  → Tracy n'est pas prête — entraînement intensif requis ❌")

        # Détail des échecs
        failures = [r for r in RESULTS if r["score"] < 1]
        if failures:
            print(f"\n{'=' * 70}")
            print(f"  POINTS À AMÉLIORER ({len(failures)} tests)")
            print(f"{'=' * 70}")
            for f in failures:
                print(f"  ❌ [{f['category']}] {f['test']}: attendu={f['expected']}, obtenu={f['actual']}")

asyncio.run(main())
