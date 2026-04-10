import asyncio
import sys
import os
import traceback
from typing import List, Any
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()



# Global variables to hold the active client and its tools
_mcp_client = None
_mcp_tools: List[Any] = []

async def init_mcp_client():
    global _mcp_client, _mcp_tools
    
    # absolute path for server.py script
    server_script = os.path.join(os.path.dirname(__file__), "server.py")
    
    npx_cmd = "npx.cmd" if sys.platform == "win32" else "npx"

    _mcp_client = MultiServerMCPClient({
        "local_server": {
            "command": sys.executable,
            "args": [server_script],
            "transport": "stdio",
        },
        "tavily": {                                          
            "url": "https://mcp.tavily.com/mcp/",
            "transport": "streamable_http",
            "headers": {
                "Authorization": f"Bearer {os.getenv('TAVILY_API_KEY')}"
            },
        },
        "github": {
            "command": npx_cmd,
            "args": ["-y", "@modelcontextprotocol/server-github"],
            "transport": "stdio",
            "env": {
                "GITHUB_PERSONAL_ACCESS_TOKEN": os.getenv("GITHUB_API_KEY", "")
            }
        }
    })
    
    try:
        _mcp_tools = await _mcp_client.get_tools()
        print("\n🛠️  [MCP Multi-Client] Successfully loaded all tools:")
        for tool in _mcp_tools:
            print(f"   ✅ {tool.name}")
        print(f"\n✨ Total tools available: {len(_mcp_tools)}\n")
    except Exception as e:
        print(f"❌ Failed to load MCP tools: {e}")
        traceback.print_exc()



async def close_mcp_client():
    """
    Closes the global MCP client connection.
    Designed to be called during FastAPI shutdown lifespan.
    """
    global _mcp_client
    if _mcp_client:
        await _mcp_client.close()
        _mcp_client = None



def get_mcp_tools() -> List[Any]:
    """
    Returns the globally cached MCP tools so LangGraph can bind them synchronously.
    """
    return _mcp_tools



# TO manually check working or not run in terminall
# set YOUTUBE_API_KEY=....
# npx -y @modelcontextprotocol/server-youtube
# npx -y @kirbah/mcp-youtube   this work 