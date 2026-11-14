#!/usr/bin/env python3
"""Test P3 — Restaurant, Campagne, Vendeur (Catalog)"""

import asyncio
import httpx

TRACY_URL = "http://127.0.0.1:8001"
API_KEY = "tracy-dev-key-2026"

async def send(client, text, conv_id, store_id="public"):
    resp = await client.post(
        f"{TRACY_URL}/chat",
        json={"store_id": store_id, "customer_id": "test_p3", "text": text, "conversation_id": conv_id},
        headers={"X-Api-Key": API_KEY},
        timeout=60,
    )
    if resp.status_code != 200:
        return {"text": f"HTTP {resp.status_code}", "agent": "?", "tools_used": [], "cards": []}
    return resp.json()

async def main():
    async with httpx.AsyncClient() as client:

        # ── P3.1 — Restaurant ─────────────────────────────────
        print("="*60)
        print("P3.1 — Restaurant (public)")

        conv_r = "p3_restaurant"
        tests_r = [
            "je veux manger",
            "tu as des restaurants",
            "je cherche un restaurant",
            "montre-moi le menu",
            "je veux commander un plat",
            "tu as du poulet braisé",
            "c'est quoi les horaires",
        ]
        for msg in tests_r:
            r = await send(client, msg, conv_r)
            print(f"\nMSG: {msg}")
            print(f"AGENT: {r.get('agent','?')} | TOOLS: {r.get('tools_used',[])} | CARDS: {len(r.get('cards') or [])}")
            print(f"REPLY: {r.get('text','')[:150]}")

        # ── P3.2 — Campagne ───────────────────────────────────
        print("\n" + "="*60)
        print("P3.2 — Campagne (public)")

        conv_c = "p3_campaign"
        tests_c = [
            "je veux lancer une campagne",
            "relance mon panier abandonné",
            "montre-moi les statistiques de ma campagne",
            "je veux devenir partenaire",
            "c'est quoi mes commissions",
        ]
        for msg in tests_c:
            r = await send(client, msg, conv_c)
            print(f"\nMSG: {msg}")
            print(f"AGENT: {r.get('agent','?')} | TOOLS: {r.get('tools_used',[])} | CARDS: {len(r.get('cards') or [])}")
            print(f"REPLY: {r.get('text','')[:150]}")

        # ── P3.3 — Vendeur / Catalog ──────────────────────────
        print("\n" + "="*60)
        print("P3.3 — Vendeur / Catalog (public)")

        conv_v = "p3_vendor"
        tests_v = [
            "je veux créer une boutique",
            "ajoute un produit à mon catalogue",
            "modifie le prix du téléphone",
            "montre-moi mon catalogue",
            "configure mes règles de négociation",
            "baisse le prix du samsung à 80000",
            "mets le téléphone en rupture de stock",
        ]
        for msg in tests_v:
            r = await send(client, msg, conv_v)
            print(f"\nMSG: {msg}")
            print(f"AGENT: {r.get('agent','?')} | TOOLS: {r.get('tools_used',[])} | CARDS: {len(r.get('cards') or [])}")
            print(f"REPLY: {r.get('text','')[:150]}")

asyncio.run(main())
