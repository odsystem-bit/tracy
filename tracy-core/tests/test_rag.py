"""Tests pour le module RAG (embeddings, retriever, tool search_knowledge).

Tests unitaires avec mocks — aucun appel réel à OpenAI ou Mantota.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.rag.embeddings import EmbeddingError, EmbeddingService
from app.rag.retriever import KnowledgeChunk, KnowledgeRetriever, classify_relevance
from app.tools.base import ToolContext
from app.tools.search_knowledge import SearchKnowledgeTool


# ── EmbeddingService ────────────────────────────────────────────────


class TestEmbeddingService:
    """Tests du service d'embedding OpenAI."""

    @pytest.fixture
    def mock_openai_response(self):
        """Mock d'une réponse OpenAI embeddings.create."""
        mock_data = MagicMock()
        mock_data.embedding = [0.1] * 1536
        mock_data.index = 0
        mock_response = MagicMock()
        mock_response.data = [mock_data]
        return mock_response

    @pytest.mark.asyncio
    async def test_embed_success(self, mock_openai_response):
        """Génère un embedding de 1536 dimensions."""
        service = EmbeddingService(api_key="test-key", retry_max=1)

        with patch.object(service._client.embeddings, "create", new_callable=AsyncMock, return_value=mock_openai_response):
            embedding = await service.embed("Dantokpa est le plus grand marché d'Afrique de l'Ouest")

        assert len(embedding) == 1536
        assert all(isinstance(v, float) for v in embedding)

    @pytest.mark.asyncio
    async def test_embed_empty_text_raises(self):
        """Lève EmbeddingError pour un texte vide."""
        service = EmbeddingService(api_key="test-key", retry_max=1)
        with pytest.raises(EmbeddingError, match="vide"):
            await service.embed("")

    @pytest.mark.asyncio
    async def test_embed_retry_on_failure(self):
        """Retrie avec backoff exponentiel sur erreur."""
        service = EmbeddingService(api_key="test-key", retry_max=3)

        call_count = 0

        async def failing_then_success(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("API error")
            mock_data = MagicMock()
            mock_data.embedding = [0.2] * 1536
            mock_data.index = 0
            mock_resp = MagicMock()
            mock_resp.data = [mock_data]
            return mock_resp

        with patch("app.rag.embeddings.asyncio.sleep", new_callable=AsyncMock), \
             patch.object(service._client.embeddings, "create", new_callable=AsyncMock, side_effect=failing_then_success):
            embedding = await service.embed("test text")

        assert call_count == 3
        assert len(embedding) == 1536

    @pytest.mark.asyncio
    async def test_embed_all_retries_exhausted(self):
        """Lève EmbeddingError après épuisement des retries."""
        service = EmbeddingService(api_key="test-key", retry_max=2)

        with patch("app.rag.embeddings.asyncio.sleep", new_callable=AsyncMock), \
             patch.object(service._client.embeddings, "create", new_callable=AsyncMock, side_effect=Exception("API down")):
            with pytest.raises(EmbeddingError, match="2 tentatives"):
                await service.embed("test")

    @pytest.mark.asyncio
    async def test_embed_batch_success(self):
        """Génère des embeddings en batch."""
        service = EmbeddingService(api_key="test-key", retry_max=1)

        mock_data1 = MagicMock()
        mock_data1.embedding = [0.1] * 1536
        mock_data1.index = 0
        mock_data2 = MagicMock()
        mock_data2.embedding = [0.2] * 1536
        mock_data2.index = 1
        mock_response = MagicMock()
        mock_response.data = [mock_data1, mock_data2]

        with patch.object(service._client.embeddings, "create", new_callable=AsyncMock, return_value=mock_response):
            embeddings = await service.embed_batch(["text 1", "text 2"])

        assert len(embeddings) == 2
        assert len(embeddings[0]) == 1536
        assert len(embeddings[1]) == 1536

    @pytest.mark.asyncio
    async def test_embed_batch_empty_list(self):
        """Retourne une liste vide pour une entrée vide."""
        service = EmbeddingService(api_key="test-key", retry_max=1)
        result = await service.embed_batch([])
        assert result == []


# ── KnowledgeRetriever ──────────────────────────────────────────────


class TestKnowledgeRetriever:
    """Tests du retriever RAG."""

    @pytest.fixture
    def mock_embedding_service(self):
        service = AsyncMock(spec=EmbeddingService)
        service.embed = AsyncMock(return_value=[0.1] * 1536)
        return service

    @pytest.fixture
    def mock_mantota_client(self):
        client = MagicMock()
        client.search_knowledge = AsyncMock(return_value={
            "results": [
                {
                    "id": 1,
                    "content": "Dantokpa est le plus grand marché à ciel ouvert d'Afrique de l'Ouest.",
                    "score": 0.92,
                    "title": "Marchés du Bénin",
                    "category": "benin_marches",
                    "country_id": 1,
                },
                {
                    "id": 2,
                    "content": "MTN MoMo et Moov Money sont les deux principaux moyens de paiement mobile au Bénin.",
                    "score": 0.85,
                    "title": "Moyens de paiement Bénin",
                    "category": "benin_paiements",
                    "country_id": 1,
                },
            ]
        })
        return client

    @pytest.mark.asyncio
    async def test_search_knowledge_success(self, mock_embedding_service, mock_mantota_client):
        """Retourne des chunks pertinents."""
        retriever = KnowledgeRetriever(mock_embedding_service, mock_mantota_client)
        chunks = await retriever.search_knowledge("marchés au Bénin", country_id=1, top_k=5)

        assert len(chunks) == 2
        assert chunks[0].title == "Marchés du Bénin"
        assert chunks[0].score == 0.92
        assert chunks[1].title == "Moyens de paiement Bénin"
        mock_embedding_service.embed.assert_called_once_with("marchés au Bénin")
        mock_mantota_client.search_knowledge.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_knowledge_empty_query(self, mock_embedding_service, mock_mantota_client):
        """Retourne une liste vide pour une requête vide."""
        retriever = KnowledgeRetriever(mock_embedding_service, mock_mantota_client)
        chunks = await retriever.search_knowledge("", top_k=5)

        assert chunks == []
        mock_embedding_service.embed.assert_not_called()

    @pytest.mark.asyncio
    async def test_search_knowledge_embedding_failure(self, mock_embedding_service, mock_mantota_client):
        """Retourne une liste vide si l'embedding échoue."""
        mock_embedding_service.embed = AsyncMock(side_effect=EmbeddingError("API down"))
        retriever = KnowledgeRetriever(mock_embedding_service, mock_mantota_client)
        chunks = await retriever.search_knowledge("test", top_k=5)

        assert chunks == []
        mock_mantota_client.search_knowledge.assert_not_called()

    @pytest.mark.asyncio
    async def test_search_knowledge_mantota_failure(self, mock_embedding_service, mock_mantota_client):
        """Retourne une liste vide si Mantota échoue."""
        from app.mantota_client.exceptions import MantotaApiError
        mock_mantota_client.search_knowledge = AsyncMock(side_effect=MantotaApiError("ERR", "Server error", 500))
        retriever = KnowledgeRetriever(mock_embedding_service, mock_mantota_client)
        chunks = await retriever.search_knowledge("test", top_k=5)

        assert chunks == []

    def test_format_chunks_for_prompt(self):
        """Formate les chunks pour injection dans le prompt."""
        chunks = [
            KnowledgeChunk(id=1, content="Dantokpa est grand.", score=0.9, title="Marchés", category="benin_marches", country_id=1),
            KnowledgeChunk(id=2, content="MTN MoMo.", score=0.8, title="Paiements", category="benin_paiements", country_id=1),
        ]
        retriever = KnowledgeRetriever(MagicMock(), MagicMock())
        formatted = retriever.format_chunks_for_prompt(chunks)

        assert "CONTEXTE DE CONNAISSANCE" in formatted
        assert "Dantokpa est grand." in formatted
        assert "MTN MoMo." in formatted
        assert "Marchés" in formatted

    def test_format_chunks_empty(self):
        """Retourne une chaîne vide pour une liste vide."""
        retriever = KnowledgeRetriever(MagicMock(), MagicMock())
        assert retriever.format_chunks_for_prompt([]) == ""


# ── SearchKnowledgeTool ─────────────────────────────────────────────


class TestSearchKnowledgeTool:
    """Tests du tool search_knowledge (28e tool)."""

    @pytest.fixture
    def ctx(self):
        return ToolContext(agent_name="CommercialAgent", correlation_id="test-corr-1")

    @pytest.fixture
    def mock_retriever_with_results(self):
        retriever = AsyncMock(spec=KnowledgeRetriever)
        retriever.search_knowledge = AsyncMock(return_value=[
            KnowledgeChunk(id=1, content="Dantokpa est le plus grand marché.", score=0.9, title="Marchés Bénin", category="benin_marches", country_id=1),
        ])
        retriever.format_chunks_for_prompt = MagicMock(return_value="CONTEXTE: Dantokpa est le plus grand marché.")
        return retriever

    @pytest.fixture
    def mock_retriever_empty(self):
        retriever = AsyncMock(spec=KnowledgeRetriever)
        retriever.search_knowledge = AsyncMock(return_value=[])
        retriever.format_chunks_for_prompt = MagicMock(return_value="")
        return retriever

    @pytest.mark.asyncio
    async def test_tool_success(self, mock_retriever_with_results, ctx):
        """Tool retourne les chunks et le contexte formaté avec relevance='correct'."""
        tool = SearchKnowledgeTool(mock_retriever_with_results)
        result = await tool.execute(ctx, query="marchés du Bénin", country_id=1, top_k=5)

        assert result.success is True
        assert result.data is not None
        assert len(result.data.chunks) == 1
        assert result.data.chunks[0]["title"] == "Marchés Bénin"
        assert "Dantokpa" in result.data.formatted_context
        assert result.data.relevance == "correct"

    @pytest.mark.asyncio
    async def test_tool_empty_query(self, mock_retriever_with_results, ctx):
        """Tool échoue avec INVALID_QUERY pour une requête vide."""
        tool = SearchKnowledgeTool(mock_retriever_with_results)
        result = await tool.execute(ctx, query="", top_k=5)

        assert result.success is False
        assert result.error.code == "INVALID_QUERY"

    @pytest.mark.asyncio
    async def test_tool_no_results_returns_incorrect(self, mock_retriever_empty, ctx):
        """Tool retourne success avec relevance='incorrect' et un contexte de repli si aucun chunk."""
        tool = SearchKnowledgeTool(mock_retriever_empty)
        result = await tool.execute(ctx, query="question obscure", top_k=5)

        assert result.success is True
        assert result.data is not None
        assert result.data.relevance == "incorrect"
        assert len(result.data.chunks) == 0
        assert "AUCUNE INFORMATION FIABLE" in result.data.formatted_context

    def test_tool_name(self, mock_retriever_with_results):
        """Le nom du tool est 'search_knowledge'."""
        tool = SearchKnowledgeTool(mock_retriever_with_results)
        assert tool.name == "search_knowledge"

    def test_tool_allowed_agents(self, mock_retriever_with_results):
        """Seuls CommercialAgent et SupportAgent sont autorisés."""
        tool = SearchKnowledgeTool(mock_retriever_with_results)
        assert "CommercialAgent" in tool.allowed_agents
        assert "SupportAgent" in tool.allowed_agents
        assert "OrderAgent" not in tool.allowed_agents
        assert "PaymentAgent" not in tool.allowed_agents

    def test_tool_permission_commercial(self, mock_retriever_with_results):
        """CommercialAgent est autorisé."""
        tool = SearchKnowledgeTool(mock_retriever_with_results)
        assert tool.is_allowed("CommercialAgent") is True

    def test_tool_permission_support(self, mock_retriever_with_results):
        """SupportAgent est autorisé."""
        tool = SearchKnowledgeTool(mock_retriever_with_results)
        assert tool.is_allowed("SupportAgent") is True

    def test_tool_permission_order_denied(self, mock_retriever_with_results):
        """OrderAgent n'est PAS autorisé."""
        tool = SearchKnowledgeTool(mock_retriever_with_results)
        assert tool.is_allowed("OrderAgent") is False

    def test_tool_permission_payment_denied(self, mock_retriever_with_results):
        """PaymentAgent n'est PAS autorisé."""
        tool = SearchKnowledgeTool(mock_retriever_with_results)
        assert tool.is_allowed("PaymentAgent") is False

    # ── RAG Correctif : classify_relevance ──

    def test_classify_relevance_correct(self):
        """Score >= 0.85 → correct."""
        chunks = [KnowledgeChunk(id=1, content="test", score=0.90, title="T", category="c", country_id=None)]
        assert classify_relevance(chunks) == "correct"

    def test_classify_relevance_correct_at_threshold(self):
        """Score == 0.85 (exactement le seuil) → correct."""
        chunks = [KnowledgeChunk(id=1, content="test", score=0.85, title="T", category="c", country_id=None)]
        assert classify_relevance(chunks) == "correct"

    def test_classify_relevance_ambiguous(self):
        """Score entre 0.6 et 0.85 → ambiguous."""
        chunks = [KnowledgeChunk(id=1, content="test", score=0.70, title="T", category="c", country_id=None)]
        assert classify_relevance(chunks) == "ambiguous"

    def test_classify_relevance_ambiguous_at_threshold(self):
        """Score == 0.6 (exactement le seuil) → ambiguous."""
        chunks = [KnowledgeChunk(id=1, content="test", score=0.60, title="T", category="c", country_id=None)]
        assert classify_relevance(chunks) == "ambiguous"

    def test_classify_relevance_incorrect(self):
        """Score < 0.6 → incorrect."""
        chunks = [KnowledgeChunk(id=1, content="test", score=0.40, title="T", category="c", country_id=None)]
        assert classify_relevance(chunks) == "incorrect"

    def test_classify_relevance_empty_list(self):
        """Liste vide → incorrect."""
        assert classify_relevance([]) == "incorrect"

    def test_classify_relevance_uses_best_score(self):
        """Utilise le premier chunk (meilleur score) pour classifier."""
        chunks = [
            KnowledgeChunk(id=1, content="good", score=0.90, title="T", category="c", country_id=None),
            KnowledgeChunk(id=2, content="bad", score=0.30, title="T2", category="c", country_id=None),
        ]
        assert classify_relevance(chunks) == "correct"

    def test_classify_relevance_custom_thresholds(self):
        """Seuils personnalisés fonctionnent."""
        chunks = [KnowledgeChunk(id=1, content="test", score=0.75, title="T", category="c", country_id=None)]
        assert classify_relevance(chunks, score_correct=0.80, score_ambiguous=0.50) == "ambiguous"

    # ── RAG Correctif : tool avec relevance incorrect + gap logging ──

    @pytest.mark.asyncio
    async def test_tool_incorrect_logs_gap(self, ctx):
        """Quand relevance='incorrect', le tool logge la lacune en arrière-plan."""
        retriever = AsyncMock(spec=KnowledgeRetriever)
        retriever.search_knowledge = AsyncMock(return_value=[
            KnowledgeChunk(id=1, content="low", score=0.30, title="T", category="c", country_id=None),
        ])
        retriever.format_chunks_for_prompt = MagicMock(return_value="")
        # Mock the internal _embeddings and _mantota for gap logging
        mock_embedding_service = AsyncMock()
        mock_embedding_service.embed = AsyncMock(return_value=[0.1] * 1536)
        mock_mantota = AsyncMock()
        mock_mantota.log_knowledge_gap = AsyncMock(return_value={"action": "created", "gap_id": 1})
        retriever._embeddings = mock_embedding_service
        retriever._mantota = mock_mantota

        tool = SearchKnowledgeTool(retriever)
        result = await tool.execute(ctx, query="question très obscure", country_id=1, top_k=5)

        assert result.success is True
        assert result.data.relevance == "incorrect"
        assert "AUCUNE INFORMATION FIABLE" in result.data.formatted_context

        # Le gap logging est fire-and-forget (asyncio.create_task) — attend qu'il se termine
        import asyncio
        await asyncio.sleep(0.05)

        # Vérifie que log_knowledge_gap a été appelé
        mock_mantota.log_knowledge_gap.assert_called_once()
        call_kwargs = mock_mantota.log_knowledge_gap.call_args
        assert call_kwargs.kwargs["query_text"] == "question très obscure"
        assert call_kwargs.kwargs["country_id"] == 1

    @pytest.mark.asyncio
    async def test_tool_incorrect_gap_log_failure_does_not_crash(self, ctx):
        """Si le gap logging échoue, le tool retourne quand même le résultat de repli."""
        retriever = AsyncMock(spec=KnowledgeRetriever)
        retriever.search_knowledge = AsyncMock(return_value=[])
        retriever.format_chunks_for_prompt = MagicMock(return_value="")
        mock_embedding_service = AsyncMock()
        mock_embedding_service.embed = AsyncMock(side_effect=Exception("OpenAI down"))
        mock_mantota = AsyncMock()
        mock_mantota.log_knowledge_gap = AsyncMock()
        retriever._embeddings = mock_embedding_service
        retriever._mantota = mock_mantota

        tool = SearchKnowledgeTool(retriever)
        result = await tool.execute(ctx, query="question obscure", top_k=5)

        assert result.success is True
        assert result.data.relevance == "incorrect"

        # Le gap logging échoue silencieusement
        import asyncio
        await asyncio.sleep(0.05)
        mock_mantota.log_knowledge_gap.assert_not_called()

    @pytest.mark.asyncio
    async def test_tool_ambiguous_adds_warning(self, ctx):
        """Quand relevance='ambiguous', le contexte formaté inclut un avertissement de prudence."""
        retriever = AsyncMock(spec=KnowledgeRetriever)
        retriever.search_knowledge = AsyncMock(return_value=[
            KnowledgeChunk(id=1, content="maybe relevant", score=0.70, title="T", category="c", country_id=None),
        ])
        retriever.format_chunks_for_prompt = MagicMock(return_value="CONTEXTE: maybe relevant")

        tool = SearchKnowledgeTool(retriever)
        result = await tool.execute(ctx, query="question ambiguë", top_k=5)

        assert result.success is True
        assert result.data.relevance == "ambiguous"
        assert "ATTENTION" in result.data.formatted_context
        assert "CONTEXTE: maybe relevant" in result.data.formatted_context
