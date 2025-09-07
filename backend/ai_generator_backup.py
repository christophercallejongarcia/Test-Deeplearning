import anthropic
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SequentialContext:
    """Context data for sequential tool calling rounds"""
    round_number: int
    user_query: str
    conversation_history: Optional[str]
    tools_used: List[str]
    tool_results: List[str]
    round_responses: List[str]
    should_continue: bool = True
    
    def add_round_result(self, tools_used: List[str], tool_results: List[str], response: str):
        """Add results from a completed round"""
        self.tools_used.extend(tools_used)
        self.tool_results.extend(tool_results)
        self.round_responses.append(response)
        self.round_number += 1
    
    def get_context_summary(self) -> str:
        """Get a summary of all previous rounds for context"""
        if not self.round_responses:
            return ""
        
        summary_parts = []
        for i, response in enumerate(self.round_responses, 1):
            summary_parts.append(f"Round {i} outcome: {response[:200]}..." if len(response) > 200 else f"Round {i} outcome: {response}")
        
        return "\n".join(summary_parts)

class AIGenerator:
    """Handles interactions with Anthropic's Claude API for generating responses"""
    
    # Static system prompt to avoid rebuilding on each call
    SYSTEM_PROMPT = """ You are an AI assistant specialized in course materials and educational content with access to comprehensive tools for course information.

CRITICAL TOOL SELECTION RULES:

**USE get_course_outline FOR THESE TRIGGER PHRASES:**
- "outline" (e.g., "course outline", "outline of", "what is the outline")
- "structure" (e.g., "course structure", "how is the course structured")
- "lessons" (e.g., "what lessons", "list of lessons", "all lessons")
- "covered" (e.g., "what's covered", "what is covered in the course")
- "complete course" (e.g., "complete course outline", "full course")
- "syllabus" (e.g., "course syllabus", "what's in the syllabus")

**USE search_course_content FOR:**
- Specific lesson content (e.g., "what did lesson 5 cover")
- Detailed explanations (e.g., "explain RAG concepts")
- Technical questions about course material

**MANDATORY: Use get_course_outline tool when:**
- User asks about course outlines, structure, or lesson lists
- User wants to know "what's covered" in a course
- User asks for complete course information
- User mentions "syllabus" or "curriculum"

Course Outline Tool Output Format:
- Always return the complete course title, course link, and numbered lesson list
- Present exactly as returned by the tool - do not modify the structure

Response Protocol:
- **General knowledge questions**: Answer using existing knowledge without using tools
- **Course outline questions**: ALWAYS use get_course_outline tool first
- **Course content questions**: Use search_course_content tool
- **No meta-commentary**: Provide direct answers only

All responses must be:
1. **Complete** - For course outlines, include all course details (title, link, lessons)
2. **Clear** - Use accessible language
3. **Direct** - Get to the point quickly
4. **Structured** - Maintain the format returned by tools
"""
    
    def __init__(self, api_key: str, model: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        
        # Pre-build base API parameters
        self.base_params = {
            "model": self.model,
            "temperature": 0,
            "max_tokens": 800
        }
    
    def generate_response(self, query: str,
                         conversation_history: Optional[str] = None,
                         tools: Optional[List] = None,
                         tool_manager=None) -> str:
        """
        Generate AI response with optional tool usage and conversation context.
        
        Args:
            query: The user's question or request
            conversation_history: Previous messages for context
            tools: Available tools the AI can use
            tool_manager: Manager to execute tools
            
        Returns:
            Generated response as string
        """
        
        # Build system content efficiently - avoid string ops when possible
        system_content = (
            f"{self.SYSTEM_PROMPT}\n\nPrevious conversation:\n{conversation_history}"
            if conversation_history 
            else self.SYSTEM_PROMPT
        )
        
        # Prepare API call parameters efficiently
        api_params = {
            **self.base_params,
            "messages": [{"role": "user", "content": query}],
            "system": system_content
        }
        
        # Add tools if available
        if tools:
            api_params["tools"] = tools
            api_params["tool_choice"] = {"type": "auto"}
        
        # Get response from Claude
        response = self.client.messages.create(**api_params)
        
        # Handle tool execution if needed
        if response.stop_reason == "tool_use" and tool_manager:
            return self._handle_tool_execution(response, api_params, tool_manager)
        
        # Return direct response
        return response.content[0].text
    
    def _handle_tool_execution(self, initial_response, base_params: Dict[str, Any], tool_manager):
        """
        Handle execution of tool calls and get follow-up response.
        
        Args:
            initial_response: The response containing tool use requests
            base_params: Base API parameters
            tool_manager: Manager to execute tools
            
        Returns:
            Final response text after tool execution
        """
        # Start with existing messages
        messages = base_params["messages"].copy()
        
        # Add AI's tool use response
        messages.append({"role": "assistant", "content": initial_response.content})
        
        # Execute all tool calls and collect results
        tool_results = []
        for content_block in initial_response.content:
            if content_block.type == "tool_use":
                tool_result = tool_manager.execute_tool(
                    content_block.name, 
                    **content_block.input
                )
                
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": content_block.id,
                    "content": tool_result
                })
        
        # Add tool results as single message
        if tool_results:
            messages.append({"role": "user", "content": tool_results})
        
        # Prepare final API call without tools
        final_params = {
            **self.base_params,
            "messages": messages,
            "system": base_params["system"]
        }
        
        # Get final response
        final_response = self.client.messages.create(**final_params)
        return final_response.content[0].text