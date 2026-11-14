#!/usr/bin/env python3
"""Test complet P1 — Recherche avancée, Négociation, Commande, Support"""

import asyncio
import httpx
import json
import sys

TRACY_URL = "http://127.0.0.1:8001"
STORE_ID = "public"
CUSTOMER_ID = "test_user_p1"
API_KEY = "tracy-dev-key-2026"

async def send_message(client, text, conv_id):
    resp = await client.post(
        f"{TRACY_URL}/chat",
        json={
            "store_id": STORE_ID,
            "customer_id": CUSTOMER_ID,
            "text": text,
            "conversation_id": conv_id,
        },
        headers={"X-Api-Key": API_KEY},
        timeout=60,
    )
    data = resp.json()
    return data

async def main():
    async with httpx.AsyncClient() as client:
        conv_id = f"test_p1_{asyncio.get_event_loop().time()}"
        
        tests = [
            # P1.1 — Recherche avancée
            ("Je cherche un telephone entre 50000 et 100000", "Gamme de prix"),
            ("Tu as un samsung bleu", "Couleur + marque"),
            ("Montre-moi une robe rouge taille M", "Couleur + taille"),
            ("Je veux un parfum", "Nouvelle catégorie"),
            ("Tu as des jouets pour enfant", "Nouvelle catégorie"),
            ("Montre-moi le moins cher en telephone", "Tri ascendant"),
            ("Tu as un laptop", "Nouvelle catégorie"),
            ("Je cherche une jupe noire", "Couleur + nouvelle catégorie"),
            
            # P1.2 — Négociation (public = pas de négociation)
            ("C'est trop cher tu peux faire un prix", "Négo sur public"),
            ("Tu peux faire une remise", "Négo sur public 2"),
            
            # P1.3 — Commande (public = pas de commande)
            ("Je veux commander", "Commande sur public"),
            ("Comment je paie", "Paiement sur public"),
            ("Annule ma commande", "Annulation sur public"),
            
            # P1.4 — Support (public = pas de support)
            ("Mon colis n'est pas arrivé", "Support sur public"),
            ("Je veux parler à un humain", "Escalade humaine"),
            ("C'est une arnaque", "Litige sur public"),
        ]
        
        for i, (msg, label) in enumerate(tests):
            try:
                data = await send_message(client, msg, conv_id)
                reply = data.get("text", "NO REPLY")
                agent = data.get("agent", "?")
                tools = data.get("tools_used", [])
                cards = len(data.get("cards") or [])
                print(f"\n{'='*60}")
                print(f"TEST {i+1}: {label}")
                print(f"MSG: {msg}")
                print(f"AGENT: {agent} | TOOLS: {tools} | CARDS: {cards}")
                print(f"REPLY: {reply[:200]}")
            except Exception as e:
                print(f"\n{'='*60}")
                print(f"TEST {i+1}: {label} — ERROR: {e}")

asyncio.run(main())
