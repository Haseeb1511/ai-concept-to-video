from langchain_core.messages import SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage

from src.chatbot.graph.chat_state import ChatState
from src.chatbot.prompts.chat_system_prompt import YOUTUBE_ASSISTANT_SYSTEM_PROMPT
from src.mcp.client import get_mcp_tools


async def agent_node(state: ChatState) -> dict:
    """
    Core agent node for the YouTube channel chatbot.
    - Injects YouTube-focused system prompt
    - Binds all available MCP tools (YouTube API, Manim, etc.)
    - LLM decides whether to call tools or respond directly
    """
    # 1. Build message list: system prompt + conversation history
    prompt_messages = [SystemMessage(content=YOUTUBE_ASSISTANT_SYSTEM_PROMPT)]

    # Defensively filter: OpenAI requires ToolMessages to follow AIMessage with tool_calls.
    history = list(state.get("messages", []))
    while history and isinstance(history[0], ToolMessage):
        history.pop(0)

    prompt_messages.extend(history)

    # 2. Bind MCP tools to the LLM
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, streaming=True)
    tools = get_mcp_tools()
    
    if tools:
        model = llm.bind_tools(tools)
    else:
        model = llm

    # 3. Invoke LLM
    try:
        response = await model.ainvoke(prompt_messages)
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_response = AIMessage(
            content=f"Sorry, I ran into an error: {str(e)[:200]}. Please try again."
        )
        return {"messages": [error_response]}

    return {"messages": [response]}
