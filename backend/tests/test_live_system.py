"""
Live system diagnostic tests to reproduce the 'query failed' issue.
"""

import pytest
import requests
import os


@pytest.mark.skipif(
    not os.environ.get("TEST_LIVE_SYSTEM"), 
    reason="Set TEST_LIVE_SYSTEM=1 to run live system tests"
)
class TestLiveSystem:
    """Test the live running system to reproduce issues."""
    
    BASE_URL = "http://127.0.0.1:8000"
    
    def test_api_health(self):
        """Test that the API is responding."""
        try:
            response = requests.get(f"{self.BASE_URL}/api/courses")
            assert response.status_code == 200
            data = response.json()
            print(f"System has {data['total_courses']} courses loaded")
        except requests.exceptions.ConnectionError:
            pytest.skip("Live system not running on localhost:8000")
    
    def test_query_general_question(self):
        """Test a general question that shouldn't need course search."""
        try:
            response = requests.post(f"{self.BASE_URL}/api/query", json={
                "query": "What is 2+2?"
            })
            assert response.status_code == 200
            data = response.json()
            print(f"General question response: {data['answer']}")
            assert "4" in data["answer"] or "four" in data["answer"].lower()
        except requests.exceptions.ConnectionError:
            pytest.skip("Live system not running on localhost:8000")
    
    def test_query_course_content_question(self):
        """Test a course content question that should trigger search."""
        try:
            response = requests.post(f"{self.BASE_URL}/api/query", json={
                "query": "What is covered in the MCP course?"
            })
            assert response.status_code == 200
            data = response.json()
            print(f"Course content response: {data['answer']}")
            print(f"Sources returned: {len(data['sources'])}")
            
            # This should not be 'query failed'
            assert "query failed" not in data["answer"].lower()
            
        except requests.exceptions.ConnectionError:
            pytest.skip("Live system not running on localhost:8000")
    
    def test_query_course_outline_question(self):
        """Test a course outline question."""
        try:
            response = requests.post(f"{self.BASE_URL}/api/query", json={
                "query": "Show me the outline of the Computer Use course"
            })
            assert response.status_code == 200
            data = response.json()
            print(f"Course outline response: {data['answer']}")
            print(f"Sources returned: {len(data['sources'])}")
            
            # This should not be 'query failed'
            assert "query failed" not in data["answer"].lower()
            
        except requests.exceptions.ConnectionError:
            pytest.skip("Live system not running on localhost:8000")
    
    def test_query_specific_lesson(self):
        """Test asking about a specific lesson."""
        try:
            response = requests.post(f"{self.BASE_URL}/api/query", json={
                "query": "What does lesson 1 of the RAG course cover?"
            })
            assert response.status_code == 200
            data = response.json()
            print(f"Specific lesson response: {data['answer']}")
            print(f"Sources returned: {len(data['sources'])}")
            
            # This should not be 'query failed'
            assert "query failed" not in data["answer"].lower()
            
        except requests.exceptions.ConnectionError:
            pytest.skip("Live system not running on localhost:8000")


if __name__ == "__main__":
    # Run with live system testing enabled
    os.environ["TEST_LIVE_SYSTEM"] = "1"
    pytest.main([__file__, "-v", "-s"])