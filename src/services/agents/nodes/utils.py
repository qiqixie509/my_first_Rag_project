from langchain_core.messages import HumanMessage, ToolMessage
from typing import List
import logging

logger = logging.getLogger(__name__)


def get_latest_query(messages: List)->str:
    """Get the latest query from the messages list"""

    logger.debug("Getting latest query from messages")
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            return msg.content
    raise ValueError("No human message found in the conversation")


def get_latest_context(messages: List)->str:
    """Get the latest context from the messages list"""
    logger.debug("Getting latest context from messages")
    for msg in reversed(messages):
        if isinstance(msg, ToolMessage):
            return msg.content if hasattr(msg, 'content') else ""
    raise ValueError("No tool message found in the conversation")