"""
Comprehensive tests for the RAG system components.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from backend.rag_system import RAGSystem
from backend.vector_store import VectorStore
from backend.ai_generator import AIGenerator
from backend.document_processor import DocumentProcessor
from backend.session_manager import SessionManager
from backend.models import QueryRequest, CourseChunk
import tempfile
import os


@pytest.fixture
def temp_chroma_path():
    """Create temporary directory for ChromaDB."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield os.path.join(temp_dir, "test_chroma")


@pytest.fixture
def mock_ai_generator():
    """Mock AI generator."""
    generator = Mock(spec=AIGenerator)
    generator.generate_response = AsyncMock(return_value="Test response")
    return generator


@pytest.fixture
def mock_vector_store():
    """Mock vector store."""
    store = Mock(spec=VectorStore)
    store.search_similar_chunks = Mock(return_value=[
        CourseChunk(
            course_title="Test Course",
            lesson_title="Test Lesson",
            content="Test content",
            chunk_id="test-123",
            metadata={}
        )
    ])
    return store


@pytest.fixture
def rag_system(mock_ai_generator, mock_vector_store):
    """Create RAG system with mocked dependencies."""
    with patch('backend.rag_system.AIGenerator', return_value=mock_ai_generator), \
         patch('backend.rag_system.VectorStore', return_value=mock_vector_store), \
         patch('backend.rag_system.SessionManager') as mock_session:
        
        mock_session.return_value.get_session_context.return_value = []
        mock_session.return_value.add_to_session.return_value = None
        
        system = RAGSystem()
        return system


class TestRAGSystem:
    """Test class for RAG system."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_query_basic(self, rag_system):
        """Test basic query processing."""
        query = QueryRequest(
            message="What is the MCP course about?",
            session_id="test-session"
        )
        
        response = await rag_system.process_query(query.message, query.session_id)
        
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_query_with_context(self, rag_system):
        """Test query processing with session context."""
        # Mock session manager to return context
        rag_system.session_manager.get_session_context.return_value = [
            {"role": "user", "content": "Previous question"},
            {"role": "assistant", "content": "Previous answer"}
        ]
        
        query = QueryRequest(
            message="Follow up question",
            session_id="test-session"
        )
        
        response = await rag_system.process_query(query.message, query.session_id)
        
        assert response is not None
        # Verify session context was retrieved
        rag_system.session_manager.get_session_context.assert_called_with("test-session")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_query_empty_message(self, rag_system):
        """Test processing empty message."""
        with pytest.raises(ValueError, match="Query message cannot be empty"):
            await rag_system.process_query("", "test-session")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_query_no_session_id(self, rag_system):
        """Test processing without session ID."""
        response = await rag_system.process_query("Test question", None)
        assert response is not None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_vector_search_integration(self, rag_system):
        """Test integration with vector search."""
        query = "Test query about courses"
        
        # Mock vector store to return specific chunks
        test_chunks = [
            CourseChunk(
                course_title="Advanced RAG",
                lesson_title="Lesson 1",
                content="This is about advanced RAG techniques",
                chunk_id="rag-001",
                metadata={"difficulty": "advanced"}
            )
        ]
        rag_system.vector_store.search_similar_chunks.return_value = test_chunks
        
        response = await rag_system.process_query(query, "test-session")
        
        # Verify vector search was called
        rag_system.vector_store.search_similar_chunks.assert_called_once_with(query, limit=5)
        assert response is not None


class TestVectorStore:
    """Test class for vector store operations."""

    @pytest.mark.unit
    def test_vector_store_initialization(self, temp_chroma_path):
        """Test vector store initialization."""
        store = VectorStore(persist_directory=temp_chroma_path)
        assert store is not None
        assert store.collection_name == "course_chunks"

    @pytest.mark.unit
    @patch('backend.vector_store.chromadb')
    def test_add_chunks(self, mock_chromadb, temp_chroma_path):
        """Test adding chunks to vector store."""
        # Mock ChromaDB client and collection
        mock_client = Mock()
        mock_collection = Mock()
        mock_chromadb.PersistentClient.return_value = mock_client
        mock_client.get_or_create_collection.return_value = mock_collection
        
        store = VectorStore(persist_directory=temp_chroma_path)
        
        chunks = [
            CourseChunk(
                course_title="Test Course",
                lesson_title="Test Lesson",
                content="Test content",
                chunk_id="test-001",
                metadata={}
            )
        ]
        
        store.add_chunks(chunks)
        
        # Verify collection.add was called
        mock_collection.add.assert_called_once()

    @pytest.mark.unit
    @patch('backend.vector_store.chromadb')
    def test_search_similar_chunks(self, mock_chromadb, temp_chroma_path):
        """Test searching similar chunks."""
        # Mock ChromaDB client and collection
        mock_client = Mock()
        mock_collection = Mock()
        mock_chromadb.PersistentClient.return_value = mock_client
        mock_client.get_or_create_collection.return_value = mock_collection
        
        # Mock query results
        mock_collection.query.return_value = {
            'documents': [['Test content']],
            'metadatas': [[{'course_title': 'Test Course', 'lesson_title': 'Test Lesson'}]],
            'ids': [['test-001']]
        }
        
        store = VectorStore(persist_directory=temp_chroma_path)
        results = store.search_similar_chunks("test query", limit=3)
        
        assert len(results) == 1
        assert results[0].content == 'Test content'
        assert results[0].course_title == 'Test Course'


class TestDocumentProcessor:
    """Test class for document processor."""

    @pytest.mark.unit
    def test_create_chunks_from_text(self):
        """Test creating chunks from text."""
        processor = DocumentProcessor()
        
        text = "This is a test document. " * 100  # Long text
        chunks = processor.create_chunks(text, "Test Course", "Test Lesson")
        
        assert len(chunks) > 0
        assert all(chunk.course_title == "Test Course" for chunk in chunks)
        assert all(chunk.lesson_title == "Test Lesson" for chunk in chunks)

    @pytest.mark.unit
    def test_create_chunks_short_text(self):
        """Test creating chunks from short text."""
        processor = DocumentProcessor()
        
        text = "Short text."
        chunks = processor.create_chunks(text, "Test Course", "Test Lesson")
        
        assert len(chunks) == 1
        assert chunks[0].content == text
        assert chunks[0].course_title == "Test Course"

    @pytest.mark.unit
    def test_create_chunks_empty_text(self):
        """Test creating chunks from empty text."""
        processor = DocumentProcessor()
        
        chunks = processor.create_chunks("", "Test Course", "Test Lesson")
        
        assert len(chunks) == 0


class TestSessionManager:
    """Test class for session manager."""

    @pytest.mark.unit
    def test_session_creation(self):
        """Test session creation."""
        manager = SessionManager()
        session_id = "test-session-123"
        
        # Initially no context
        context = manager.get_session_context(session_id)
        assert context == []

    @pytest.mark.unit
    def test_add_to_session(self):
        """Test adding messages to session."""
        manager = SessionManager()
        session_id = "test-session-123"
        
        # Add user message
        manager.add_to_session(session_id, "user", "Test question")
        
        # Add assistant message
        manager.add_to_session(session_id, "assistant", "Test answer")
        
        # Retrieve context
        context = manager.get_session_context(session_id)
        
        assert len(context) == 2
        assert context[0]["role"] == "user"
        assert context[0]["content"] == "Test question"
        assert context[1]["role"] == "assistant"
        assert context[1]["content"] == "Test answer"

    @pytest.mark.unit
    def test_session_isolation(self):
        """Test that sessions are isolated."""
        manager = SessionManager()
        
        # Add to first session
        manager.add_to_session("session-1", "user", "Question 1")
        
        # Add to second session
        manager.add_to_session("session-2", "user", "Question 2")
        
        # Verify isolation
        context1 = manager.get_session_context("session-1")
        context2 = manager.get_session_context("session-2")
        
        assert len(context1) == 1
        assert len(context2) == 1
        assert context1[0]["content"] == "Question 1"
        assert context2[0]["content"] == "Question 2"


@pytest.mark.slow
class TestPerformance:
    """Performance tests."""

    @pytest.mark.asyncio
    async def test_concurrent_queries(self, rag_system):
        """Test handling concurrent queries."""
        import asyncio
        
        queries = [
            rag_system.process_query(f"Query {i}", f"session-{i}")
            for i in range(5)
        ]
        
        responses = await asyncio.gather(*queries)
        
        assert len(responses) == 5
        assert all(response is not None for response in responses)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])