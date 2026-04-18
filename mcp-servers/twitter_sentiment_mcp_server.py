#!/usr/bin/env python3
"""
MCP Server for Twitter Alpha Sentiment Analysis
Wraps the Twitter sentiment tracker NLP engine.
"""

import asyncio
import json
import sys
from typing import Any, Sequence

from mcp import Tool
from mcp.server import Server
from mcp.types import TextContent, PromptMessage
import mcp.server.stdio

# Add the twitter tracker path to sys.path
sys.path.insert(0, "/workspaces/Memetrader/mcp-wrappers/social/twitter-alpha-sentiment-tracker-v2")

from nlp.sentiment import SentimentEngine

server = Server("twitter-sentiment-mcp")

# Initialize the sentiment engine
sentiment_engine = SentimentEngine()

@server.tool()
async def analyze_twitter_sentiment(text: str) -> str:
    """
    Analyze sentiment of Twitter text using FinBERT + VADER hybrid model.
    
    Args:
        text: Twitter post text to analyze
        
    Returns:
        JSON with sentiment analysis (BUY/SELL/NEUTRAL, confidence, scores)
    """
    try:
        result = sentiment_engine.analyze(text)
        
        return json.dumps({
            "direction": result.direction,
            "confidence": result.confidence,
            "finbert_positive": result.finbert_positive,
            "finbert_negative": result.finbert_negative,
            "finbert_neutral": result.finbert_neutral,
            "vader_compound": result.vader_compound,
            "consensus": result.consensus
        })
        
    except Exception as e:
        return json.dumps({"error": str(e)})

async def main():
    # Run the server using stdio transport
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, 
            write_stream, 
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())