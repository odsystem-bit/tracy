"""app/rag/ — Module RAG (Retrieval-Augmented Generation) pour Tracy Core.

Rôle : fournir une recherche sémantique dans la base de connaissances Mantota
(via pgvector sur PostgreSQL) pour enrichir le contexte de reformulation du LLM.

RÈGLE FONDAMENTALE : le LLM reformule, il ne décide jamais.
Les résultats récupérés par ce module sont injectés dans le prompt de reformulation
finale du LLM. Ils ne déclenchent jamais d'action métier (prix, commande, paiement).
"""
