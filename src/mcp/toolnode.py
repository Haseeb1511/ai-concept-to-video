from langgraph.prebuilt import ToolNode
from src.mcp.client import get_mcp_tools

def get_all_tools():
    """
    Get all available tools for the agent.
    Currently returns the MCP tools.
    """
    mcp_tools = get_mcp_tools()
    return mcp_tools



# We expose a wrapper function for the graph builder that
# instantiates LangGraph's prebuilt ToolNode with the live tools list.
# This prevents manual execution routing.
async def tool_node(state: dict) -> dict:
    """
    Executes tool calls requested by the agent automatically using LangGraph's ToolNode.
    """
    #fetch live tools
    all_tools = get_all_tools()
    
    # Initialize the prebuilt LangGraph ToolNode
    # in langgraph ToolNode act as a bridge between our Grapah and External Tools
    # toolnode can automatically detect which tool to call abse on query and waht argument to pass to that query
    executor = ToolNode(all_tools)
    
    # Execute
    return await executor.ainvoke(state)
