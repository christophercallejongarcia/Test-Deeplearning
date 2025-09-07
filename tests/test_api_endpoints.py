"""
Comprehensive API endpoint tests for the RAG chatbot application.
"""

import pytest
import httpx
from fastapi.testclient import TestClient
from backend.app import app
from backend.models import QueryRequest
import json


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_query():
    """Sample query for testing."""
    return {
        "message": "What is the outline of the MCP course?",
        "session_id": "test-session-123"
    }


class TestAPIEndpoints:
    """Test class for API endpoints."""

    @pytest.mark.api
    def test_health_check(self, client: TestClient):
        """Test health check endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        assert "Course Materials Assistant" in response.text

    @pytest.mark.api
    def test_query_endpoint_valid_request(self, client: TestClient, sample_query):
        """Test query endpoint with valid request."""
        response = client.post("/api/query", json=sample_query)
        assert response.status_code == 200
        
        data = response.json()
        assert "response" in data
        assert "session_id" in data
        assert data["session_id"] == sample_query["session_id"]

    @pytest.mark.api
    def test_query_endpoint_missing_message(self, client: TestClient):
        """Test query endpoint with missing message."""
        response = client.post("/api/query", json={"session_id": "test"})
        assert response.status_code == 422  # Validation error

    @pytest.mark.api
    def test_query_endpoint_empty_message(self, client: TestClient):
        """Test query endpoint with empty message."""
        response = client.post("/api/query", json={
            "message": "",
            "session_id": "test"
        })
        assert response.status_code == 400

    @pytest.mark.api
    def test_courses_endpoint(self, client: TestClient):
        """Test courses endpoint."""
        response = client.get("/api/courses")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_courses" in data
        assert "courses" in data
        assert isinstance(data["courses"], list)

    @pytest.mark.api  
    def test_detailed_courses_endpoint(self, client: TestClient):
        """Test detailed courses endpoint."""
        response = client.get("/api/courses/detailed")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_courses" in data
        assert "courses" in data
        assert isinstance(data["courses"], list)
        
        # Check course structure if courses exist
        if data["courses"]:
            course = data["courses"][0]
            assert "title" in course
            assert "lessons" in course

    @pytest.mark.api
    def test_cors_headers(self, client: TestClient):
        """Test CORS headers are present."""
        response = client.options("/api/query")
        assert response.status_code == 200
        
        # Check common CORS headers
        headers = response.headers
        assert "access-control-allow-origin" in headers or "Access-Control-Allow-Origin" in headers

    @pytest.mark.api
    @pytest.mark.slow
    def test_query_endpoint_long_message(self, client: TestClient):
        """Test query endpoint with very long message."""
        long_message = "What is the course about? " * 100
        response = client.post("/api/query", json={
            "message": long_message,
            "session_id": "test-long"
        })
        # Should handle long messages gracefully
        assert response.status_code in [200, 413]  # OK or Request Entity Too Large

    @pytest.mark.api
    def test_static_files_served(self, client: TestClient):
        """Test that static files are served."""
        # Test main HTML file
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    @pytest.mark.integration
    def test_session_persistence(self, client: TestClient):
        """Test that session context is maintained."""
        session_id = "persistence-test-123"
        
        # First query
        response1 = client.post("/api/query", json={
            "message": "What is the MCP course about?",
            "session_id": session_id
        })
        assert response1.status_code == 200
        
        # Follow-up query that requires context
        response2 = client.post("/api/query", json={
            "message": "What are the main topics covered in it?",
            "session_id": session_id
        })
        assert response2.status_code == 200
        
        # Responses should be contextual
        data1 = response1.json()
        data2 = response2.json()
        assert data1["session_id"] == data2["session_id"]


@pytest.mark.e2e
class TestEndToEndScenarios:
    """End-to-end test scenarios."""

    def test_complete_user_journey(self, client: TestClient):
        """Test complete user interaction flow."""
        session_id = "e2e-test-456"
        
        # 1. Get courses list
        courses_response = client.get("/api/courses/detailed")
        assert courses_response.status_code == 200
        courses_data = courses_response.json()
        
        # 2. Ask about a specific course
        if courses_data["courses"]:
            course_title = courses_data["courses"][0]["title"]
            query_response = client.post("/api/query", json={
                "message": f"Tell me about the {course_title} course",
                "session_id": session_id
            })
            assert query_response.status_code == 200
            
            # 3. Follow up with specific question
            followup_response = client.post("/api/query", json={
                "message": "What are the learning objectives?",
                "session_id": session_id
            })
            assert followup_response.status_code == 200

    def test_error_handling_flow(self, client: TestClient):
        """Test error handling scenarios."""
        # Invalid JSON
        response = client.post("/api/query", 
                             data="invalid json",
                             headers={"content-type": "application/json"})
        assert response.status_code == 422

        # Missing required fields
        response = client.post("/api/query", json={})
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])