from langgraph.graph import START, END, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode

from src.chatbot.graph.chat_state import ChatState
from src.chatbot.agent.chat_agent import agent_node
from src.mcp.client import get_mcp_tools


def agent_router(state: ChatState) -> str:
    """
    Route after the agent node:
    - If the LLM emitted tool_calls → run tool_node (ReAct loop)
    - Otherwise → END (respond to user)
    """
    last_msg = state["messages"][-1]
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        return "tool_node"
    return END


def build_chat_graph() -> StateGraph:
    """
    Build and compile the YouTube channel chatbot LangGraph.

    Graph topology:
        START → agent_node ──(tool_calls?)──► tool_node ──► agent_node
                           └──(done)────────────────────────────► END
    """
    workflow = StateGraph(ChatState)

    # ── Nodes ──────────────────────────────────────────────────────────────────
    workflow.add_node("agent_node", agent_node)

    # Prebuilt ToolNode — lazily fetches live MCP tools at runtime
    async def dynamic_tool_node(state: ChatState) -> dict:
        tools = get_mcp_tools()
        executor = ToolNode(tools)
        return await executor.ainvoke(state)

    workflow.add_node("tool_node", dynamic_tool_node)

    # ── Edges ──────────────────────────────────────────────────────────────────
    workflow.add_edge(START, "agent_node")

    workflow.add_conditional_edges(
        "agent_node",
        agent_router,
        {
            "tool_node": "tool_node",
            END: END,
        },
    )

    # After tools are executed, loop back to agent for the next reasoning step
    workflow.add_edge("tool_node", "agent_node")

    # ── Compile with in-memory checkpointer (per-thread conversation memory) ──
    checkpointer = MemorySaver()
    app = workflow.compile(checkpointer=checkpointer)
    return app


# Module-level singleton — built once when the backend starts
chat_graph = build_chat_graph()
