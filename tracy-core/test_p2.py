#!/usr/bin/env python3
"""Test P2 — Gestion conversationnelle, contexte boutique, mémoire"""

import asyncio
import httpx

TRACY_URL = "http://127.0.0.1:8001"
API_KEY = "tracy-dev-key-2026"

async def send(client, text, conv_id, store_id="public"):
    resp = await client.post(
        f"{TRACY_URL}/chat",
        json={"store_id": store_id, "customer_id": "test_p2", "text": text, "conversation_id": conv_id},
        headers={"X-Api-Key": API_KEY},
        timeout=60,
    )
    if resp.status_code != 200:
        return {"text": f"HTTP {resp.status_code}", "agent": "?", "tools_used": [], "cards": []}
    return resp.json()

async def main():
    async with httpx.AsyncClient() as client:
        # P2.1 — Change d'avis (conversation en 2 messages)
        conv1 = "p2_change_avis"
        print("="*60)
        print("P2.1 — Change d'avis")
        r = await send(client, "je cherche une robe", conv1)
        print(f"MSG 1: je cherche une robe")
        print(f"REPLY: {r.get('text','')[:150]}")
        r = await send(client, "non finalement je veux un telephone", conv1)
        print(f"MSG 2: non finalement je veux un telephone")
        print(f"AGENT: {r.get('agent','?')} | TOOLS: {r.get('tools_used',[])} | CARDS: {len(r.get('cards') or [])}")
        print(f"REPLY: {r.get('text','')[:150]}")

        # P2.2 — Conseil
        conv2 = "p2_conseil"
        print("\n" + "="*60)
        print("P2.2 — Conseil")
        r = await send(client, "je cherche un telephone mais je ne sais pas lequel choisir", conv2)
        print(f"AGENT: {r.get('agent','?')} | TOOLS: {r.get('tools_used',[])} | CARDS: {len(r.get('cards') or [])}")
        print(f"REPLY: {r.get('text','')[:200]}")

        # P2.3 — Indécision
        conv3 = "p2_indecision"
        print("\n" + "="*60)
        print("P2.3 — Indécision")
        r = await send(client, "je ne sais pas quoi choisir entre les deux", conv3)
        print(f"AGENT: {r.get('agent','?')} | TOOLS: {r.get('tools_used',[])} | CARDS: {len(r.get('cards') or [])}")
        print(f"REPLY: {r.get('text','')[:200]}")

        # P2.4 — Multi-sujets
        conv4 = "p2_multi"
        print("\n" + "="*60)
        print("P2.4 — Multi-sujets")
        r = await send(client, "je veux un telephone et aussi une robe", conv4)
        print(f"AGENT: {r.get('agent','?')} | TOOLS: {r.get('tools_used',[])} | CARDS: {len(r.get('cards') or [])}")
        print(f"REPLY: {r.get('text','')[:200]}")

        # P2.5 — Contexte boutique
        conv5 = "p2_boutique"
        print("\n" + "="*60)
        print("P2.5 — Contexte boutique")
        for msg in ["tu vends quoi ici", "tu as des promotions", "tu livres ou", "c'est quoi les frais de livraison", "tu es ouverte quand"]:
            r = await send(client, msg, conv5)
            print(f"\nMSG: {msg}")
            print(f"AGENT: {r.get('agent','?')} | TOOLS: {r.get('tools_used',[])} | CARDS: {len(r.get('cards') or [])}")
            print(f"REPLY: {r.get('text','')[:150]}")

        # P2.6 — Mémoire
        conv6 = "p2_memoire"
        print("\n" + "="*60)
        print("P2.6 — Mémoire")
        r = await send(client, "souviens-toi que je fais du 42 en chaussure", conv6)
        print(f"MSG: souviens-toi que je fais du 42")
        print(f"AGENT: {r.get('agent','?')} | TOOLS: {r.get('tools_used',[])}")
        print(f"REPLY: {r.get('text','')[:150]}")
        r = await send(client, "tu me connais non ?", conv6)
        print(f"\nMSG: tu me connais non ?")
        print(f"AGENT: {r.get('agent','?')} | TOOLS: {r.get('tools_used',[])}")
        print(f"REPLY: {r.get('text','')[:150]}")

        # P2.7 — Messages spéciaux
        conv7 = "p2_special"
        print("\n" + "="*60)
        print("P2.7 — Messages spéciaux")
        for msg in ["JE VEUX UN TELEPHONE MAINTENANT", "je cherche un tél 🔥🔥", "wai je veux un sac cho"]:
            r = await send(client, msg, conv7)
            print(f"\nMSG: {msg}")
            print(f"AGENT: {r.get('agent','?')} | TOOLS: {r.get('tools_used',[])} | CARDS: {len(r.get('cards') or [])}")
            print(f"REPLY: {r.get('text','')[:150]}")

asyncio.run(main())
