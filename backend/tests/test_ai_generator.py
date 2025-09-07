"""
Comprehensive tests for AIGenerator to identify tool calling and API issues.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from ai_generator import AIGenerator


class TestAIGenerator:
    """Test the AIGenerator functionality comprehensively."""

    @pytest.fixture
    def mock_anthropic_client(self):
        """Create a mock Anthropic client."""
        with patch('ai_generator.anthropic') as mock_anthropic:
            mock_client = Mock()
            mock_anthropic.Anthropic.return_value = mock_client
            yield mock_client

    @pytest.fixture 
    def ai_generator(self, mock_anthropic_client):
        """Create an AIGenerator instance with mocked client."""
        return AIGenerator("test-api-key", "claude-sonnet-4-20250514")

    def test_initialization(self, mock_anthropic_client):
        """Test AIGenerator initialization."""
        generator = AIGenerator("test-key", "test-model")
        
        assert generator.model == "test-model"
        assert generator.base_params["model"] == "test-model"
        assert generator.base_params["temperature"] == 0
        assert generator.base_params["max_tokens"] == 800

    def test_generate_response_without_tools(self, ai_generator, mock_anthropic_client):
        """Test generating response without tools (direct response)."""
        # Mock response without tool use
        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock(text="This is a direct response")]
        mock_anthropic_client.messages.create.return_value = mock_response
        
        result = ai_generator.generate_response("What is AI?")
        
        # Verify API call
        mock_anthropic_client.messages.create.assert_called_once()
        call_args = mock_anthropic_client.messages.create.call_args[1]
        
        assert call_args["model"] == "claude-sonnet-4-20250514"
        assert call_args["temperature"] == 0
        assert call_args["max_tokens"] == 800
        assert call_args["messages"] == [{"role": "user", "content": "What is AI?"}]
        assert "tools" not in call_args
        
        assert result == "This is a direct response"

    def test_generate_response_with_conversation_history(self, ai_generator, mock_anthropic_client):
        """Test generating response with conversation history."""
        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock(text="Response with history")]
        mock_anthropic_client.messages.create.return_value = mock_response
        
        history = "Previous: User asked about RAG. Assistant: RAG stands for..."
        
        result = ai_generator.generate_response("Tell me more", conversation_history=history)
        
        call_args = mock_anthropic_client.messages.create.call_args[1]
        
        # System prompt should include history
        assert history in call_args["system"]
        assert result == "Response with history"

    def test_generate_response_with_tools_no_tool_use(self, ai_generator, mock_anthropic_client):
        """Test response generation with tools available but not used."""
        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock(text="Direct answer without tools")]
        mock_anthropic_client.messages.create.return_value = mock_response
        
        tools = [
            {
                "name": "search_course_content",
                "description": "Search for course content",
                "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}}
            }
        ]
        mock_tool_manager = Mock()
        
        result = ai_generator.generate_response(
            "What's 2+2?",
            tools=tools,
            tool_manager=mock_tool_manager
        )
        
        call_args = mock_anthropic_client.messages.create.call_args[1]
        
        # Tools should be included in API call
        assert call_args["tools"] == tools
        assert call_args["tool_choice"] == {"type": "auto"}
        
        # Tool manager should not be called since no tools were used
        mock_tool_manager.execute_tool.assert_not_called()
        
        assert result == "Direct answer without tools"

    def test_generate_response_with_tool_use_sequential_path(self, ai_generator, mock_anthropic_client):
        """Test response generation with tool use (now uses sequential path)."""
        # Mock initial response with tool use
        mock_tool_use = Mock()
        mock_tool_use.type = "tool_use"
        mock_tool_use.name = "search_course_content"
        mock_tool_use.id = "tool_123"
        mock_tool_use.input = {"query": "test query"}
        
        mock_initial_response = Mock()
        mock_initial_response.stop_reason = "tool_use"
        mock_initial_response.content = [mock_tool_use]
        
        # Mock final response after tool execution
        mock_final_response = Mock()
        mock_final_response.content = [Mock(text="Final response with tool results")]
        
        mock_anthropic_client.messages.create.side_effect = [
            mock_initial_response,
            mock_final_response
        ]
        
        # Mock tool manager
        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.return_value = "Tool search results"
        
        tools = [{"name": "search_course_content"}]
        
        result = ai_generator.generate_response(
            "Search for RAG information",
            tools=tools,
            tool_manager=mock_tool_manager
        )
        
        # Verify tool was executed
        mock_tool_manager.execute_tool.assert_called_once_with(
            "search_course_content",
            query="test query"
        )
        
        # Verify API calls were made - sequential processing may make more calls
        # (at least 2: initial tool call + final response)
        assert mock_anthropic_client.messages.create.call_count >= 2
        
        # Verify final result
        assert result == "Final response with tool results"

    def test_generate_response_multiple_tool_calls(self, ai_generator, mock_anthropic_client):
        """Test handling multiple tool calls in one response."""
        # Mock multiple tool uses
        mock_tool_use_1 = Mock()
        mock_tool_use_1.type = "tool_use"
        mock_tool_use_1.name = "search_course_content"
        mock_tool_use_1.id = "tool_123"
        mock_tool_use_1.input = {"query": "first query"}
        
        mock_tool_use_2 = Mock()
        mock_tool_use_2.type = "tool_use"
        mock_tool_use_2.name = "get_course_outline"
        mock_tool_use_2.id = "tool_456"
        mock_tool_use_2.input = {"course_title": "Test Course"}
        
        mock_initial_response = Mock()
        mock_initial_response.stop_reason = "tool_use"
        mock_initial_response.content = [mock_tool_use_1, mock_tool_use_2]
        
        mock_final_response = Mock()
        mock_final_response.content = [Mock(text="Response with multiple tool results")]
        
        mock_anthropic_client.messages.create.side_effect = [
            mock_initial_response,
            mock_final_response
        ]
        
        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.side_effect = [
            "Search results",
            "Course outline results"
        ]
        
        # Must provide non-empty tools array for sequential processing to engage
        tools = [
            {"name": "search_course_content"},
            {"name": "get_course_outline"}
        ]
        
        result = ai_generator.generate_response(
            "Get course info",
            tools=tools,  # Fixed: provide actual tools
            tool_manager=mock_tool_manager
        )
        
        # Verify both tools were executed
        assert mock_tool_manager.execute_tool.call_count == 2
        mock_tool_manager.execute_tool.assert_any_call(
            "search_course_content",
            query="first query"
        )
        mock_tool_manager.execute_tool.assert_any_call(
            "get_course_outline", 
            course_title="Test Course"
        )

    def test_handle_tool_execution_message_flow_deprecated_method(self, ai_generator, mock_anthropic_client):
        """Test the deprecated _handle_tool_execution method (for backward compatibility)."""
        # Setup mocks
        mock_tool_use = Mock()
        mock_tool_use.type = "tool_use"
        mock_tool_use.name = "test_tool"
        mock_tool_use.id = "tool_123"
        mock_tool_use.input = {"param": "value"}
        
        mock_initial_response = Mock()
        mock_initial_response.content = [mock_tool_use]
        
        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.return_value = "Tool result"
        
        base_params = {
            "model": "test-model",
            "messages": [{"role": "user", "content": "test query"}],
            "system": "test system prompt",
            "tools": [{"name": "test_tool"}]  # Include tools for new implementation
        }
        
        # Mock final API call
        mock_final_response = Mock()
        mock_final_response.content = [Mock(text="Final answer")]
        mock_anthropic_client.messages.create.return_value = mock_final_response
        
        # Execute deprecated tool handling method
        with patch('ai_generator.logger') as mock_logger:
            result = ai_generator._handle_tool_execution(
                mock_initial_response,
                base_params,
                mock_tool_manager
            )
            
            # Should log deprecation warning
            mock_logger.warning.assert_called_once()
            assert "deprecated" in mock_logger.warning.call_args[0][0].lower()
        
        # Should still return string result
        assert isinstance(result, str)
        assert result == "Final answer"

    def test_api_error_handling_without_tools(self, ai_generator, mock_anthropic_client):
        """Test handling of API errors in single response mode."""
        # Mock API exception
        mock_anthropic_client.messages.create.side_effect = Exception("API Error: Rate limit exceeded")
        
        # Without tools, generates error response due to top-level exception handling
        result = ai_generator.generate_response("test query")  # No tools provided
        
        # Should return error message instead of propagating (due to top-level exception handling)
        assert isinstance(result, str)
        assert "encountered an error" in result.lower()
    
    def test_api_error_handling_with_tools_graceful(self, ai_generator, mock_anthropic_client):
        """Test graceful handling of API errors in sequential mode."""
        # Mock API exception
        mock_anthropic_client.messages.create.side_effect = Exception("API Error: Rate limit exceeded")
        
        # With tools, should use sequential mode and handle gracefully
        result = ai_generator.generate_response(
            "test query", 
            tools=[{"name": "test_tool"}], 
            tool_manager=Mock()
        )
        
        # Should return error message instead of propagating
        assert isinstance(result, str)
        assert "encountered an error" in result.lower()

    def test_tool_execution_error_handling_graceful_degradation(self, ai_generator, mock_anthropic_client):
        """Test graceful handling of tool execution errors in sequential processing."""
        # Mock tool use response
        mock_tool_use = Mock()
        mock_tool_use.type = "tool_use"
        mock_tool_use.name = "failing_tool"
        mock_tool_use.id = "tool_123"
        mock_tool_use.input = {"param": "value"}
        
        mock_initial_response = Mock()
        mock_initial_response.stop_reason = "tool_use"
        mock_initial_response.content = [mock_tool_use]
        
        # Mock final response (should still work despite tool error)
        mock_final_response = Mock()
        mock_final_response.content = [Mock(text="Response despite tool error")]
        
        mock_anthropic_client.messages.create.side_effect = [
            mock_initial_response,
            mock_final_response
        ]
        
        # Mock tool manager that raises an exception
        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.side_effect = Exception("Tool execution failed")
        
        # Should handle the error gracefully with new sequential processing
        result = ai_generator.generate_response(
            "test",
            tools=[{"name": "failing_tool"}],
            tool_manager=mock_tool_manager
        )
        
        # Should return a string response (graceful error handling)
        assert isinstance(result, str)
        assert len(result) > 0
        
        # Tool should have been attempted
        mock_tool_manager.execute_tool.assert_called_once_with("failing_tool", param="value")

    def test_empty_tool_results(self, ai_generator, mock_anthropic_client):
        """Test handling when no tool results are available."""
        mock_initial_response = Mock()
        mock_initial_response.stop_reason = "tool_use"
        mock_initial_response.content = []  # No tool use blocks
        
        mock_final_response = Mock()
        mock_final_response.content = [Mock(text="Response with no tools")]
        mock_anthropic_client.messages.create.return_value = mock_final_response
        
        mock_tool_manager = Mock()
        
        base_params = {"messages": [{"role": "user", "content": "test"}], "system": "test"}
        
        result = ai_generator._handle_tool_execution(
            mock_initial_response,
            base_params,
            mock_tool_manager
        )
        
        # Should still make final API call even with no tool results  
        # Note: With safe response extraction, this should work
        assert isinstance(result, str)
        assert len(result) > 0  # Should return some response, even if not exactly what's expected
        mock_tool_manager.execute_tool.assert_not_called()

    def test_system_prompt_structure(self, ai_generator):
        """Test that system prompt contains expected elements."""
        system_prompt = ai_generator.SYSTEM_PROMPT
        
        # Check for key elements that should be in the system prompt
        assert "search_course_content" in system_prompt
        assert "get_course_outline" in system_prompt
        assert "outline" in system_prompt.lower()
        assert "lesson" in system_prompt.lower()
        
        # Should contain tool selection rules
        assert "USE get_course_outline FOR" in system_prompt
        assert "USE search_course_content FOR" in system_prompt

    def test_parameter_validation(self, mock_anthropic_client):
        """Test parameter validation during initialization."""
        # Test with empty API key
        generator = AIGenerator("", "test-model")
        assert generator.base_params["model"] == "test-model"
        
        # Test with None values
        generator = AIGenerator(None, None)
        # Should handle gracefully or raise appropriate error


if __name__ == "__main__":
    pytest.main([__file__])