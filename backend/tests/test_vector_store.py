"""
Comprehensive tests for VectorStore to identify ChromaDB and search issues.
"""

import pytest
import tempfile
import shutil
from unittest.mock import Mock, MagicMock, patch
from vector_store import VectorStore, SearchResults
from models import Course, Lesson, CourseChunk


class TestSearchResults:
    """Test the SearchResults dataclass functionality."""
    
    def test_from_chroma_with_results(self):
        """Test creating SearchResults from ChromaDB results."""
        chroma_results = {
            'documents': [['doc1', 'doc2']],
            'metadatas': [[{'course': 'test'}, {'course': 'test2'}]],
            'distances': [[0.1, 0.2]]
        }
        
        results = SearchResults.from_chroma(chroma_results)
        
        assert results.documents == ['doc1', 'doc2']
        assert results.metadata == [{'course': 'test'}, {'course': 'test2'}]
        assert results.distances == [0.1, 0.2]
        assert results.error is None

    def test_from_chroma_empty_results(self):
        """Test creating SearchResults from empty ChromaDB results."""
        chroma_results = {
            'documents': [[]],
            'metadatas': [[]],
            'distances': [[]]
        }
        
        results = SearchResults.from_chroma(chroma_results)
        
        assert results.documents == []
        assert results.metadata == []
        assert results.distances == []
        assert results.error is None

    def test_empty_with_error(self):
        """Test creating empty SearchResults with error message."""
        results = SearchResults.empty("Test error message")
        
        assert results.documents == []
        assert results.metadata == []
        assert results.distances == []
        assert results.error == "Test error message"

    def test_is_empty(self):
        """Test is_empty method."""
        empty_results = SearchResults([], [], [])
        non_empty_results = SearchResults(['doc'], [{}], [0.1])
        
        assert empty_results.is_empty()
        assert not non_empty_results.is_empty()


class TestVectorStore:
    """Test the VectorStore functionality comprehensively."""

    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary directory for test ChromaDB."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def vector_store(self, temp_db_path):
        """Create a VectorStore instance for testing."""
        return VectorStore(
            chroma_path=temp_db_path,
            embedding_model="all-MiniLM-L6-v2",
            max_results=5
        )

    @pytest.fixture
    def mock_vector_store(self):
        """Create a VectorStore with mocked ChromaDB."""
        with patch('vector_store.chromadb') as mock_chromadb:
            mock_client = Mock()
            mock_chromadb.PersistentClient.return_value = mock_client
            
            mock_course_catalog = Mock()
            mock_course_content = Mock()
            mock_client.get_or_create_collection.side_effect = [
                mock_course_catalog, mock_course_content
            ]
            
            store = VectorStore("test_path", "test-model", max_results=3)
            store.course_catalog = mock_course_catalog
            store.course_content = mock_course_content
            
            yield store, mock_course_catalog, mock_course_content

    def test_initialization(self, temp_db_path):
        """Test VectorStore initialization."""
        store = VectorStore(temp_db_path, "all-MiniLM-L6-v2", max_results=10)
        
        assert store.max_results == 10
        assert store.client is not None
        assert store.course_catalog is not None
        assert store.course_content is not None

    def test_search_without_filters(self, mock_vector_store):
        """Test basic search without course or lesson filters."""
        store, mock_catalog, mock_content = mock_vector_store
        
        # Mock successful search
        mock_content.query.return_value = {
            'documents': [['Test document']],
            'metadatas': [[{'course_title': 'Test Course'}]],
            'distances': [[0.1]]
        }
        
        results = store.search("test query")
        
        mock_content.query.assert_called_once_with(
            query_texts=["test query"],
            n_results=3,
            where=None
        )
        
        assert len(results.documents) == 1
        assert results.documents[0] == "Test document"
        assert results.error is None

    def test_search_with_course_name_resolved(self, mock_vector_store):
        """Test search with course name that gets resolved."""
        store, mock_catalog, mock_content = mock_vector_store
        
        # Mock course name resolution
        mock_catalog.query.return_value = {
            'documents': [['course doc']],
            'metadatas': [[{'title': 'Resolved Course Title'}]]
        }
        
        # Mock content search
        mock_content.query.return_value = {
            'documents': [['Content from resolved course']],
            'metadatas': [[{'course_title': 'Resolved Course Title'}]],
            'distances': [[0.1]]
        }
        
        results = store.search("query", course_name="partial name")
        
        # Should first resolve course name
        mock_catalog.query.assert_called_once_with(
            query_texts=["partial name"],
            n_results=1
        )
        
        # Then search content with resolved name
        mock_content.query.assert_called_once_with(
            query_texts=["query"],
            n_results=3,
            where={"course_title": "Resolved Course Title"}
        )

    def test_search_with_course_name_not_found(self, mock_vector_store):
        """Test search when course name cannot be resolved."""
        store, mock_catalog, mock_content = mock_vector_store
        
        # Mock failed course resolution
        mock_catalog.query.return_value = {
            'documents': [[]],
            'metadatas': [[]]
        }
        
        results = store.search("query", course_name="nonexistent course")
        
        assert results.error == "No course found matching 'nonexistent course'"
        mock_content.query.assert_not_called()

    def test_search_with_lesson_number(self, mock_vector_store):
        """Test search with lesson number filter."""
        store, mock_catalog, mock_content = mock_vector_store
        
        mock_content.query.return_value = {
            'documents': [['Lesson content']],
            'metadatas': [[{'lesson_number': 5}]],
            'distances': [[0.1]]
        }
        
        results = store.search("query", lesson_number=5)
        
        mock_content.query.assert_called_once_with(
            query_texts=["query"],
            n_results=3,
            where={"lesson_number": 5}
        )

    def test_search_with_both_filters(self, mock_vector_store):
        """Test search with both course name and lesson number filters."""
        store, mock_catalog, mock_content = mock_vector_store
        
        # Mock course resolution
        mock_catalog.query.return_value = {
            'documents': [['course']],
            'metadatas': [[{'title': 'Test Course'}]]
        }
        
        mock_content.query.return_value = {
            'documents': [['Specific content']],
            'metadatas': [[{'course_title': 'Test Course', 'lesson_number': 3}]],
            'distances': [[0.1]]
        }
        
        results = store.search("query", course_name="Test", lesson_number=3)
        
        expected_filter = {"$and": [
            {"course_title": "Test Course"},
            {"lesson_number": 3}
        ]}
        
        mock_content.query.assert_called_once_with(
            query_texts=["query"],
            n_results=3,
            where=expected_filter
        )

    def test_search_chromadb_exception(self, mock_vector_store):
        """Test handling of ChromaDB exceptions during search."""
        store, mock_catalog, mock_content = mock_vector_store
        
        # Make ChromaDB query raise an exception
        mock_content.query.side_effect = Exception("ChromaDB connection failed")
        
        results = store.search("query")
        
        assert results.error == "Search error: ChromaDB connection failed"
        assert results.is_empty()

    def test_resolve_course_name_successful(self, mock_vector_store):
        """Test successful course name resolution."""
        store, mock_catalog, mock_content = mock_vector_store
        
        mock_catalog.query.return_value = {
            'documents': [['matching course']],
            'metadatas': [[{'title': 'Full Course Title'}]]
        }
        
        result = store._resolve_course_name("partial")
        
        assert result == "Full Course Title"
        mock_catalog.query.assert_called_once_with(
            query_texts=["partial"],
            n_results=1
        )

    def test_resolve_course_name_no_results(self, mock_vector_store):
        """Test course name resolution with no results."""
        store, mock_catalog, mock_content = mock_vector_store
        
        mock_catalog.query.return_value = {
            'documents': [[]],
            'metadatas': [[]]
        }
        
        result = store._resolve_course_name("nonexistent")
        
        assert result is None

    def test_resolve_course_name_exception(self, mock_vector_store):
        """Test course name resolution with exception."""
        store, mock_catalog, mock_content = mock_vector_store
        
        mock_catalog.query.side_effect = Exception("Query failed")
        
        result = store._resolve_course_name("test")
        
        assert result is None

    def test_build_filter_no_params(self, mock_vector_store):
        """Test filter building with no parameters."""
        store, _, _ = mock_vector_store
        
        filter_dict = store._build_filter(None, None)
        
        assert filter_dict is None

    def test_build_filter_course_only(self, mock_vector_store):
        """Test filter building with course title only."""
        store, _, _ = mock_vector_store
        
        filter_dict = store._build_filter("Test Course", None)
        
        assert filter_dict == {"course_title": "Test Course"}

    def test_build_filter_lesson_only(self, mock_vector_store):
        """Test filter building with lesson number only."""
        store, _, _ = mock_vector_store
        
        filter_dict = store._build_filter(None, 5)
        
        assert filter_dict == {"lesson_number": 5}

    def test_build_filter_both_params(self, mock_vector_store):
        """Test filter building with both parameters."""
        store, _, _ = mock_vector_store
        
        filter_dict = store._build_filter("Test Course", 3)
        
        expected = {"$and": [
            {"course_title": "Test Course"},
            {"lesson_number": 3}
        ]}
        assert filter_dict == expected

    def test_add_course_metadata(self, mock_vector_store):
        """Test adding course metadata to catalog."""
        store, mock_catalog, mock_content = mock_vector_store
        
        # Create test course
        course = Course(
            title="Test Course",
            course_link="https://test.com",
            instructor="Test Instructor",
            lessons=[
                Lesson(lesson_number=1, title="Lesson 1", lesson_link="https://test.com/1"),
                Lesson(lesson_number=2, title="Lesson 2", lesson_link="https://test.com/2")
            ]
        )
        
        store.add_course_metadata(course)
        
        # Verify catalog.add was called with correct parameters
        mock_catalog.add.assert_called_once()
        call_args = mock_catalog.add.call_args
        
        assert call_args[1]['documents'] == ["Test Course"]
        assert call_args[1]['ids'] == ["Test Course"]
        
        metadata = call_args[1]['metadatas'][0]
        assert metadata['title'] == "Test Course"
        assert metadata['instructor'] == "Test Instructor"
        assert metadata['course_link'] == "https://test.com"
        assert metadata['lesson_count'] == 2
        
        # Verify lessons are serialized as JSON
        import json
        lessons = json.loads(metadata['lessons_json'])
        assert len(lessons) == 2
        assert lessons[0]['lesson_number'] == 1
        assert lessons[0]['lesson_title'] == "Lesson 1"

    def test_add_course_content(self, mock_vector_store):
        """Test adding course content chunks."""
        store, mock_catalog, mock_content = mock_vector_store
        
        chunks = [
            CourseChunk(
                content="First chunk content",
                course_title="Test Course",
                lesson_number=1,
                chunk_index=0
            ),
            CourseChunk(
                content="Second chunk content", 
                course_title="Test Course",
                lesson_number=1,
                chunk_index=1
            )
        ]
        
        store.add_course_content(chunks)
        
        mock_content.add.assert_called_once()
        call_args = mock_content.add.call_args
        
        assert len(call_args[1]['documents']) == 2
        assert call_args[1]['documents'][0] == "First chunk content"
        assert call_args[1]['documents'][1] == "Second chunk content"
        
        assert call_args[1]['ids'] == ["Test_Course_0", "Test_Course_1"]

    def test_add_course_content_empty_list(self, mock_vector_store):
        """Test adding empty course content list."""
        store, mock_catalog, mock_content = mock_vector_store
        
        store.add_course_content([])
        
        mock_content.add.assert_not_called()

    def test_get_existing_course_titles(self, mock_vector_store):
        """Test getting existing course titles."""
        store, mock_catalog, mock_content = mock_vector_store
        
        mock_catalog.get.return_value = {
            'ids': ['Course 1', 'Course 2', 'Course 3']
        }
        
        titles = store.get_existing_course_titles()
        
        assert titles == ['Course 1', 'Course 2', 'Course 3']

    def test_get_existing_course_titles_exception(self, mock_vector_store):
        """Test getting course titles with exception."""
        store, mock_catalog, mock_content = mock_vector_store
        
        mock_catalog.get.side_effect = Exception("Database error")
        
        titles = store.get_existing_course_titles()
        
        assert titles == []

    def test_search_with_custom_limit(self, mock_vector_store):
        """Test search with custom result limit."""
        store, mock_catalog, mock_content = mock_vector_store
        
        mock_content.query.return_value = {
            'documents': [['doc1', 'doc2']],
            'metadatas': [[{}, {}]],
            'distances': [[0.1, 0.2]]
        }
        
        results = store.search("query", limit=10)
        
        mock_content.query.assert_called_once_with(
            query_texts=["query"],
            n_results=10,  # Should use custom limit instead of default
            where=None
        )


if __name__ == "__main__":
    pytest.main([__file__])