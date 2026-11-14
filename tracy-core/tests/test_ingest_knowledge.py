"""Tests pour le script d'ingestion RAG (découpage sémantique).

Teste uniquement la fonction de découpage (chunk_document) — pas d'appels API.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ajoute scripts/ au path pour importer ingest_knowledge
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from ingest_knowledge import chunk_document


class TestChunkDocument:
    """Tests du découpage sémantique de documents."""

    def test_short_document_single_chunk(self):
        """Un document court reste en un seul chunk."""
        content = "Dantokpa est le plus grand marché d'Afrique de l'Ouest."
        chunks = chunk_document(content)
        assert len(chunks) == 1
        assert "Dantokpa" in chunks[0]

    def test_split_by_sections(self):
        """Découpe par sections séparées par '---'."""
        content = (
            "Dantokpa est le plus grand marché.\n\n"
            "---\n"
            "Ganhi est le quartier des affaires.\n\n"
            "---\n"
            "Ouando est à Porto-Novo."
        )
        chunks = chunk_document(content)
        assert len(chunks) == 3
        assert "Dantokpa" in chunks[0]
        assert "Ganhi" in chunks[1]
        assert "Ouando" in chunks[2]

    def test_split_by_markdown_headers(self):
        """Découpe par titres markdown '# '."""
        content = (
            "# Marchés du Bénin\n"
            "Dantokpa à Cotonou.\n\n"
            "# Moyens de paiement\n"
            "MTN MoMo et Moov Money."
        )
        chunks = chunk_document(content)
        assert len(chunks) >= 2
        assert any("Dantokpa" in c for c in chunks)
        assert any("MTN MoMo" in c for c in chunks)

    def test_long_section_split_by_paragraphs(self):
        """Une section trop longue est découpée par paragraphes."""
        para1 = "Dantokpa est le plus grand marché à ciel ouvert d'Afrique de l'Ouest. " * 10
        para2 = "Ganhi est le quartier des affaires de Cotonou. " * 10
        content = f"{para1}\n\n{para2}"
        chunks = chunk_document(content, max_chunk_size=500)
        assert len(chunks) >= 2
        # Chaque chunk ne dépasse pas la taille max (avec tolérance pour les phrases)
        for chunk in chunks:
            assert len(chunk) <= 600  # tolérance pour découpage par phrases

    def test_empty_content(self):
        """Contenu vide retourne une liste vide."""
        chunks = chunk_document("")
        assert chunks == []

    def test_whitespace_only(self):
        """Contenu avec uniquement des espaces retourne une liste vide."""
        chunks = chunk_document("   \n\n   \n  ")
        assert chunks == []

    def test_chunk_preserves_content(self):
        """Le contenu original est préservé dans les chunks (au complet)."""
        sections = [
            "Dantokpa est le plus grand marché d'Afrique de l'Ouest.",
            "Il se trouve à Cotonou, la capitale économique du Bénin.",
            "On y trouve de tout : tissus, alimentation, électronique.",
        ]
        content = "\n---\n".join(sections)
        chunks = chunk_document(content)
        assert len(chunks) == 3
        for i, section in enumerate(sections):
            assert section in chunks[i]

    def test_very_long_paragraph_split_by_sentences(self):
        """Un paragraphe très long est découpé par phrases."""
        sentences = [f"Phrase numéro {i} sur le Bénin. " for i in range(50)]
        content = "".join(sentences)
        chunks = chunk_document(content, max_chunk_size=200)
        assert len(chunks) > 1
        # Aucun chunk ne devrait être excessivement long
        for chunk in chunks:
            assert len(chunk) <= 300
