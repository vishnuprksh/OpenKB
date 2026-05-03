# OpenKB Project Overview

**North Star**: Build a comprehensive understanding of OpenKB codebase to enable UI development.

**Core Architecture**: 
- LLM-powered document compilation system
- File-based wiki storage (Markdown + JSON)
- Vectorless indexing via PageIndex for long documents
- Agent-based Q&A with tool-use (read_file, get_page_content, get_image)
- Multi-turn chat with session persistence

**Core Components**:
1. **Input Pipeline**: Document conversion + hashing + deduplication
2. **Indexing**: PageIndex for long PDFs (tree-based, vectorless)
3. **Compilation**: LLM generates summaries + concepts + cross-links
4. **Retrieval**: Agent-based navigation with tools
5. **Storage**: Filesystem (Markdown files + JSON for structure)
6. **Maintenance**: Linting (structural + knowledge-based)

**Key Tech Stack**:
- Python 3.10+
- LiteLLM (multi-model LLM support)
- PageIndex (long document indexing)
- MarkItDown (document conversion)
- Prompt Toolkit (CLI UI)
- Agents SDK (agentic loop)

**Guiding Principles**: 
- Simple, direct implementations
- Minimal abstractions
- File-based (no database)
- LLM-driven (compile once, query many times)

**Constraints**:
- No external database (filesystem-based)
- Stateless agents (no long-term memory in agent SDK)
- LLM API key required (external dependency)
- Async operations for scalability
