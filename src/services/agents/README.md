# Agentic RAG Service

Think of the **Agentic RAG Service** as the "Brain" of this project. Instead of just doing a simple search and giving you an answer, it acts like a smart research assistant that thinks, checks its own work, and tries again if it fails.

We use **LangGraph** to build this assistant, which allows it to follow a flow-chart of steps (called "Nodes") to get you the best possible answer.

## How the "Brain" Works

Here is the step-by-step journey of your question:

### 1. The Gatekeeper (`guardrail_node`)
**What it does:** It checks if your question is actually about research papers.
**Value:** You don't want to waste time and computer power (tokens) answering "How do I make a cake?" in a philosophy and AI research assistant. If it's not related, it sends you to the default response and avoids calling the rest of the pipeline.

### 2. The Polite Rejection (`out_of_scope_node`)
**What it does:** If the gatekeeper says "No," this node explains why it can't answer and guides you back to relevant topics.
**Value:** It ensures the user understands the assistant's specific purpose.

### 3. The Librarian (`retrieve_node`)
**What it does:** It runs to the **OpenSearch** database and grabs the papers it thinks are most relevant to your question.
**Value:** It finds the raw material needed to answer your question.

### 4. The Fact-Checker (`grade_documents_node`)
**What it does:** It looks at the papers the librarian found and asks: "Do these actually answer the user's question?"
**Value:** Sometimes a search finds papers that mention your keywords but don't actually contain the answer. This step filters out the "junk" so the AI doesn't give you a wrong answer based on irrelevant info.

### 5. The Search Optimizer (`rewrite_query_node`)
**What it does:** If the fact-checker says "none of these papers are useful," this node takes your original question and rewrites it to be better for searching.
**Value:** If you ask a vague question, the AI realizes it and tries a more specific search automatically, without you having to ask again!

### 6. The Writer (`generate_answer_node`)
**What it does:** Finally, it takes the **good** papers and writes a clear, helpful response for you.
**Value:** It turns complex research into a simple answer you can actually use.

---

## Why is an "Agent" better than a normal RAG?

| Feature | Normal RAG | Agentic RAG (This Project) |
| :--- | :--- | :--- |
| **Logic** | Simple: Search -> Answer | Complex: Think -> Search -> Check -> Answer |
| **Mistakes** | Often answers based on irrelevant text | Fact-checks itself to avoid garbage answers |
| **Failure** | Gives up if the first search fails | Tries rephrasing the question and searching again |
| **Safety** | Answers anything (wastes resources) | Stays on topic using Guardrails |

## Technical Components

- **`agentic_rag.py`**: The "Map" that connects all these nodes together.
- **`state.py`**: The "Memory" of the assistant as it moves through the steps.
- **`tools.py`**: The "Skills" the assistant has (like the ability to search OpenSearch).
- **`context.py`**: Shared settings like which model to use and how strict to be.
