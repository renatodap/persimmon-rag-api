/**
 * TypeScript Agent using Recall Notebook API
 * Demonstrates RAG implementation in TypeScript/Node.js
 */

import Anthropic from "@anthropic-ai/sdk";

// Configuration
const API_URL = process.env.RECALL_API_URL || "https://your-app.railway.app";
const API_TOKEN = process.env.RECALL_API_TOKEN || "";
const ANTHROPIC_API_KEY = process.env.ANTHROPIC_API_KEY || "";

interface SearchResult {
  source: {
    id: string;
    title: string;
    content_type: string;
    original_content: string;
    url?: string;
    created_at: string;
  };
  summary: {
    summary_text: string;
    key_actions: string[];
    key_topics: string[];
    word_count: number;
  };
  relevance_score: number;
  match_type: "semantic" | "keyword" | "hybrid";
}

interface SearchResponse {
  results: SearchResult[];
  total: number;
  search_mode: string;
}

interface Source {
  source: {
    id: string;
    title: string;
    content_type: string;
    original_content: string;
    created_at: string;
  };
  summary: {
    id: string;
    summary_text: string;
    key_actions: string[];
    key_topics: string[];
    word_count: number;
  };
}

class RecallAPI {
  private apiUrl: string;
  private token: string;

  constructor(apiUrl: string, token: string) {
    this.apiUrl = apiUrl;
    this.token = token;
  }

  /**
   * Search the knowledge base
   */
  async search(
    query: string,
    mode: "semantic" | "keyword" | "hybrid" = "hybrid",
    limit: number = 10
  ): Promise<SearchResult[]> {
    const response = await fetch(`${this.apiUrl}/api/v1/search`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${this.token}`,
      },
      body: JSON.stringify({ query, mode, limit, threshold: 0.7 }),
    });

    if (!response.ok) {
      throw new Error(`Search failed: ${response.statusText}`);
    }

    const data: SearchResponse = await response.json();
    return data.results;
  }

  /**
   * Generate summary for content
   */
  async summarize(
    content: string,
    contentType: string = "text"
  ): Promise<{
    summary: string;
    key_actions: string[];
    topics: string[];
    word_count: number;
  }> {
    const response = await fetch(`${this.apiUrl}/api/v1/summarize`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${this.token}`,
      },
      body: JSON.stringify({ content, content_type: contentType }),
    });

    if (!response.ok) {
      throw new Error(`Summarization failed: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * Save source to knowledge base
   */
  async saveSource(
    title: string,
    content: string,
    summaryData: {
      summary: string;
      key_actions: string[];
      topics: string[];
      word_count: number;
    }
  ): Promise<Source> {
    const response = await fetch(`${this.apiUrl}/api/v1/sources`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${this.token}`,
      },
      body: JSON.stringify({
        title,
        content_type: "text",
        original_content: content,
        summary_text: summaryData.summary,
        key_actions: summaryData.key_actions,
        key_topics: summaryData.topics,
        word_count: summaryData.word_count,
      }),
    });

    if (!response.ok) {
      throw new Error(`Save failed: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * Fetch URL content
   */
  async fetchURL(url: string): Promise<{
    url: string;
    title: string;
    content: string;
    word_count: number;
  }> {
    const response = await fetch(`${this.apiUrl}/api/v1/fetch-url`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${this.token}`,
      },
      body: JSON.stringify({ url }),
    });

    if (!response.ok) {
      throw new Error(`URL fetch failed: ${response.statusText}`);
    }

    return await response.json();
  }
}

class RAGAgent {
  private api: RecallAPI;
  private claude: Anthropic;
  private conversationHistory: Array<{
    role: "user" | "assistant";
    content: string;
  }> = [];

  constructor(apiUrl: string, apiToken: string, anthropicKey: string) {
    this.api = new RecallAPI(apiUrl, apiToken);
    this.claude = new Anthropic({ apiKey: anthropicKey });
  }

  /**
   * Format search results as context
   */
  private formatContext(results: SearchResult[]): string {
    if (results.length === 0) {
      return "No relevant information found in knowledge base.";
    }

    return results
      .map(
        (r, i) =>
          `[Source ${i + 1}: ${r.source.title}]\n` +
          `${r.summary.summary_text}\n` +
          `Topics: ${r.summary.key_topics.join(", ")}\n` +
          `Relevance: ${r.relevance_score.toFixed(2)}`
      )
      .join("\n\n");
  }

  /**
   * Chat with RAG
   */
  async chat(userMessage: string, useRAG: boolean = true): Promise<string> {
    // Add to history
    this.conversationHistory.push({
      role: "user",
      content: userMessage,
    });

    // Search knowledge base if RAG enabled
    let context = "";
    if (useRAG) {
      console.log("🔍 Searching knowledge base...");
      const results = await this.api.search(userMessage, "hybrid", 5);
      context = this.formatContext(results);
      console.log(`✅ Found ${results.length} relevant sources\n`);
    }

    // Build system prompt
    let systemPrompt =
      "You are a helpful research assistant with access to a knowledge base.\n\n" +
      "When answering:\n" +
      "1. Use context from the knowledge base when relevant\n" +
      "2. Cite sources by title\n" +
      "3. Be honest if information is not available\n" +
      "4. Provide accurate and helpful answers";

    if (context) {
      systemPrompt += `\n\nRelevant context:\n${context}`;
    }

    // Get Claude response
    console.log("💭 Thinking...");
    const response = await this.claude.messages.create({
      model: "claude-3-5-sonnet-20241022",
      max_tokens: 2048,
      system: systemPrompt,
      messages: this.conversationHistory,
    });

    const assistantMessage = response.content[0].text;

    // Add to history
    this.conversationHistory.push({
      role: "assistant",
      content: assistantMessage,
    });

    return assistantMessage;
  }

  /**
   * Ingest URL into knowledge base
   */
  async ingestURL(url: string): Promise<Source> {
    console.log(`📥 Fetching ${url}...`);

    // Fetch content
    const content = await this.api.fetchURL(url);
    console.log(`✅ Fetched: ${content.title}`);

    // Summarize
    console.log("📝 Summarizing...");
    const summary = await this.api.summarize(content.content, "url");

    // Save
    console.log("💾 Saving to knowledge base...");
    const source = await this.api.saveSource(content.title, content.content, summary);

    console.log(`✅ Saved: ${source.source.id}\n`);

    return source;
  }

  /**
   * Research a topic with multiple searches
   */
  async research(topic: string, maxIterations: number = 3): Promise<string> {
    console.log(`📚 Researching: ${topic}\n`);

    const allResults: SearchResult[] = [];
    let currentQuery = topic;

    for (let i = 0; i < maxIterations; i++) {
      console.log(`🔍 Iteration ${i + 1}: Searching for '${currentQuery}'`);

      const results = await this.api.search(currentQuery, "hybrid", 3);
      allResults.push(...results);

      if (results.length === 0) {
        console.log("   No results found.\n");
        break;
      }

      console.log(`   Found ${results.length} results\n`);

      // Ask Claude if we need more info
      const context = this.formatContext(results);
      const decision = await this.claude.messages.create({
        model: "claude-3-5-sonnet-20241022",
        max_tokens: 300,
        messages: [
          {
            role: "user",
            content:
              `Context:\n${context}\n\n` +
              `Topic: ${topic}\n\n` +
              `Do we have enough info? Reply with:\n` +
              `- "SUFFICIENT" if yes\n` +
              `- "SEARCH: <query>" if we need more`,
          },
        ],
      });

      const text = decision.content[0].text.trim();

      if (text.startsWith("SUFFICIENT")) {
        console.log("✅ Sufficient information gathered\n");
        break;
      } else if (text.startsWith("SEARCH:")) {
        currentQuery = text.replace("SEARCH:", "").trim();
        console.log(`💡 Next search: ${currentQuery}\n`);
      } else {
        break;
      }
    }

    // Generate final summary
    console.log("📝 Generating research summary...\n");

    const allContext = this.formatContext(allResults);
    const summary = await this.claude.messages.create({
      model: "claude-3-5-sonnet-20241022",
      max_tokens: 3000,
      messages: [
        {
          role: "user",
          content:
            `Research context:\n${allContext}\n\n` +
            `Topic: ${topic}\n\n` +
            `Provide a comprehensive summary with:\n` +
            `1. Key findings\n` +
            `2. Important concepts\n` +
            `3. Knowledge gaps\n` +
            `4. Further research suggestions`,
        },
      ],
    });

    return summary.content[0].text;
  }
}

// Example usage
async function main() {
  const agent = new RAGAgent(API_URL, API_TOKEN, ANTHROPIC_API_KEY);

  console.log("🤖 TypeScript RAG Agent with Recall Notebook API\n");
  console.log("=".repeat(60));

  try {
    // Example 1: Simple chat with RAG
    console.log("\n📌 Example 1: RAG Chat\n");
    const response = await agent.chat(
      "What are transformers in deep learning?",
      true
    );
    console.log(`\nAgent: ${response}\n`);

    // Example 2: Research topic
    console.log("\n" + "=".repeat(60));
    console.log("\n📌 Example 2: Research Topic\n");
    const research = await agent.research("attention mechanisms in neural networks");
    console.log(`\nResearch Summary:\n${research}\n`);

    // Example 3: Ingest URL
    // console.log("\n" + "=".repeat(60));
    // console.log("\n📌 Example 3: Ingest URL\n");
    // const source = await agent.ingestURL("https://arxiv.org/abs/1706.03762");
    // console.log(`Source ID: ${source.source.id}\n`);

  } catch (error) {
    console.error("Error:", error);
  }
}

// Run if executed directly
if (require.main === module) {
  main().catch(console.error);
}

export { RAGAgent, RecallAPI };
