"""
Complete LangChain Agent using Recall Notebook API
Demonstrates tool-based agent with knowledge base access
"""
import os
from typing import List, Dict

import httpx
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.tools import Tool
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

# Configuration
API_URL = os.getenv("RECALL_API_URL", "https://your-app.railway.app")
API_TOKEN = os.getenv("RECALL_API_TOKEN")  # JWT token from Supabase Auth


class RecallAPIClient:
    """Client for Recall Notebook API."""

    def __init__(self, api_url: str, token: str):
        self.api_url = api_url
        self.token = token
        self.headers = {"Authorization": f"Bearer {token}"}

    def search(self, query: str, mode: str = "hybrid", limit: int = 5) -> str:
        """
        Search knowledge base and format results.

        Args:
            query: Search query
            mode: Search mode (semantic, keyword, hybrid)
            limit: Max results

        Returns:
            Formatted search results
        """
        try:
            response = httpx.post(
                f"{self.api_url}/api/v1/search",
                json={"query": query, "mode": mode, "limit": limit},
                headers=self.headers,
                timeout=30.0,
            )
            response.raise_for_status()

            results = response.json()["results"]

            if not results:
                return "No results found in knowledge base."

            # Format results for agent
            formatted = []
            for i, r in enumerate(results, 1):
                formatted.append(
                    f"{i}. [{r['source']['title']}] (relevance: {r['relevance_score']:.2f})\n"
                    f"   Summary: {r['summary']['summary_text']}\n"
                    f"   Topics: {', '.join(r['summary']['key_topics'])}"
                )

            return "\n\n".join(formatted)

        except Exception as e:
            return f"Search failed: {str(e)}"

    def save_knowledge(self, title: str, content: str) -> str:
        """
        Save new information to knowledge base.

        Args:
            title: Document title
            content: Document content

        Returns:
            Confirmation message
        """
        try:
            # First, summarize the content
            summary_response = httpx.post(
                f"{self.api_url}/api/v1/summarize",
                json={"content": content, "content_type": "text"},
                headers=self.headers,
                timeout=60.0,
            )
            summary_response.raise_for_status()
            summary = summary_response.json()

            # Save to knowledge base
            source_response = httpx.post(
                f"{self.api_url}/api/v1/sources",
                json={
                    "title": title,
                    "content_type": "text",
                    "original_content": content,
                    "summary_text": summary["summary"],
                    "key_actions": summary["key_actions"],
                    "key_topics": summary["topics"],
                    "word_count": summary["word_count"],
                },
                headers=self.headers,
                timeout=30.0,
            )
            source_response.raise_for_status()

            source = source_response.json()
            return f"✅ Saved to knowledge base: {source['source']['id']}"

        except Exception as e:
            return f"Save failed: {str(e)}"

    def fetch_url(self, url: str) -> str:
        """
        Fetch and extract content from URL.

        Args:
            url: URL to fetch

        Returns:
            Extracted content or error message
        """
        try:
            response = httpx.post(
                f"{self.api_url}/api/v1/fetch-url",
                json={"url": url},
                headers=self.headers,
                timeout=60.0,
            )
            response.raise_for_status()

            data = response.json()
            return (
                f"Title: {data['title']}\n"
                f"Content: {data['content'][:500]}...\n"
                f"Word count: {data['word_count']}"
            )

        except Exception as e:
            return f"URL fetch failed: {str(e)}"


def create_recall_agent(api_client: RecallAPIClient) -> AgentExecutor:
    """
    Create LangChain agent with Recall Notebook tools.

    Args:
        api_client: Recall API client

    Returns:
        Configured agent executor
    """
    # Define tools
    tools = [
        Tool(
            name="search_knowledge_base",
            func=api_client.search,
            description="""
            Search the knowledge base for relevant information.
            Input should be a natural language query about what you're looking for.
            Returns summaries of relevant documents with relevance scores.
            Use this when you need to find existing information.
            """,
        ),
        Tool(
            name="save_to_knowledge_base",
            func=lambda input_str: api_client.save_knowledge(
                title=input_str.split("|")[0].strip(),
                content=input_str.split("|")[1].strip(),
            ),
            description="""
            Save new information to the knowledge base.
            Input should be: "title|content"
            Example: "ML Research Findings|Deep learning uses neural networks..."
            Use this when you want to store important findings or insights.
            """,
        ),
        Tool(
            name="fetch_url_content",
            func=api_client.fetch_url,
            description="""
            Fetch and extract text content from a URL.
            Input should be a valid URL starting with http:// or https://
            Returns the title and extracted text content.
            Use this when you need to read content from a web page.
            """,
        ),
    ]

    # Create LLM
    llm = ChatAnthropic(
        model="claude-3-5-sonnet-20241022", temperature=0
    )

    # Create prompt
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a helpful research assistant with access to a knowledge base.

You can:
1. Search the knowledge base for relevant information
2. Save new findings and insights
3. Fetch content from URLs

When searching, use specific queries. When you find useful information,
consider saving important insights for future reference.

Always cite your sources when providing information from the knowledge base.""",
            ),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    # Create agent
    agent = create_openai_functions_agent(llm, tools, prompt)

    # Create executor
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=5,
    )


def main():
    """Run example agent interactions."""
    # Initialize client
    client = RecallAPIClient(API_URL, API_TOKEN)

    # Create agent
    agent = create_recall_agent(client)

    # Example interactions
    examples = [
        "Search the knowledge base for information about transformers in deep learning",
        "Fetch content from https://arxiv.org/abs/1706.03762 and save key findings about the Transformer architecture",
        "What have I learned about attention mechanisms? Search the knowledge base.",
    ]

    print("🤖 LangChain Agent with Recall Notebook API\n")

    for example in examples:
        print(f"\n{'='*60}")
        print(f"User: {example}")
        print(f"{'='*60}\n")

        try:
            result = agent.invoke({"input": example})
            print(f"\nAgent: {result['output']}\n")
        except Exception as e:
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    main()
