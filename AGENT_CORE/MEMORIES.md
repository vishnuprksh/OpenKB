# Strategic Memories

### [2026-05-02] - Core Architecture: Compilation Model
- **Context**: Understanding OpenKB's fundamental design vs traditional RAG
- **Key Decision**: OpenKB compiles knowledge once, queries many times (vs RAG's re-retrieval per query)
- **Why It Matters**: Affects UI design — not real-time search UI, but static wiki browser + navigation
- **Implication**: UI should focus on browsing compiled wiki + starting new queries, not live search

### [2026-05-02] - Document Type Branching
- **Context**: System treats documents differently based on page count
- **Pattern**: PDF < 20 pages → direct compilation; PDF ≥ 20 pages → PageIndex indexing
- **For UI**: Need separate handling for "short" vs "indexed" documents in visualization
- **Technical Detail**: Long docs stored as pages/{}.json, short docs as single .md file

### [2026-05-02] - Agent Tool Architecture
- **Context**: Query/chat agents use a tool-use loop, not pre-defined search queries
- **Tools Available**: read_file, get_page_content, get_image (agents decide which to call)
- **For UI**: Show tool calls in real-time + reasoning. Agent iterates up to 50 times before giving up
- **Key Feature**: Transparent reasoning loop is important for user trust

### [2026-05-02] - File-Based Storage = Filesystem as Database
- **Context**: All data stored as Markdown/JSON files, not a relational database
- **Advantage**: Real-time file watching, grep-based search, Obsidian compatibility
- **For UI**: Can directly parse Markdown files without ORM; enables file-watching for external edits
- **Constraint**: No transactions; must be careful with concurrent writes

### [2026-05-02] - Hash-Based Deduplication
- **Pattern**: Files tracked by SHA-256 hash in .openkb/hashes.json, not filename
- **For UI**: User can rename/move files and system still recognizes them (no reprocessing)
- **Edge Case**: Identical files trigger skip (feature, not bug)

### [2026-05-02] - Prompt Caching for Cost Reduction
- **Pattern**: Compilation uses LLM prompt caching (schema + doc content cached once)
- **Cost Impact**: First call full price; subsequent calls 90% cheaper if cache hits (5 min lifetime)
- **For UI**: Can show cost estimates; batch compilation for same-session efficiency

### [2026-05-02] - Session Persistence Without Long-Term Agent Memory
- **Context**: Chat sessions persisted as JSON, but agent SDK is stateless
- **Pattern**: History loaded into agent each turn (no agent memory between turns)
- **For UI**: Sessions manually managed by app, not by agent SDK
- **Implication**: Can't rely on agent's internal state across sessions

### [2026-05-02] - PageIndex as Vectorless Indexing Alternative
- **Innovation**: Long docs indexed via PageIndex (tree structure) instead of vector DB
- **Benefit**: No embedding costs; tree-based retrieval precise; supports page ranges
- **For UI**: Can show document structure (TOC) and highlight relevant sections
- **Data Stored**: Cached at .openkb/pageindex/{doc_id}.json

### [2026-05-02] - Image Handling Split Between Short & Long Docs
- **Short Docs**: Images extracted from base64, saved to wiki/sources/images/{doc}/
- **Long Docs**: Images per-page, included in PageIndex pages/{}.json
- **For UI**: Different strategies to display images for each type

### [2026-05-02] - Lint Has Two Flavors: Structural + Knowledge
- **Structural Lint**: Broken links, orphans, missing entries (filesystem-based, fast)
- **Knowledge Lint**: Contradictions, gaps, stale content (LLM-based, slow)
- **For UI**: Show both in health check; mark LLM-based as "in progress"
- **Reporting**: Lint reports saved to wiki/reports/lint_{timestamp}.md
