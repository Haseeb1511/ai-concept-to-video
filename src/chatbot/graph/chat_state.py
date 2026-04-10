from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages


class ChatState(TypedDict, total=False):
    """Minimal state for the YouTube channel chatbot."""
    messages: Annotated[list[BaseMessage], add_messages]
