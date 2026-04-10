import os
import subprocess
import tempfile
import shutil
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from mcp.server.fastmcp import FastMCP
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv

load_dotenv()

# Initialize a single FastMCP instance for all utility tools
mcp = FastMCP("manim_assistant")

# ==============================================================================
# YouTube Tools (YouTube Data API Access)
# ==============================================================================

# Initialize YouTube client
def get_youtube_client():
    refresh_token = os.getenv("GOOGLE_REFRESH_TOKEN")
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    
    if not refresh_token:
        print("WARNING: GOOGLE_REFRESH_TOKEN is not set in .env. YouTube tools will NOT work.")
        return None
        
    try:
        creds = Credentials(
            None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=["https://www.googleapis.com/auth/youtube.readonly"]
        )
        return build("youtube", "v3", credentials=creds)
    except Exception as e:
        print(f"ERROR: Failed to initialize YouTube client: {e}")
        return None

@mcp.tool()
def list_my_videos(max_results: int = 5) -> str:
    """List videos from the user's YouTube channel."""
    youtube = get_youtube_client()
    if not youtube:
        return "YouTube refresh token not found in .env. Please run getrefreshtoken.py first."
    
    try:
        request = youtube.channels().list(mine=True, part="contentDetails")
        response = request.execute()
        uploads_playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        
        request = youtube.playlistItems().list(
            playlistId=uploads_playlist_id,
            part="snippet",
            maxResults=max_results
        )
        response = request.execute()
        
        videos = []
        for item in response.get('items', []):
            title = item['snippet']['title']
            video_id = item['snippet']['resourceId']['videoId']
            videos.append(f"- {title} (ID: {video_id})")
            
        return "\n".join(videos) if videos else "No videos found."
    except Exception as e:
        return f"Error listing videos: {str(e)}"

@mcp.tool()
def get_video_stats(video_id: str) -> str:
    """Get statistics for a specific YouTube video."""
    youtube = get_youtube_client()
    if not youtube:
        return "YouTube refresh token not found in .env."
    
    try:
        request = youtube.videos().list(
            part="statistics,snippet",
            id=video_id
        )
        response = request.execute()
        
        if not response.get('items'):
            return "Video not found."
            
        item = response['items'][0]
        stats = item['statistics']
        title = item['snippet']['title']
        
        return (f"Title: {title}\n"
                f"Views: {stats.get('viewCount', 'N/A')}\n"
                f"Likes: {stats.get('likeCount', 'N/A')}\n"
                f"Comments: {stats.get('commentCount', 'N/A')}")
    except Exception as e:
        return f"Error getting stats: {str(e)}"

@mcp.tool()
def search_youtube_videos(query: str, max_results: int = 5) -> str:
    """Search for YouTube videos by query."""
    youtube = get_youtube_client()
    if not youtube:
        return "YouTube refresh token not found in .env."
    
    try:
        request = youtube.search().list(
            q=query,
            part="snippet",
            type="video",
            maxResults=max_results
        )
        response = request.execute()
        
        results = []
        for item in response.get('items', []):
            title = item['snippet']['title']
            video_id = item['id']['videoId']
            results.append(f"- {title} (https://www.youtube.com/watch?v={video_id})")
            
        return "\n".join(results) if results else "No results found."
    except Exception as e:
        return f"Error searching YouTube: {str(e)}"

# ==============================================================================
# Manim Documentation Tools (GitHub/Web Docs Access)
# ==============================================================================

@mcp.tool()
def search_manim_docs(query: str) -> str:
    """Search Manim documentation for correct syntax and usage."""
    search_query = f"site:docs.manim.community {query}"
    with DDGS() as ddgs:
        results = list(ddgs.text(search_query, max_results=5))
    return "\n".join([r["href"] for r in results])

@mcp.tool()
def read_doc_page(url: str) -> str:
    """Extract text from a Manim documentation page."""
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    paragraphs = soup.find_all("p")
    text = "\n".join(p.text for p in paragraphs[:20])
    return text

# ==============================================================================
# Manim Code Execution Tools
# ==============================================================================

# Get Manim executable path from environment variables or assume it's in the system PATH
MANIM_EXECUTABLE = os.getenv("MANIM_EXECUTABLE", "manim")
BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "media")
os.makedirs(BASE_DIR, exist_ok=True)

@mcp.tool()
def execute_manim_code(manim_code: str) -> str:
    """Execute Manim code and generate a video file."""
    tmpdir = os.path.join(BASE_DIR, "manim_tmp")  
    os.makedirs(tmpdir, exist_ok=True)
    script_path = os.path.join(tmpdir, "scene.py")
    
    try:
        with open(script_path, "w", encoding="utf-8") as script_file:
            script_file.write(manim_code)
        
        result = subprocess.run(
            [MANIM_EXECUTABLE, "-p", script_path],
            capture_output=True,
            text=True,
            cwd=tmpdir
        )

        if result.returncode == 0:
            return f"Execution successful. Video generated in {tmpdir}"
        else:
            return f"Execution failed: {result.stderr}"
    except Exception as e:
        return f"Error during execution: {str(e)}"

@mcp.tool()
def cleanup_manim_temp_dir(directory: str) -> str:
    """Clean up a specified Manim temporary directory."""
    try:
        if os.path.exists(directory):
            shutil.rmtree(directory)
            return f"Cleanup successful for directory: {directory}"
        return f"Directory not found: {directory}"
    except Exception as e:
        return f"Failed to clean up directory: {directory}. Error: {str(e)}"

# ==============================================================================
# Image / Assets Access Tools
# ==============================================================================

ASSETS_DIR = "assets"
os.makedirs(ASSETS_DIR, exist_ok=True)

@mcp.tool()
def search_image(query: str) -> str:
    """Search for images related to a concept. Returns a list of URLs."""
    with DDGS() as ddgs:
        results = list(ddgs.images(query, max_results=5))
    urls = [r["image"] for r in results]
    return "\n".join(urls)

@mcp.tool()
def download_image(url: str, filename: str) -> str:
    """Download an image into the assets folder."""
    path = os.path.join(ASSETS_DIR, filename)
    r = requests.get(url)
    with open(path, "wb") as f:
        f.write(r.content)
    return f"Saved image to {path}"

if __name__ == "__main__":
    import sys
    sys.stderr.write("\n🚀 [Manim Assistant - MCP Server] Starting...\n")
    sys.stderr.write("✅ Successfully registered tools:\n")
    sys.stderr.write("   - list_my_videos           (YouTube)\n")
    sys.stderr.write("   - get_video_stats          (YouTube)\n")
    sys.stderr.write("   - search_youtube_videos    (YouTube)\n")
    sys.stderr.write("   - search_manim_docs        (Documentation)\n")
    sys.stderr.write("   - read_doc_page            (Documentation)\n")
    sys.stderr.write("   - execute_manim_code       (Execution)\n")
    sys.stderr.write("   - cleanup_manim_temp_dir   (Cleanup)\n")
    sys.stderr.write("   - search_image             (Assets)\n")
    sys.stderr.write("   - download_image           (Assets)\n")
    sys.stderr.write("\n⚡ Server is ready and listening on stdio...\n\n")
    
    mcp.run()