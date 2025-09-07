"""
Shared pytest configuration and fixtures for RAG system tests.
"""

import pytest
import tempfile
import shutil
import os
from unittest.mock import Mock
from config import Config


@pytest.fixture
def temp_test_dir():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_config(temp_test_dir):
    """Create a test configuration with temporary paths."""
    config = Config()
    config.CHROMA_PATH = os.path.join(temp_test_dir, "test_chroma")
    config.ANTHROPIC_API_KEY = "test-api-key-123"
    config.ANTHROPIC_MODEL = "claude-sonnet-4-20250514"
    config.EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    config.CHUNK_SIZE = 300
    config.CHUNK_OVERLAP = 50
    config.MAX_RESULTS = 3
    config.MAX_HISTORY = 2
    return config


@pytest.fixture
def sample_course_data():
    """Sample course data for testing."""
    return {
        "course_title": "Test RAG Course",
        "instructor": "Test Instructor",
        "course_link": "https://test.com/course",
        "lessons": [
            {
                "lesson_number": 1,
                "title": "Introduction to RAG",
                "content": "RAG stands for Retrieval-Augmented Generation. It combines retrieval with generation."
            },
            {
                "lesson_number": 2,
                "title": "Vector Databases",
                "content": "Vector databases store embeddings for semantic search. ChromaDB is an example."
            }
        ]
    }


@pytest.fixture
def sample_document_content():
    """Sample document content in expected format."""
    return """Course Title: Building Towards Computer Use with Anthropic
Course Link: https://www.deeplearning.ai/short-courses/building-toward-computer-use-with-anthropic/
Course Instructor: Colt Steele

Lesson 1: Introduction
Welcome to Building Toward Computer Use with Anthropic. This course covers the fundamentals.

Lesson 2: Multi-modal Requests  
In this lesson you'll learn about processing images and other media types with Claude.

Lesson 3: Tool Usage
This lesson focuses on using tools effectively with Claude's API.
"""


@pytest.fixture
def mock_anthropic_response():
    """Mock response from Anthropic API."""
    mock_response = Mock()
    mock_response.stop_reason = "end_turn"
    mock_response.content = [Mock(text="This is a test response from Claude.")]
    return mock_response


@pytest.fixture
def mock_tool_use_response():
    """Mock tool use response from Anthropic API."""
    mock_tool_use = Mock()
    mock_tool_use.type = "tool_use"
    mock_tool_use.name = "search_course_content"
    mock_tool_use.id = "tool_123"
    mock_tool_use.input = {"query": "test query"}
    
    mock_response = Mock()
    mock_response.stop_reason = "tool_use"
    mock_response.content = [mock_tool_use]
    return mock_response