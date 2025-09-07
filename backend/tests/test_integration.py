"""
Integration tests for the complete RAG system to identify end-to-end failures.
"""

import pytest
import tempfile
import shutil
import os
from unittest.mock import Mock, MagicMock, patch
from rag_system import RAGSystem
from config import Config
from models import Course, Lesson, CourseChunk


class TestRAGSystemIntegration:
    """Integration tests for the complete RAG system."""

    @pytest.fixture
    def temp_config(self):
        """Create a temporary config for testing."""
        temp_dir = tempfile.mkdtemp()
        
        config = Config()
        config.CHROMA_PATH = os.path.join(temp_dir, "test_chroma")
        config.ANTHROPIC_API_KEY = "test-key-123"
        config.CHUNK_SIZE = 500
        config.CHUNK_OVERLAP = 50
        config.MAX_RESULTS = 3
        
        yield config
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_rag_system(self, temp_config):
        """Create a RAG system with mocked external dependencies."""
        with patch('rag_system.AIGenerator') as mock_ai_gen, \
             patch('rag_system.VectorStore') as mock_vector_store, \
             patch('rag_system.DocumentProcessor') as mock_doc_processor:
            
            # Setup mocks
            mock_ai_gen_instance = Mock()
            mock_ai_gen.return_value = mock_ai_gen_instance
            
            mock_vector_store_instance = Mock()
            mock_vector_store.return_value = mock_vector_store_instance
            
            mock_doc_processor_instance = Mock()
            mock_doc_processor.return_value = mock_doc_processor_instance
            
            rag_system = RAGSystem(temp_config)
            
            yield rag_system, mock_ai_gen_instance, mock_vector_store_instance, mock_doc_processor_instance

    def test_rag_system_initialization(self, temp_config):
        """Test that RAG system initializes all components correctly."""
        with patch('rag_system.AIGenerator'), \
             patch('rag_system.VectorStore'), \
             patch('rag_system.DocumentProcessor'):
            
            rag_system = RAGSystem(temp_config)
            
            # Check that all components are initialized
            assert rag_system.config == temp_config
            assert rag_system.document_processor is not None
            assert rag_system.vector_store is not None
            assert rag_system.ai_generator is not None
            assert rag_system.session_manager is not None
            assert rag_system.tool_manager is not None
            
            # Check that tools are registered
            tool_definitions = rag_system.tool_manager.get_tool_definitions()
            assert len(tool_definitions) == 2  # CourseSearchTool and CourseOutlineTool
            
            tool_names = [tool['name'] for tool in tool_definitions]
            assert 'search_course_content' in tool_names
            assert 'get_course_outline' in tool_names

    def test_query_successful_with_tool_use(self, mock_rag_system):
        """Test successful query processing with tool use."""
        rag_system, mock_ai_gen, mock_vector_store, mock_doc_processor = mock_rag_system
        
        # Mock AI generator response with tool use
        mock_ai_gen.generate_response.return_value = "Here's the course content you requested..."
        
        # Mock tool manager to return sources
        rag_system.tool_manager.get_last_sources = Mock(return_value=[
            {"display": "Test Course - Lesson 1", "link": "https://test.com"}
        ])
        rag_system.tool_manager.reset_sources = Mock()
        
        # Mock session manager
        rag_system.session_manager.get_conversation_history = Mock(return_value=None)
        rag_system.session_manager.add_exchange = Mock()
        
        # Execute query
        response, sources = rag_system.query("What is covered in lesson 1?", session_id="test-session")
        
        # Verify AI generator was called with correct parameters
        mock_ai_gen.generate_response.assert_called_once()
        call_args = mock_ai_gen.generate_response.call_args
        
        assert "What is covered in lesson 1?" in call_args[1]['query']
        assert call_args[1]['tools'] == rag_system.tool_manager.get_tool_definitions()
        assert call_args[1]['tool_manager'] == rag_system.tool_manager
        
        # Verify response
        assert response == "Here's the course content you requested..."
        assert len(sources) == 1
        assert sources[0]["display"] == "Test Course - Lesson 1"
        
        # Verify session management
        rag_system.session_manager.add_exchange.assert_called_once_with(
            "test-session", "What is covered in lesson 1?", response
        )

    def test_query_without_session(self, mock_rag_system):
        """Test query processing without session ID."""
        rag_system, mock_ai_gen, mock_vector_store, mock_doc_processor = mock_rag_system
        
        mock_ai_gen.generate_response.return_value = "General response"
        rag_system.tool_manager.get_last_sources = Mock(return_value=[])
        rag_system.tool_manager.reset_sources = Mock()
        
        response, sources = rag_system.query("What is AI?")
        
        # Should not try to get or update conversation history
        rag_system.session_manager.get_conversation_history.assert_not_called()
        rag_system.session_manager.add_exchange.assert_not_called()
        
        assert response == "General response"
        assert sources == []

    def test_query_with_conversation_history(self, mock_rag_system):
        """Test query processing with existing conversation history."""
        rag_system, mock_ai_gen, mock_vector_store, mock_doc_processor = mock_rag_system
        
        # Mock conversation history
        mock_history = "Previous: User asked about RAG. Assistant: RAG stands for..."
        rag_system.session_manager.get_conversation_history = Mock(return_value=mock_history)
        rag_system.session_manager.add_exchange = Mock()
        
        mock_ai_gen.generate_response.return_value = "Follow-up response"
        rag_system.tool_manager.get_last_sources = Mock(return_value=[])
        rag_system.tool_manager.reset_sources = Mock()
        
        response, sources = rag_system.query("Tell me more", session_id="test-session")
        
        # Verify history was passed to AI generator
        call_args = mock_ai_gen.generate_response.call_args[1]
        assert call_args['conversation_history'] == mock_history

    def test_query_ai_generator_failure(self, mock_rag_system):
        """Test handling of AI generator failures."""
        rag_system, mock_ai_gen, mock_vector_store, mock_doc_processor = mock_rag_system
        
        # Make AI generator raise an exception
        mock_ai_gen.generate_response.side_effect = Exception("API rate limit exceeded")
        
        # Should propagate exception or handle gracefully
        with pytest.raises(Exception) as exc_info:
            rag_system.query("test query")
        
        assert "API rate limit exceeded" in str(exc_info.value)

    def test_add_course_document_success(self, mock_rag_system):
        """Test successful course document processing."""
        rag_system, mock_ai_gen, mock_vector_store, mock_doc_processor = mock_rag_system
        
        # Mock document processing
        test_course = Course(
            title="Test Course",
            instructor="Test Instructor",
            lessons=[Lesson(lesson_number=1, title="Introduction")]
        )
        test_chunks = [
            CourseChunk(content="Chunk 1", course_title="Test Course", chunk_index=0),
            CourseChunk(content="Chunk 2", course_title="Test Course", chunk_index=1)
        ]
        
        mock_doc_processor.process_course_document.return_value = (test_course, test_chunks)
        
        # Execute
        course, chunk_count = rag_system.add_course_document("/fake/path/course.txt")
        
        # Verify document processor was called
        mock_doc_processor.process_course_document.assert_called_once_with("/fake/path/course.txt")
        
        # Verify vector store operations
        mock_vector_store.add_course_metadata.assert_called_once_with(test_course)
        mock_vector_store.add_course_content.assert_called_once_with(test_chunks)
        
        # Verify return values
        assert course == test_course
        assert chunk_count == 2

    def test_add_course_document_processing_error(self, mock_rag_system):
        """Test handling of document processing errors."""
        rag_system, mock_ai_gen, mock_vector_store, mock_doc_processor = mock_rag_system
        
        # Make document processor raise an exception
        mock_doc_processor.process_course_document.side_effect = Exception("File not found")
        
        course, chunk_count = rag_system.add_course_document("/fake/path/missing.txt")
        
        # Should handle error gracefully
        assert course is None
        assert chunk_count == 0
        
        # Vector store should not be called
        mock_vector_store.add_course_metadata.assert_not_called()
        mock_vector_store.add_course_content.assert_not_called()

    def test_add_course_folder_with_existing_courses(self, mock_rag_system):
        """Test adding course folder with some existing courses."""
        rag_system, mock_ai_gen, mock_vector_store, mock_doc_processor = mock_rag_system
        
        # Mock existing courses in vector store
        mock_vector_store.get_existing_course_titles.return_value = ["Existing Course"]
        
        # Mock document processing for multiple files
        test_course_1 = Course(title="New Course", instructor="Teacher 1")
        test_course_2 = Course(title="Existing Course", instructor="Teacher 2")
        
        mock_doc_processor.process_course_document.side_effect = [
            (test_course_1, [CourseChunk(content="New content", course_title="New Course", chunk_index=0)]),
            (test_course_2, [CourseChunk(content="Existing content", course_title="Existing Course", chunk_index=0)])
        ]
        
        # Mock folder contents
        with patch('os.path.exists') as mock_exists, \
             patch('os.listdir') as mock_listdir, \
             patch('os.path.isfile') as mock_isfile:
            
            mock_exists.return_value = True
            mock_listdir.return_value = ["new_course.txt", "existing_course.txt"]
            mock_isfile.return_value = True
            
            total_courses, total_chunks = rag_system.add_course_folder("/fake/docs")
        
        # Should only add new course
        assert total_courses == 1
        assert total_chunks == 1
        
        # Vector store should be called only for new course
        mock_vector_store.add_course_metadata.assert_called_once_with(test_course_1)
        mock_vector_store.add_course_content.assert_called_once()

    def test_add_course_folder_clear_existing(self, mock_rag_system):
        """Test adding course folder with clear_existing=True."""
        rag_system, mock_ai_gen, mock_vector_store, mock_doc_processor = mock_rag_system
        
        with patch('os.path.exists') as mock_exists, \
             patch('os.listdir') as mock_listdir, \
             patch('os.path.isfile') as mock_isfile:
            
            mock_exists.return_value = True
            mock_listdir.return_value = []  # Empty folder
            mock_isfile.return_value = True
            
            total_courses, total_chunks = rag_system.add_course_folder(
                "/fake/docs", 
                clear_existing=True
            )
        
        # Should clear existing data
        mock_vector_store.clear_all_data.assert_called_once()

    def test_get_course_analytics(self, mock_rag_system):
        """Test getting course analytics."""
        rag_system, mock_ai_gen, mock_vector_store, mock_doc_processor = mock_rag_system
        
        mock_vector_store.get_course_count.return_value = 5
        mock_vector_store.get_existing_course_titles.return_value = [
            "Course 1", "Course 2", "Course 3", "Course 4", "Course 5"
        ]
        
        analytics = rag_system.get_course_analytics()
        
        assert analytics["total_courses"] == 5
        assert len(analytics["course_titles"]) == 5

    def test_get_detailed_course_analytics(self, mock_rag_system):
        """Test getting detailed course analytics."""
        rag_system, mock_ai_gen, mock_vector_store, mock_doc_processor = mock_rag_system
        
        mock_metadata = [
            {
                "title": "Course 1",
                "instructor": "Teacher 1",
                "lesson_count": 10,
                "course_link": "https://course1.com"
            },
            {
                "title": "Course 2",
                "instructor": "Teacher 2",
                "lesson_count": 5,
                "course_link": None
            }
        ]
        
        mock_vector_store.get_all_courses_metadata.return_value = mock_metadata
        
        detailed_analytics = rag_system.get_detailed_course_analytics()
        
        assert detailed_analytics["total_courses"] == 2
        assert len(detailed_analytics["courses"]) == 2
        assert detailed_analytics["courses"][0]["title"] == "Course 1"
        assert detailed_analytics["courses"][0]["instructor"] == "Teacher 1"


class TestRAGSystemRealIntegration:
    """Integration tests with real components (but isolated data)."""

    @pytest.fixture
    def real_temp_config(self):
        """Create a temporary config for real integration testing."""
        temp_dir = tempfile.mkdtemp()
        
        config = Config()
        config.CHROMA_PATH = os.path.join(temp_dir, "real_test_chroma")
        config.ANTHROPIC_API_KEY = "test-key-123"  # Will be mocked
        config.EMBEDDING_MODEL = "all-MiniLM-L6-v2"
        config.CHUNK_SIZE = 200
        config.CHUNK_OVERLAP = 20
        config.MAX_RESULTS = 2
        
        yield config
        shutil.rmtree(temp_dir)

    def test_real_document_processing_and_storage(self, real_temp_config):
        """Test real document processing and vector storage."""
        # Mock only the AI generator to avoid API calls
        with patch('rag_system.AIGenerator') as mock_ai_gen:
            mock_ai_gen_instance = Mock()
            mock_ai_gen_instance.generate_response.return_value = "Test response"
            mock_ai_gen.return_value = mock_ai_gen_instance
            
            rag_system = RAGSystem(real_temp_config)
            
            # Create a test document
            test_doc_content = """Course Title: Test Integration Course
Course Link: https://test.com
Course Instructor: Test Teacher

Lesson 1: Introduction
This is the introduction lesson content. It covers basic concepts.

Lesson 2: Advanced Topics  
This lesson covers advanced topics in detail. More complex material here."""
            
            # Write to temporary file
            temp_doc = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
            temp_doc.write(test_doc_content)
            temp_doc.close()
            
            try:
                # Process the document
                course, chunk_count = rag_system.add_course_document(temp_doc.name)
                
                # Verify processing worked
                assert course is not None
                assert course.title == "Test Integration Course"
                assert course.instructor == "Test Teacher"
                assert len(course.lessons) == 2
                assert chunk_count > 0
                
                # Verify data was stored in vector store
                analytics = rag_system.get_course_analytics()
                assert analytics["total_courses"] == 1
                assert "Test Integration Course" in analytics["course_titles"]
                
                # Test query (with mocked AI response)
                rag_system.tool_manager.get_last_sources = Mock(return_value=[])
                rag_system.tool_manager.reset_sources = Mock()
                
                response, sources = rag_system.query("What is covered in lesson 1?")
                
                # AI generator should have been called with tools
                mock_ai_gen_instance.generate_response.assert_called()
                call_args = mock_ai_gen_instance.generate_response.call_args[1]
                assert 'tools' in call_args
                assert 'tool_manager' in call_args
                
            finally:
                os.unlink(temp_doc.name)

    def test_empty_query_handling(self, real_temp_config):
        """Test handling of queries when no data is loaded."""
        with patch('rag_system.AIGenerator') as mock_ai_gen:
            mock_ai_gen_instance = Mock()
            mock_ai_gen_instance.generate_response.return_value = "I don't have information about that."
            mock_ai_gen.return_value = mock_ai_gen_instance
            
            rag_system = RAGSystem(real_temp_config)
            
            # Mock tool manager
            rag_system.tool_manager.get_last_sources = Mock(return_value=[])
            rag_system.tool_manager.reset_sources = Mock()
            
            # Query with no data loaded
            response, sources = rag_system.query("What courses are available?")
            
            assert response == "I don't have information about that."
            assert sources == []


if __name__ == "__main__":
    pytest.main([__file__])