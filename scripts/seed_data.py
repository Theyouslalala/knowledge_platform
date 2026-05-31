"""Seed data for demo mode."""

DEMO_DOCUMENTS = [
    {
        "filename": "rag_introduction.txt",
        "content": """Retrieval-Augmented Generation (RAG) is a technique that combines
information retrieval with language generation. RAG systems retrieve relevant
documents from a knowledge base and use them as context for generating responses.

Key components of RAG:
1. Document Processing: Loading, parsing, and chunking documents
2. Embedding: Converting text chunks into vector representations
3. Vector Store: Storing and retrieving embeddings efficiently
4. Retrieval: Finding the most relevant chunks for a given query
5. Generation: Using retrieved context to generate accurate responses

Benefits of RAG:
- Reduces hallucination by grounding responses in real data
- Allows knowledge updates without retraining the model
- Provides source attribution for generated answers
- Works with domain-specific knowledge bases""",
    },
    {
        "filename": "multi_agent_systems.txt",
        "content": """Multi-agent systems involve multiple AI agents collaborating to solve complex tasks.

Common agent patterns:
1. Planner: Decomposes complex tasks into subtasks
2. Researcher: Gathers information from various sources
3. Analyst: Performs analysis and reasoning on gathered data
4. Writer: Synthesizes information into coherent responses
5. Critic: Evaluates output quality and suggests improvements

Reflection pattern:
- Agent generates an initial response
- Critic evaluates the response quality
- If quality is insufficient, the agent revises based on feedback
- This loop continues until quality threshold is met or max iterations reached

Communication patterns:
- Sequential: Agents work one after another
- Parallel: Agents work simultaneously on different aspects
- Hierarchical: Manager agent coordinates worker agents
- Blackboard: Agents share a common workspace""",
    },
    {
        "filename": "chunking_strategies.txt",
        "content": """Text chunking is a critical step in RAG pipeline design.

Fixed-Size Chunking:
- Splits text into chunks of uniform token count
- Simple and predictable
- May break sentences or paragraphs mid-thought
- Overlap between chunks preserves context

Recursive Chunking:
- Tries to split at natural boundaries (paragraphs, sentences)
- Falls back to smaller separators when chunks are too large
- Better semantic coherence than fixed-size
- Most commonly used in production

Semantic Chunking:
- Uses embeddings to detect topic boundaries
- Splits where semantic similarity drops
- Best semantic coherence
- More computationally expensive

Best practices:
- Chunk size: 256-512 tokens for most use cases
- Overlap: 10-20% of chunk size
- Consider the embedding model's context window
- Test different strategies on your specific data""",
    },
]


DEMO_TASKS = [
    {
        "title": "Explain RAG and its components",
        "description": "Provide a comprehensive explanation of Retrieval-Augmented Generation",
        "task_type": "research",
    },
    {
        "title": "Compare chunking strategies",
        "description": "Analyze and compare different text chunking approaches for RAG",
        "task_type": "analysis",
    },
    {
        "title": "Design a multi-agent workflow",
        "description": "Design an agent workflow for a research task",
        "task_type": "complex",
    },
]
