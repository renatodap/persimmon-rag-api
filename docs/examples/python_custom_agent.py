"""
Custom RAG Agent using Recall Notebook API
Demonstrates building an agent from scratch without frameworks
"""
import asyncio
import os
from typing import List, Dict, Optional

import httpx
from anthropic import Anthropic

# Configuration
API_URL = os.getenv("RECALL_API_URL", "https://your-app.railway.app")
API_TOKEN = os.getenv("RECALL_API_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")


class SimpleRAGAgent:
    """
    Custom RAG agent using Recall Notebook API for knowledge retrieval.
    """

    def __init__(self, api_url: str, api_token: str, anthropic_key: str):
        self.api_url = api_url
        self.api_token = api_token
        self.headers = {"Authorization": f"Bearer {api_token}"}
        self.claude = Anthropic(api_key=anthropic_key)
        self.conversation_history = []

    async def search_knowledge(
        self, query: str, mode: str = "hybrid", limit: int = 5
    ) -> List[Dict]:
        """
        Search the knowledge base.

        Args:
            query: Search query
            mode: Search mode
            limit: Max results

        Returns:
            List of search results
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/api/v1/search",
                json={"query": query, "mode": mode, "limit": limit},
                headers=self.headers,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()["results"]

    async def save_source(self, title: str, content: str) -> Dict:
        """
        Save content to knowledge base with AI summarization.

        Args:
            title: Document title
            content: Document content

        Returns:
            Created source
        """
        async with httpx.AsyncClient() as client:
            # Summarize first
            summary_response = await client.post(
                f"{self.api_url}/api/v1/summarize",
                json={"content": content, "content_type": "text"},
                headers=self.headers,
                timeout=60.0,
            )
            summary_response.raise_for_status()
            summary = summary_response.json()

            # Save source
            source_response = await client.post(
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
            return source_response.json()

    def format_context(self, results: List[Dict]) -> str:
        """
        Format search results into context for Claude.

        Args:
            results: Search results from API

        Returns:
            Formatted context string
        """
        if not results:
            return "No relevant information found in knowledge base."

        context_parts = []
        for i, r in enumerate(results, 1):
            context_parts.append(
                f"[Source {i}: {r['source']['title']}]\n"
                f"{r['summary']['summary_text']}\n"
                f"Key topics: {', '.join(r['summary']['key_topics'])}\n"
                f"Relevance: {r['relevance_score']:.2f}"
            )

        return "\n\n".join(context_parts)

    async def chat(self, user_message: str, use_rag: bool = True) -> str:
        """
        Chat with the agent.

        Args:
            user_message: User's message
            use_rag: Whether to use RAG (search knowledge base)

        Returns:
            Agent's response
        """
        # Add user message to history
        self.conversation_history.append({"role": "user", "content": user_message})

        # Retrieve context if RAG is enabled
        context = ""
        if use_rag:
            print("🔍 Searching knowledge base...")
            results = await self.search_knowledge(user_message, limit=5)
            context = self.format_context(results)
            print(f"✅ Found {len(results)} relevant sources\n")

        # Build system prompt
        system_prompt = """You are a helpful research assistant with access to a knowledge base.

When answering questions:
1. Use information from the provided context when relevant
2. Cite sources by mentioning the source title
3. Be honest if the information is not in the context
4. Provide helpful and accurate answers

If you learn something new or important during the conversation, suggest saving it to the knowledge base."""

        if context:
            system_prompt += f"\n\nRelevant context from knowledge base:\n{context}"

        # Get response from Claude
        print("💭 Thinking...")
        response = self.claude.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            system=system_prompt,
            messages=self.conversation_history,
        )

        assistant_message = response.content[0].text

        # Add to history
        self.conversation_history.append(
            {"role": "assistant", "content": assistant_message}
        )

        return assistant_message

    async def multi_hop_research(
        self, topic: str, max_iterations: int = 3
    ) -> str:
        """
        Conduct multi-hop research on a topic.

        Args:
            topic: Research topic
            max_iterations: Max search iterations

        Returns:
            Research summary
        """
        print(f"📚 Starting multi-hop research on: {topic}\n")

        all_results = []
        current_query = topic

        for iteration in range(max_iterations):
            print(f"🔍 Iteration {iteration + 1}: Searching for '{current_query}'")

            # Search knowledge base
            results = await self.search_knowledge(current_query, limit=3)
            all_results.extend(results)

            if not results:
                print("   No more results found.\n")
                break

            print(f"   Found {len(results)} results\n")

            # Use Claude to analyze and generate next query
            context = self.format_context(results)

            response = self.claude.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Context from knowledge base:
{context}

Original research topic: {topic}

Based on this context, determine:
1. Do we have enough information to answer comprehensively?
2. If not, what specific aspect should we search for next?

Reply with either:
- "SUFFICIENT" if we have enough information
- "SEARCH: <refined query>" if we need more specific information""",
                    }
                ],
            )

            decision = response.content[0].text.strip()

            if decision.startswith("SUFFICIENT"):
                print("✅ Sufficient information gathered\n")
                break
            elif decision.startswith("SEARCH:"):
                current_query = decision.replace("SEARCH:", "").strip()
                print(f"💡 Next search: {current_query}\n")
            else:
                break

        # Generate final research summary
        print("📝 Generating research summary...\n")

        all_context = self.format_context(all_results)

        final_response = self.claude.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=3000,
            messages=[
                {
                    "role": "user",
                    "content": f"""Based on this research context:

{all_context}

Topic: {topic}

Please provide a comprehensive research summary including:
1. Key findings
2. Important concepts
3. Gaps in current knowledge
4. Suggestions for further research

Format as a well-structured research report.""",
                }
            ],
        )

        return final_response.content[0].text


async def main():
    """Run example agent interactions."""
    agent = SimpleRAGAgent(API_URL, API_TOKEN, ANTHROPIC_API_KEY)

    print("🤖 Custom RAG Agent with Recall Notebook API\n")
    print("="*60)

    # Example 1: Simple RAG chat
    print("\n📌 Example 1: Simple RAG Chat\n")
    response = await agent.chat(
        "What are transformers in deep learning?",
        use_rag=True
    )
    print(f"\nAgent: {response}\n")

    # Example 2: Multi-hop research
    print("\n" + "="*60)
    print("\n📌 Example 2: Multi-Hop Research\n")
    research_summary = await agent.multi_hop_research(
        "transformer architecture and attention mechanisms"
    )
    print(f"\nResearch Summary:\n{research_summary}\n")

    # Example 3: Save new knowledge
    print("\n" + "="*60)
    print("\n📌 Example 3: Save Research Findings\n")
    source = await agent.save_source(
        title="Research Summary: Transformers",
        content=research_summary
    )
    print(f"✅ Saved: {source['source']['id']}\n")


if __name__ == "__main__":
    asyncio.run(main())
