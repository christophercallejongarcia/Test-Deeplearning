import anthropic
from typing import List, Optional, Dict, Any
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
    
    # Enhanced system prompt for sequential tool calling
    SYSTEM_PROMPT = """ You are an AI assistant specialized in course materials and educational content with access to comprehensive tools for course information.

🔄 SEQUENTIAL REASONING CAPABILITY:
You can perform multi-step reasoning by making tool calls across multiple rounds (max 2 rounds total).
Each round allows you to:
1. Analyze information from previous tool calls
2. Make additional tool calls based on that information
3. Synthesize a complete response

EXAMPLE SEQUENTIAL FLOWS:
- User: "What's the outline of course X and find similar courses?"
  Round 1: Use get_course_outline for course X
  Round 2: Use search_course_content to find courses with similar topics
  Final: Provide outline + similar course recommendations

- User: "What was covered in lesson 4 of course Y and are there other courses on that topic?"
  Round 1: Use search_course_content for lesson 4 content  
  Round 2: Use search_course_content to find courses on that topic
  Final: Provide lesson content + related courses

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
- Finding courses by topic (e.g., "courses about machine learning")

**SEQUENTIAL REASONING GUIDELINES:**
- If you need information from one tool to inform another tool call, continue to next round
- If you can provide a complete answer without additional tools, stop after current round
- Maximum 2 rounds total - synthesize final answer by round 2
- Build upon information from previous rounds

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
- **Multi-part questions**: Use sequential rounds to gather all needed information
- **No meta-commentary**: Provide direct answers only

All responses must be:
1. **Complete** - For course outlines, include all course details (title, link, lessons)
2. **Clear** - Use accessible language
3. **Direct** - Get to the point quickly
4. **Structured** - Maintain the format returned by tools
5. **Comprehensive** - Leverage sequential rounds for thorough answers"""
    
    @dataclass
    class RoundResult:
        """Results from a single round of tool calling"""
        response: str
        used_tools: List[str]
        tool_results: List[str]
        messages: List[Dict[str, Any]]
    
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
        Enhanced to support sequential tool calling up to 2 rounds.
        
        Args:
            query: The user's question or request
            conversation_history: Previous messages for context
            tools: Available tools the AI can use
            tool_manager: Manager to execute tools
            
        Returns:
            Generated response as string
        """
        try:
            # Use sequential tool calling for enhanced responses
            if tools and tool_manager:
                return self.generate_sequential_response(query, conversation_history, tools, tool_manager)
            else:
                # Fallback to single round for non-tool queries
                return self._generate_single_response(query, conversation_history)
                
        except Exception as e:
            logger.error(f"Error in generate_response: {str(e)}")
            return f"I apologize, but I encountered an error while processing your request. Please try again."
    
    def generate_sequential_response(self, query: str,
                                   conversation_history: Optional[str] = None,
                                   tools: Optional[List] = None,
                                   tool_manager=None,
                                   max_rounds: int = 2) -> str:
        """
        Generate response using sequential tool calling approach.
        Allows Claude to make tool calls across multiple rounds for complex queries.
        
        Args:
            query: The user's question or request
            conversation_history: Previous messages for context
            tools: Available tools the AI can use
            tool_manager: Manager to execute tools
            max_rounds: Maximum number of rounds (default: 2)
            
        Returns:
            Generated response as string
        """
        
        # Initialize sequential context
        context = SequentialContext(
            round_number=1,
            user_query=query,
            conversation_history=conversation_history,
            tools_used=[],
            tool_results=[],
            round_responses=[]
        )
        
        logger.info(f"Starting sequential response generation for query: {query[:100]}...")
        
        for round_num in range(1, max_rounds + 1):
            logger.info(f"Starting round {round_num}/{max_rounds}")
            
            try:
                # Execute current round
                round_result = self._execute_round(context, tools, tool_manager, round_num)
                
                # Check termination conditions
                if not round_result.used_tools or round_num == max_rounds:
                    logger.info(f"Terminating after round {round_num}. Used tools: {round_result.used_tools}, Max rounds: {round_num == max_rounds}")
                    return round_result.response
                
                # Add round results to context for next round
                context.add_round_result(
                    round_result.used_tools,
                    round_result.tool_results,
                    round_result.response
                )
                
                # Continue to next round if tools were used and we haven't hit max rounds
                logger.info(f"Round {round_num} completed, continuing to round {round_num + 1}")
                
            except Exception as e:
                logger.error(f"Error in round {round_num}: {str(e)}")
                # Return best available response or error message
                if context.round_responses:
                    return context.round_responses[-1]
                else:
                    return "I encountered an error while processing your request. Please try again."
        
        # Should not reach here, but safety fallback
        return context.round_responses[-1] if context.round_responses else "I was unable to generate a response."
    
    def _generate_single_response(self, query: str, conversation_history: Optional[str] = None) -> str:
        """
        Generate a simple single-round response without tools.
        
        Args:
            query: The user's question or request
            conversation_history: Previous messages for context
            
        Returns:
            Generated response as string
        """
        # Build system content efficiently
        system_content = (
            f"{self.SYSTEM_PROMPT}\n\nPrevious conversation:\n{conversation_history}"
            if conversation_history 
            else self.SYSTEM_PROMPT
        )
        
        # Prepare API call parameters
        api_params = {
            **self.base_params,
            "messages": [{"role": "user", "content": query}],
            "system": system_content
        }
        
        try:
            # Get response from Claude
            response = self.client.messages.create(**api_params)
            return self._safe_extract_response(response)
            
        except Exception as e:
            logger.error(f"Error in single response generation: {str(e)}")
            raise

    def _execute_round(self, context: SequentialContext, tools: Optional[List], 
                      tool_manager, round_num: int) -> 'AIGenerator.RoundResult':
        """
        Execute a single round of the sequential tool calling process.
        
        Args:
            context: Sequential context with round information
            tools: Available tools
            tool_manager: Manager to execute tools
            round_num: Current round number
            
        Returns:
            RoundResult with response and tool usage information
        """
        
        # Build system content with sequential context
        system_content = self._build_system_content_with_context(context, round_num)
        
        # Build messages for current round
        messages = self._build_messages_for_round(context, round_num)
        
        # Prepare API call parameters with tools (CRITICAL: keep tools available)
        api_params = {
            **self.base_params,
            "messages": messages,
            "system": system_content,
            "tools": tools,  # FIXED: Always include tools in each round
            "tool_choice": {"type": "auto"}
        }
        
        # Get initial response from Claude
        response = self.client.messages.create(**api_params)
        
        # Handle tool execution if needed
        if response.stop_reason == "tool_use" and tool_manager:
            return self._handle_tool_execution_sequential(response, api_params, tool_manager)
        
        # No tools used - return direct response
        return self.RoundResult(
            response=self._safe_extract_response(response),
            used_tools=[],
            tool_results=[],
            messages=messages + [{"role": "assistant", "content": response.content}]
        )
    
    def _handle_tool_execution_sequential(self, initial_response, base_params: Dict[str, Any], 
                                        tool_manager) -> 'AIGenerator.RoundResult':
        """
        Handle execution of tool calls in sequential context and get follow-up response.
        CRITICAL FIX: Preserve tools in follow-up API calls.
        
        Args:
            initial_response: The response containing tool use requests
            base_params: Base API parameters (includes tools)
            tool_manager: Manager to execute tools
            
        Returns:
            RoundResult with final response and tool information
        """
        # Start with existing messages
        messages = base_params["messages"].copy()
        
        # Add AI's tool use response
        messages.append({"role": "assistant", "content": initial_response.content})
        
        # Execute all tool calls and collect results
        tool_results = []
        used_tools = []
        tool_result_texts = []
        
        for content_block in initial_response.content:
            if content_block.type == "tool_use":
                try:
                    tool_result = tool_manager.execute_tool(
                        content_block.name, 
                        **content_block.input
                    )
                    
                    used_tools.append(content_block.name)
                    tool_result_texts.append(str(tool_result))
                    
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": content_block.id,
                        "content": tool_result
                    })
                    
                    logger.info(f"Successfully executed tool: {content_block.name}")
                    
                except Exception as e:
                    logger.error(f"Tool execution failed for {content_block.name}: {str(e)}")
                    # Add error result to maintain conversation flow
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": content_block.id,
                        "content": f"Tool execution failed: {str(e)}"
                    })
                    used_tools.append(f"{content_block.name} (failed)")
                    tool_result_texts.append(f"Error: {str(e)}")
        
        # Add tool results as single message
        if tool_results:
            messages.append({"role": "user", "content": tool_results})
        
        # CRITICAL FIX: Prepare final API call WITH TOOLS for potential next round
        final_params = {
            **self.base_params,
            "messages": messages,
            "system": base_params["system"]
        }
        
        # Only add tools if they were in the original parameters (maintain backward compatibility)
        if "tools" in base_params:
            final_params["tools"] = base_params["tools"]
            final_params["tool_choice"] = {"type": "auto"}
        
        try:
            # Get final response
            final_response = self.client.messages.create(**final_params)
            final_text = self._safe_extract_response(final_response)
            
            return self.RoundResult(
                response=final_text,
                used_tools=used_tools,
                tool_results=tool_result_texts,
                messages=messages + [{"role": "assistant", "content": final_response.content}]
            )
            
        except Exception as e:
            logger.error(f"Error in final API call: {str(e)}")
            # Return partial result with tool information
            return self.RoundResult(
                response=f"I gathered information using tools but encountered an error generating the final response: {str(e)}",
                used_tools=used_tools,
                tool_results=tool_result_texts,
                messages=messages
            )
    
    def _build_system_content_with_context(self, context: SequentialContext, round_num: int) -> str:
        """
        Build system content including conversation history and sequential context.
        
        Args:
            context: Sequential context with round information
            round_num: Current round number
            
        Returns:
            Complete system content string
        """
        parts = [self.SYSTEM_PROMPT]
        
        # Add conversation history if available
        if context.conversation_history:
            parts.append(f"\n\nPrevious conversation:\n{context.conversation_history}")
        
        # Add sequential context for rounds > 1
        if round_num > 1:
            context_summary = context.get_context_summary()
            if context_summary:
                parts.append(f"\n\nSequential Context (Previous Rounds):\n{context_summary}")
                parts.append(f"\n\nCurrent Round: {round_num}/2 - Build upon previous information to provide a comprehensive response.")
        
        return "".join(parts)
    
    def _build_messages_for_round(self, context: SequentialContext, round_num: int) -> List[Dict[str, Any]]:
        """
        Build message history for the current round.
        
        Args:
            context: Sequential context with round information
            round_num: Current round number
            
        Returns:
            List of messages for API call
        """
        if round_num == 1:
            # First round - just the user query
            return [{"role": "user", "content": context.user_query}]
        else:
            # Later rounds - include context about needing additional information
            context_prompt = f"""Original query: {context.user_query}

Based on information gathered in previous rounds, please continue with additional tool calls if needed to provide a complete response.

Previous rounds summary:
{context.get_context_summary()}

Please synthesize all information or make additional tool calls as needed."""
            
            return [{"role": "user", "content": context_prompt}]
    
    def _safe_extract_response(self, response) -> str:
        """
        Safely extract response text with error handling.
        
        Args:
            response: API response object
            
        Returns:
            Response text or error message
        """
        try:
            if response.content and len(response.content) > 0:
                return response.content[0].text
            else:
                logger.warning("API response has no content")
                return "I apologize, but I didn't receive a proper response. Please try again."
        except (AttributeError, IndexError, TypeError) as e:
            logger.error(f"Error extracting response: {str(e)}")
            return "I encountered an error processing the response. Please try again."

    def _handle_tool_execution(self, initial_response, base_params: Dict[str, Any], tool_manager):
        """
        DEPRECATED: Legacy method for backward compatibility.
        Now delegates to sequential tool execution.
        """
        logger.warning("Using deprecated _handle_tool_execution method. Consider migrating to sequential approach.")
        return self._handle_tool_execution_sequential(initial_response, base_params, tool_manager).response