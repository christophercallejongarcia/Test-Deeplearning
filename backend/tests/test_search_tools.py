"""
Comprehensive tests for CourseSearchTool to identify 'query failed' issues.
"""

import pytest
from unittest.mock import Mock
from search_tools import CourseSearchTool, Tool
from vector_store import SearchResults


class TestCourseSearchTool:
    """Test the CourseSearchTool execute method comprehensively."""

    @pytest.fixture
    def mock_vector_store(self):
        """Create a mock vector store for testing."""
        mock_store = Mock()
        return mock_store

    @pytest.fixture
    def search_tool(self, mock_vector_store):
        """Create a CourseSearchTool with mock vector store."""
        return CourseSearchTool(mock_vector_store)

    def test_tool_definition(self, search_tool):
        """Test that the tool returns correct definition structure."""
        definition = search_tool.get_tool_definition()
        
        assert definition["name"] == "search_course_content"
        assert "description" in definition
        assert "input_schema" in definition
        assert definition["input_schema"]["required"] == ["query"]
        
        # Verify all expected parameters are defined
        properties = definition["input_schema"]["properties"]
        assert "query" in properties
        assert "course_name" in properties  
        assert "lesson_number" in properties

    def test_execute_successful_search(self, search_tool, mock_vector_store):
        """Test successful search execution with results."""
        # Setup mock successful search results
        mock_results = SearchResults(
            documents=["Course content about RAG systems", "Advanced retrieval techniques"],
            metadata=[
                {"course_title": "Advanced RAG", "lesson_number": 1},
                {"course_title": "Advanced RAG", "lesson_number": 2}
            ],
            distances=[0.1, 0.2],
            error=None
        )
        mock_vector_store.search.return_value = mock_results
        
        # Execute search
        result = search_tool.execute("What is RAG?")
        
        # Verify vector store was called correctly
        mock_vector_store.search.assert_called_once_with(
            query="What is RAG?",
            course_name=None,
            lesson_number=None
        )
        
        # Verify result formatting
        assert "[Advanced RAG - Lesson 1]" in result
        assert "[Advanced RAG - Lesson 2]" in result
        assert "Course content about RAG systems" in result
        assert "Advanced retrieval techniques" in result

    def test_execute_with_course_name_filter(self, search_tool, mock_vector_store):
        """Test search execution with course name filter."""
        mock_results = SearchResults(
            documents=["MCP introduction content"],
            metadata=[{"course_title": "MCP Course", "lesson_number": 1}],
            distances=[0.1],
            error=None
        )
        mock_vector_store.search.return_value = mock_results
        
        result = search_tool.execute("introduction", course_name="MCP")
        
        mock_vector_store.search.assert_called_once_with(
            query="introduction",
            course_name="MCP",
            lesson_number=None
        )
        
        assert "[MCP Course - Lesson 1]" in result

    def test_execute_with_lesson_number_filter(self, search_tool, mock_vector_store):
        """Test search execution with lesson number filter."""
        mock_results = SearchResults(
            documents=["Lesson 3 content"],
            metadata=[{"course_title": "Test Course", "lesson_number": 3}],
            distances=[0.1],
            error=None
        )
        mock_vector_store.search.return_value = mock_results
        
        result = search_tool.execute("content", lesson_number=3)
        
        mock_vector_store.search.assert_called_once_with(
            query="content",
            course_name=None, 
            lesson_number=3
        )
        
        assert "[Test Course - Lesson 3]" in result

    def test_execute_with_both_filters(self, search_tool, mock_vector_store):
        """Test search execution with both course and lesson filters."""
        mock_results = SearchResults(
            documents=["Specific lesson content"],
            metadata=[{"course_title": "Specific Course", "lesson_number": 2}],
            distances=[0.1],
            error=None
        )
        mock_vector_store.search.return_value = mock_results
        
        result = search_tool.execute("content", course_name="Specific", lesson_number=2)
        
        mock_vector_store.search.assert_called_once_with(
            query="content",
            course_name="Specific",
            lesson_number=2
        )
        
        assert "[Specific Course - Lesson 2]" in result

    def test_execute_with_search_error(self, search_tool, mock_vector_store):
        """Test handling of search errors from vector store."""
        # Setup mock error response
        mock_results = SearchResults(
            documents=[],
            metadata=[],
            distances=[],
            error="Search failed: Database connection error"
        )
        mock_vector_store.search.return_value = mock_results
        
        result = search_tool.execute("test query")
        
        # Should return the error message directly
        assert result == "Search failed: Database connection error"

    def test_execute_with_empty_results(self, search_tool, mock_vector_store):
        """Test handling of empty search results."""
        # Setup mock empty results
        mock_results = SearchResults(
            documents=[],
            metadata=[],
            distances=[],
            error=None
        )
        mock_vector_store.search.return_value = mock_results
        
        result = search_tool.execute("nonexistent content")
        
        assert result == "No relevant content found."

    def test_execute_empty_results_with_course_filter(self, search_tool, mock_vector_store):
        """Test handling of empty results with course filter."""
        mock_results = SearchResults(
            documents=[],
            metadata=[],
            distances=[],
            error=None
        )
        mock_vector_store.search.return_value = mock_results
        
        result = search_tool.execute("content", course_name="Nonexistent Course")
        
        assert "in course 'Nonexistent Course'" in result

    def test_execute_empty_results_with_lesson_filter(self, search_tool, mock_vector_store):
        """Test handling of empty results with lesson filter."""
        mock_results = SearchResults(
            documents=[],
            metadata=[],
            distances=[],
            error=None
        )
        mock_vector_store.search.return_value = mock_results
        
        result = search_tool.execute("content", lesson_number=99)
        
        assert "in lesson 99" in result

    def test_execute_empty_results_with_both_filters(self, search_tool, mock_vector_store):
        """Test handling of empty results with both filters."""
        mock_results = SearchResults(
            documents=[],
            metadata=[],
            distances=[],
            error=None
        )
        mock_vector_store.search.return_value = mock_results
        
        result = search_tool.execute("content", course_name="Test", lesson_number=5)
        
        assert "in course 'Test'" in result
        assert "in lesson 5" in result

    def test_format_results_with_missing_metadata(self, search_tool, mock_vector_store):
        """Test result formatting when metadata is missing or incomplete."""
        mock_results = SearchResults(
            documents=["Content with missing metadata", "Content with partial metadata"],
            metadata=[
                {},  # Empty metadata
                {"course_title": "Partial Course"}  # Missing lesson_number
            ],
            distances=[0.1, 0.2],
            error=None
        )
        mock_vector_store.search.return_value = mock_results
        
        result = search_tool.execute("test query")
        
        assert "[unknown]" in result
        assert "[Partial Course]" in result

    def test_source_tracking(self, search_tool, mock_vector_store):
        """Test that sources are properly tracked for UI."""
        mock_results = SearchResults(
            documents=["Test content"],
            metadata=[{"course_title": "Test Course", "lesson_number": 1}],
            distances=[0.1],
            error=None
        )
        mock_vector_store.search.return_value = mock_results
        mock_vector_store.get_lesson_link.return_value = "https://test.com/lesson1"
        
        result = search_tool.execute("test")
        
        # Check that sources were stored
        assert len(search_tool.last_sources) == 1
        source = search_tool.last_sources[0]
        assert source["display"] == "Test Course - Lesson 1"
        assert source["link"] == "https://test.com/lesson1"

    def test_source_tracking_without_link(self, search_tool, mock_vector_store):
        """Test source tracking when no lesson link is available."""
        mock_results = SearchResults(
            documents=["Test content"],
            metadata=[{"course_title": "Test Course", "lesson_number": 1}],
            distances=[0.1],
            error=None
        )
        mock_vector_store.search.return_value = mock_results
        mock_vector_store.get_lesson_link.return_value = None
        
        result = search_tool.execute("test")
        
        assert len(search_tool.last_sources) == 1
        source = search_tool.last_sources[0]
        assert source["link"] is None

    def test_vector_store_exception_handling(self, search_tool, mock_vector_store):
        """Test handling of unexpected exceptions from vector store."""
        # Make the vector store raise an exception
        mock_vector_store.search.side_effect = Exception("Unexpected database error")
        
        # The search should not crash, but return an error message
        # This tests if CourseSearchTool properly handles exceptions
        result = search_tool.execute("test query")
        
        # The behavior depends on implementation - either the exception propagates
        # or it's caught and converted to an error message
        # This test will help identify the actual behavior
        assert isinstance(result, str)  # Should return some string response


class TestToolInterface:
    """Test that CourseSearchTool properly implements the Tool interface."""
    
    def test_implements_tool_interface(self):
        """Test that CourseSearchTool implements the Tool ABC properly."""
        mock_vector_store = Mock()
        tool = CourseSearchTool(mock_vector_store)
        
        # Should be able to instantiate without errors
        assert isinstance(tool, Tool)
        
        # Should have required methods
        assert hasattr(tool, 'get_tool_definition')
        assert hasattr(tool, 'execute')
        assert callable(tool.get_tool_definition)
        assert callable(tool.execute)


if __name__ == "__main__":
    pytest.main([__file__])