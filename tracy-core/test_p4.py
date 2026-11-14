#!/usr/bin/env python3
"""Test P4 — Multi-pays/devises, Vision, Audio"""

import asyncio
import httpx
import base64
import json

TRACY_URL = "http://127.0.0.1:8001"
API_KEY = "tracy-dev-key-2026"

async def send(client, text, conv_id, store_id="public"):
    resp = await client.post(
        f"{TRACY_URL}/chat",
        json={"store_id": store_id, "customer_id": "test_p4", "text": text, "conversation_id": conv_id},
        headers={"X-Api-Key": API_KEY},
        timeout=60,
    )
    if resp.status_code != 200:
        return {"text": f"HTTP {resp.status_code}", "agent": "?", "tools_used": [], "cards": []}
    return resp.json()

async def main():
    async with httpx.AsyncClient() as client:

        # ── P4.1 — Multi-pays / Devises ───────────────────────
        print("="*60)
        print("P4.1 — Multi-pays / Devises")

        conv_d = "p4_devises"
        tests_d = [
            "quelle monnaie tu accepte",
            "tu accepte le naira",
            "c'est quoi la devise",
            "je peux payer en dollar",
            "tu livre dans quels pays",
        ]
        for msg in tests_d:
            r = await send(client, msg, conv_d)
            print(f"\nMSG: {msg}")
            print(f"AGENT: {r.get('agent','?')} | TOOLS: {r.get('tools_used',[])} | CARDS: {len(r.get('cards') or [])}")
            print(f"REPLY: {r.get('text','')[:150]}")

        # ── P4.2 — Vision (endpoint direct) ───────────────────
        print("\n" + "="*60)
        print("P4.2 — Vision (endpoints API)")

        # Test health du module vision
        try:
            # Crée une image simple (1x1 pixel rouge)
            from PIL import Image
            import io
            img = Image.new("RGB", (100, 100), color=(255, 0, 0))
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            img_b64 = base64.b64encode(buf.getvalue()).decode()

            # Test compute-embedding
            resp = await client.post(
                f"{TRACY_URL}/vision/compute-embedding",
                json={
                    "image_base64": img_b64,
                    "product_id": "test_001",
                    "store_id": "1",
                    "image_url": "https://example.com/test.jpg",
                    "augment": False,
                },
                headers={"X-Api-Key": API_KEY},
                timeout=120,
            )
            if resp.status_code == 200:
                data = resp.json()
                print(f"\ncompute-embedding: OK (count={data.get('count')})")
            else:
                print(f"\ncompute-embedding: HTTP {resp.status_code} — {resp.text[:200]}")
        except Exception as e:
            print(f"\nVision test: {e}")

        # Test shop-quality
        try:
            resp = await client.get(
                f"{TRACY_URL}/vision/shop-quality/1",
                headers={"X-Api-Key": API_KEY},
                timeout=30,
            )
            if resp.status_code == 200:
                data = resp.json()
                print(f"shop-quality: score={data.get('score')}, level={data.get('level')}")
            else:
                print(f"shop-quality: HTTP {resp.status_code}")
        except Exception as e:
            print(f"shop-quality: {e}")

        # ── P4.3 — Audio (placeholder) ────────────────────────
        print("\n" + "="*60)
        print("P4.3 — Audio (notreel implémenté en V1)")
        print("Audio: prévu pour V2 (WebRTC + transcription)")
        print("Statut: SKIP — dépend de l'app Flutter")

        # ── P4.4 — Tests boutiques réelles multi-contexte ─────
        print("\n" + "="*60)
        print("P4.4 — Boutiques réelles multi-contexte")

        conv_r = "p4_real"
        tests_r = [
            ("1", "je cherche un telephone"),
            ("1", "quelle monnaie tu accepte"),
            ("1", "tu peux me faire un prix"),
            ("1", "je veux payer en naira"),
            ("2", "montre-moi ton catalogue"),
            ("2", "tu as des promotions"),
        ]
        for sid, msg in tests_r:
            r = await send(client, msg, conv_r, store_id=sid)
            print(f"\nSTORE={sid} | MSG: {msg}")
            print(f"  AGENT: {r.get('agent','?')} | TOOLS: {r.get('tools_used',[])} | CARDS: {len(r.get('cards') or [])}")
            print(f"  REPLY: {r.get('text','')[:120]}")

asyncio.run(main())
