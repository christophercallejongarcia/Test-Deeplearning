"""
Comprehensive tests for AIGenerator sequential tool calling functionality.
Tests focus on external behavior verification rather than internal state details.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from ai_generator import AIGenerator, SequentialContext

class TestAIGeneratorSequential:
    """Test the enhanced AIGenerator with sequential tool calling."""

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

    @pytest.fixture
    def mock_tools(self):
        """Create mock tools for testing."""
        return [
            {
                "name": "get_course_outline",
                "description": "Get course outline",
                "input_schema": {"type": "object", "properties": {"course_title": {"type": "string"}}}
            },
            {
                "name": "search_course_content", 
                "description": "Search for course content",
                "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}}
            }
        ]

    def test_sequential_two_round_flow_course_outline_then_search(self, ai_generator, mock_anthropic_client, mock_tools):
        """
        Test the desired sequential flow: get course outline → search for similar courses
        This tests the main use case described in the requirements.
        """
        # Mock first round: Claude decides to get course outline
        mock_outline_tool = Mock()
        mock_outline_tool.type = "tool_use"
        mock_outline_tool.name = "get_course_outline"
        mock_outline_tool.id = "tool_outline_123"
        mock_outline_tool.input = {"course_title": "MCP Course"}

        mock_first_response = Mock()
        mock_first_response.stop_reason = "tool_use"
        mock_first_response.content = [mock_outline_tool]

        # Mock first round follow-up response after tool execution
        mock_first_followup = Mock()
        mock_first_followup.content = [Mock(text="Based on the course outline, I can see this covers MCP concepts. Let me search for similar courses.")]

        # Mock second round: Claude decides to search for similar courses
        mock_search_tool = Mock()
        mock_search_tool.type = "tool_use"
        mock_search_tool.name = "search_course_content"
        mock_search_tool.id = "tool_search_456"
        mock_search_tool.input = {"query": "MCP similar courses"}

        mock_second_response = Mock()
        mock_second_response.stop_reason = "tool_use"
        mock_second_response.content = [mock_search_tool]

        # Mock final response after second round tools
        mock_final_response = Mock()
        mock_final_response.content = [Mock(text="Here's the complete course outline and similar courses found.")]

        # Set up API call sequence
        mock_anthropic_client.messages.create.side_effect = [
            mock_first_response,      # Round 1: tool use decision
            mock_first_followup,      # Round 1: response after tool execution  
            mock_second_response,     # Round 2: tool use decision
            mock_final_response       # Round 2: final response
        ]

        # Mock tool manager
        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.side_effect = [
            "Course: MCP\nLesson 1: Introduction\nLesson 2: Advanced Topics",  # Outline result
            "Similar courses: AI Fundamentals, Advanced ML"  # Search result
        ]

        # Execute sequential query
        result = ai_generator.generate_response(
            "What's the outline of the MCP course and find similar courses?",
            tools=mock_tools,
            tool_manager=mock_tool_manager
        )

        # Verify external behavior
        assert "Here's the complete course outline and similar courses found." in result
        
        # Verify tool execution sequence
        assert mock_tool_manager.execute_tool.call_count == 2
        mock_tool_manager.execute_tool.assert_any_call("get_course_outline", course_title="MCP Course")
        mock_tool_manager.execute_tool.assert_any_call("search_course_content", query="MCP similar courses")
        
        # Verify API calls were made (4 calls: 2 rounds × 2 calls per round)
        assert mock_anthropic_client.messages.create.call_count == 4

    def test_sequential_early_termination_no_tools_needed(self, ai_generator, mock_anthropic_client, mock_tools):
        """
        Test that sequential processing terminates early when no tools are needed.
        Condition (b): Claude's response has no tool_use blocks
        """
        # Mock response without tool use
        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock(text="This is a general knowledge question I can answer directly without tools.")]

        mock_anthropic_client.messages.create.return_value = mock_response

        mock_tool_manager = Mock()

        # Execute query
        result = ai_generator.generate_response(
            "What is artificial intelligence?",
            tools=mock_tools,
            tool_manager=mock_tool_manager
        )

        # Verify behavior
        assert "This is a general knowledge question I can answer directly without tools." in result
        
        # Should only make 1 API call (early termination)
        assert mock_anthropic_client.messages.create.call_count == 1
        
        # No tools should be executed
        mock_tool_manager.execute_tool.assert_not_called()

    def test_sequential_max_rounds_termination(self, ai_generator, mock_anthropic_client, mock_tools):
        """
        Test that sequential processing terminates after maximum 2 rounds.
        Condition (a): 2 rounds completed
        """
        # Mock tools for both rounds
        def create_tool_mock(name, tool_id, input_params):
            tool = Mock()
            tool.type = "tool_use"
            tool.name = name
            tool.id = tool_id
            tool.input = input_params
            return tool

        # Round 1: get_course_outline
        round1_tool = create_tool_mock("get_course_outline", "tool_1", {"course_title": "Test Course"})
        round1_initial = Mock()
        round1_initial.stop_reason = "tool_use"
        round1_initial.content = [round1_tool]
        
        round1_followup = Mock()
        round1_followup.content = [Mock(text="Got the outline, now searching for more info.")]

        # Round 2: search_course_content  
        round2_tool = create_tool_mock("search_course_content", "tool_2", {"query": "advanced topics"})
        round2_initial = Mock()
        round2_initial.stop_reason = "tool_use" 
        round2_initial.content = [round2_tool]

        round2_final = Mock()
        round2_final.content = [Mock(text="Final comprehensive response after 2 rounds.")]

        # Set up API call sequence
        mock_anthropic_client.messages.create.side_effect = [
            round1_initial, round1_followup,  # Round 1
            round2_initial, round2_final      # Round 2 (should terminate here)
        ]

        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.side_effect = ["Outline content", "Search results"]

        # Execute
        result = ai_generator.generate_response(
            "Complex multi-part query",
            tools=mock_tools,
            tool_manager=mock_tool_manager
        )

        # Verify termination after exactly 2 rounds
        assert result == "Final comprehensive response after 2 rounds."
        assert mock_anthropic_client.messages.create.call_count == 4  # 2 rounds × 2 calls
        assert mock_tool_manager.execute_tool.call_count == 2

    def test_sequential_tool_execution_error_handling(self, ai_generator, mock_anthropic_client, mock_tools):
        """
        Test graceful handling of tool execution errors.
        Condition (c): tool call fails
        """
        # Mock tool use
        tool_mock = Mock()
        tool_mock.type = "tool_use"
        tool_mock.name = "failing_tool"
        tool_mock.id = "tool_fail"
        tool_mock.input = {"param": "value"}

        initial_response = Mock()
        initial_response.stop_reason = "tool_use"
        initial_response.content = [tool_mock]

        # Mock follow-up response after tool error
        final_response = Mock()
        final_response.content = [Mock(text="I encountered an error but handled it gracefully.")]

        mock_anthropic_client.messages.create.side_effect = [initial_response, final_response]

        # Mock tool manager that fails
        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.side_effect = Exception("Tool execution failed")

        # Execute
        result = ai_generator.generate_response(
            "Test query",
            tools=mock_tools,
            tool_manager=mock_tool_manager
        )

        # Should handle error gracefully and continue
        assert isinstance(result, str)
        assert len(result) > 0
        
        # Tool should have been attempted
        mock_tool_manager.execute_tool.assert_called_once()

    def test_sequential_context_management_between_rounds(self, ai_generator, mock_anthropic_client, mock_tools):
        """
        Test that conversation context is properly preserved and passed between rounds.
        """
        # Mock two-round scenario
        round1_tool = Mock()
        round1_tool.type = "tool_use"
        round1_tool.name = "get_course_outline"
        round1_tool.id = "tool_1"
        round1_tool.input = {"course_title": "Test"}

        round1_initial = Mock()
        round1_initial.stop_reason = "tool_use"
        round1_initial.content = [round1_tool]

        round1_followup = Mock()
        round1_followup.content = [Mock(text="Round 1 completed successfully.")]

        round2_tool = Mock()
        round2_tool.type = "tool_use" 
        round2_tool.name = "search_course_content"
        round2_tool.id = "tool_2"
        round2_tool.input = {"query": "related content"}

        round2_initial = Mock()
        round2_initial.stop_reason = "tool_use"
        round2_initial.content = [round2_tool]

        round2_final = Mock()
        round2_final.content = [Mock(text="Final response with full context.")]

        mock_anthropic_client.messages.create.side_effect = [
            round1_initial, round1_followup, round2_initial, round2_final
        ]

        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.side_effect = ["Result 1", "Result 2"]

        # Execute with conversation history
        result = ai_generator.generate_response(
            "Complex query",
            conversation_history="Previous: User asked about courses. Assistant: Explained basics.",
            tools=mock_tools,
            tool_manager=mock_tool_manager
        )

        # Verify context was used
        assert result == "Final response with full context."

        # Check that system prompts included context information
        api_calls = mock_anthropic_client.messages.create.call_args_list
        
        # First round should include conversation history
        first_call_system = api_calls[0][1]["system"]
        assert "Previous conversation:" in first_call_system
        
        # Second round should include sequential context
        if len(api_calls) >= 3:  # Round 2 initial call
            second_round_system = api_calls[2][1]["system"]
            assert "Sequential Context" in second_round_system or "Original query:" in str(api_calls[2][1]["messages"])

    def test_sequential_vs_single_response_routing(self, ai_generator, mock_anthropic_client):
        """
        Test that the system correctly routes to sequential vs single response based on tool availability.
        """
        # Test 1: With tools and tool_manager - should use sequential
        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock(text="Sequential path response")]
        mock_anthropic_client.messages.create.return_value = mock_response

        result1 = ai_generator.generate_response(
            "Test query",
            tools=[{"name": "test_tool"}],
            tool_manager=Mock()
        )
        
        # Should have used sequential path (even if no tools were actually used)
        assert result1 == "Sequential path response"

        # Test 2: Without tools - should use single response
        mock_anthropic_client.messages.create.reset_mock()
        mock_response2 = Mock()
        mock_response2.stop_reason = "end_turn"
        mock_response2.content = [Mock(text="Single path response")]
        mock_anthropic_client.messages.create.return_value = mock_response2

        result2 = ai_generator.generate_response("Test query without tools")
        
        assert result2 == "Single path response"

    def test_system_prompt_includes_sequential_guidelines(self, ai_generator):
        """
        Test that the system prompt contains sequential reasoning guidelines.
        """
        system_prompt = ai_generator.SYSTEM_PROMPT
        
        # Check for sequential capability indicators
        assert "SEQUENTIAL REASONING CAPABILITY" in system_prompt
        assert "multi-step reasoning" in system_prompt.lower()
        assert "2 rounds total" in system_prompt.lower()
        assert "EXAMPLE SEQUENTIAL FLOWS" in system_prompt
        
        # Check for termination conditions guidance
        assert "continue to next round" in system_prompt.lower()
        assert "complete answer without additional tools" in system_prompt.lower()

    def test_error_recovery_with_partial_results(self, ai_generator, mock_anthropic_client, mock_tools):
        """
        Test error recovery when second round fails but first round succeeded.
        """
        # Round 1 succeeds
        round1_tool = Mock()
        round1_tool.type = "tool_use"
        round1_tool.name = "get_course_outline" 
        round1_tool.id = "tool_1"
        round1_tool.input = {"course_title": "Test"}

        round1_initial = Mock()
        round1_initial.stop_reason = "tool_use"
        round1_initial.content = [round1_tool]

        round1_followup = Mock()
        round1_followup.content = [Mock(text="Round 1 successful result")]

        # Round 2 fails
        mock_anthropic_client.messages.create.side_effect = [
            round1_initial, 
            round1_followup,
            Exception("API error in round 2")  # Round 2 fails
        ]

        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.return_value = "Tool result"

        # Execute
        result = ai_generator.generate_response(
            "Test query",
            tools=mock_tools,
            tool_manager=mock_tool_manager
        )

        # Should return the successful result from round 1
        assert result == "Round 1 successful result"

class TestSequentialContext:
    """Test the SequentialContext helper class."""

    def test_context_initialization(self):
        """Test context is properly initialized."""
        context = SequentialContext(
            round_number=1,
            user_query="Test query",
            conversation_history="Previous convo",
            tools_used=[],
            tool_results=[],
            round_responses=[]
        )
        
        assert context.round_number == 1
        assert context.user_query == "Test query" 
        assert context.conversation_history == "Previous convo"
        assert context.should_continue is True

    def test_context_add_round_result(self):
        """Test adding round results to context."""
        context = SequentialContext(
            round_number=1,
            user_query="Test",
            conversation_history=None,
            tools_used=[],
            tool_results=[],
            round_responses=[]
        )
        
        context.add_round_result(
            ["tool1", "tool2"],
            ["result1", "result2"], 
            "Round response"
        )
        
        assert context.round_number == 2
        assert context.tools_used == ["tool1", "tool2"]
        assert context.tool_results == ["result1", "result2"]
        assert context.round_responses == ["Round response"]

    def test_context_summary_generation(self):
        """Test context summary generation for multiple rounds."""
        context = SequentialContext(
            round_number=1,
            user_query="Test",
            conversation_history=None,
            tools_used=[],
            tool_results=[],
            round_responses=["First round result", "Second round result"]
        )
        
        summary = context.get_context_summary()
        
        assert "Round 1 outcome: First round result" in summary
        assert "Round 2 outcome: Second round result" in summary

    def test_context_summary_truncation(self):
        """Test that long responses are truncated in summary."""
        long_response = "A" * 300  # 300 character response
        context = SequentialContext(
            round_number=1,
            user_query="Test",
            conversation_history=None,
            tools_used=[],
            tool_results=[],
            round_responses=[long_response]
        )
        
        summary = context.get_context_summary()
        
        # Should be truncated to 200 chars + "..."
        assert len(summary) < len(long_response)
        assert "..." in summary


if __name__ == "__main__":
    pytest.main([__file__])