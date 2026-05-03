# OpenKB: Complete Technical Tutorial

**Purpose**: This tutorial explains the entire OpenKB system—its architecture, workflows, file operations, and LLM integration—to help you build a UI for it.

**Last Updated**: May 2, 2026

---

## Table of Contents

1. [Vision & Philosophy](#vision--philosophy)
2. [High-Level Architecture](#high-level-architecture)
3. [Directory Structure & Data Model](#directory-structure--data-model)
4. [Core Modules Explained](#core-modules-explained)
5. [Data Flow Workflows](#data-flow-workflows)
6. [CLI Commands & User Interactions](#cli-commands--user-interactions)
7. [Configuration & State Management](#configuration--state-management)
8. [LLM Integration & Prompting](#llm-integration--prompting)
9. [Image & Document Handling](#image--document-handling)
10. [Example: Complete Document Add Flow](#example-complete-document-add-flow)
11. [Key Concepts for UI Development](#key-concepts-for-ui-development)

---

## Vision & Philosophy

### What is OpenKB?

**OpenKB** (Open Knowledge Base) is an LLM-powered system that transforms raw documents into a **structured, self-managing wiki**. Instead of traditional RAG (Retrieval-Augmented Generation) that re-discovers knowledge on every query, OpenKB:

1. **Ingests** documents once (PDFs, Word, Markdown, etc.)
2. **Converts** them to Markdown with extracted images
3. **Indexes** long documents using PageIndex (vectorless tree indexing)
4. **Compiles** them into summaries and concept pages using LLM
5. **Cross-links** documents with `[[wikilinks]]`
6. **Queries** the compiled wiki intelligently using LLM agents
7. **Maintains** knowledge health via linting and updates

### Key Innovation: Compilation, Not Retrieval

Traditional RAG:
```
Query → Search vectors → Find chunks → Ask LLM → Answer
(Repeats for every query; no accumulation)
```

OpenKB:
```
Document → Convert → Index → Compile (once) → Wiki
Query → Navigate compiled wiki → Ask LLM → Answer
(Knowledge compounds; cross-references exist; synthesis reflects all documents)
```

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     INPUT DOCUMENTS                         │
│        (PDF, Word, Markdown, HTML, Excel, etc.)            │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────▼─────────────┐
        │  DOCUMENT CONVERTER      │
        │  (markitdown + pymupdf)  │
        │  • Hash check            │
        │  • Image extraction      │
        │  • Markdown generation   │
        └────────────┬─────────────┘
                     │
        ┌────────────▼─────────────────────────────────┐
        │  DOCUMENT TYPE DETECTION                    │
        │  • Short docs → Direct compilation          │
        │  • Long PDFs (≥20 pages) → PageIndex index  │
        └────────────┬─────────────────────────────────┘
                     │
      ┌──────────────┴──────────────┐
      │                             │
  ┌───▼────────────┐        ┌──────▼──────────┐
  │  SHORT DOCS    │        │  LONG DOCS      │
  │  Compile       │        │  PageIndex →    │
  │  directly      │        │  Compile        │
  └───┬────────────┘        └──────┬──────────┘
      │                             │
      └──────────────┬──────────────┘
                     │
        ┌────────────▼─────────────┐
        │  LLM COMPILATION         │
        │  • Write summary         │
        │  • Plan concepts         │
        │  • Generate concepts     │
        │  • Add cross-refs        │
        │  • Update index.md       │
        └────────────┬─────────────┘
                     │
        ┌────────────▼─────────────┐
        │  WIKI (Markdown files)   │
        │  • sources/              │
        │  • summaries/            │
        │  • concepts/             │
        │  • index.md              │
        └────────────┬─────────────┘
                     │
      ┌──────────────┴──────────────┐
      │                             │
  ┌───▼──────────┐          ┌──────▼──────┐
  │  QUERY       │          │  CHAT       │
  │  One-shot    │          │  Multi-turn │
  │  Q&A         │          │  Sessions   │
  └──────────────┘          └─────────────┘
```

---

## Directory Structure & Data Model

### Knowledge Base Layout

```
my-kb/                          # Knowledge base root
├── raw/                         # User-provided documents
│   ├── paper.pdf
│   ├── notes.md
│   └── data.xlsx
│
├── wiki/                        # Compiled knowledge base
│   ├── AGENTS.md               # Schema & instructions (don't modify)
│   ├── index.md                # Index of all pages (auto-maintained)
│   ├── log.md                  # Append-only operation log
│   │
│   ├── sources/                # Document content (auto-generated)
│   │   ├── paper.md            # Short doc converted to markdown
│   │   ├── notes.json          # Long doc: page-by-page content
│   │   └── images/             # Extracted images
│   │       ├── paper/
│   │       │   ├── p1_img1.png
│   │       │   └── p2_img2.png
│   │       └── notes/
│   │
│   ├── summaries/              # Summary pages (one per source doc)
│   │   ├── paper.md            # Summary + frontmatter with metadata
│   │   └── notes.md
│   │
│   ├── concepts/               # Cross-document concept pages
│   │   ├── attention.md
│   │   └── transformer.md
│   │
│   ├── explorations/           # Saved query results
│   │   └── how-does-attention-work.md
│   │
│   └── reports/                # Lint health check reports
│       └── lint_20260502_123456.md
│
└── .openkb/                     # State directory (hidden)
    ├── config.yaml             # KB-level config (model, language, etc)
    ├── hashes.json             # Registry of file SHA-256 hashes
    ├── pageindex/              # PageIndex cached data
    │   └── doc_123.json        # Cached PageIndex tree for long doc
    └── chats/                  # Chat session persistence
        ├── 20260502-123456-abc.json
        └── 20260502-134517-xyz.json
```

### Data Files Explained

#### **index.md** (Auto-maintained)
Lists all documents and concepts with one-liner summaries:
```markdown
# Knowledge Base Index

## Documents
- [paper](summaries/paper.md) — Attention mechanisms in neural networks (short)
- [notes](summaries/notes.md) — Quick reference on transformers (short)

## Concepts
- [attention](concepts/attention.md) — Mechanism for focusing on relevant inputs
- [transformer](concepts/transformer.md) — Architecture using attention layers

## Explorations
- [how-does-attention-work](explorations/how-does-attention-work.md) — Q&A on attention
```

#### **sources/{doc}.md** (Short documents)
Raw Markdown converted from the original document:
```markdown
# Paper Title

This is the content converted to Markdown.

![Diagram](images/paper/p1_img1.png)

References: [concept/attention]
```

#### **sources/{doc}.json** (Long documents via PageIndex)
Per-page content from PageIndex indexing:
```json
{
  "pages": [
    {
      "page_num": 1,
      "content": "Introduction...",
      "images": ["images/paper/p1_img1.png"]
    },
    {
      "page_num": 2,
      "content": "Background...",
      "images": []
    }
  ]
}
```

#### **summaries/{doc}.md** (Generated by LLM)
Frontmatter + summary + concept links:
```markdown
---
doc_type: short
doc_name: paper
brief: "Introduces attention mechanisms..."
full_text: sources/paper.md
---

# Paper Summary

## Key Findings
- Attention allows models to focus on relevant inputs
- Enables parallel computation vs RNNs

## Related Concepts
- [[concepts/attention]]
- [[concepts/transformer]]
```

#### **concepts/{concept}.md** (Generated by LLM)
Cross-document synthesis with references:
```markdown
# Attention Mechanism

Attention is a mechanism that allows models to focus on specific parts of input.

## In Transformers
From [[summaries/paper]], attention is used in multi-head form...

## Historical Context
Early work on attention in [[summaries/seq2seq-paper]]...

## Applications
Used in NLP, vision, and multimodal models.
```

#### **log.md** (Append-only)
Chronological record of all operations:
```markdown
# Operations Log

## [2026-05-02 10:23:45] ingest | paper.pdf
## [2026-05-02 10:25:30] query | What is attention?
## [2026-05-02 10:26:15] lint | Structural + knowledge health
```

---

## Core Modules Explained

### 1. **converter.py** — Document Conversion
**Purpose**: Transform raw files into standardized Markdown with extracted images.

**Key Functions**:
- `convert_document(src: Path, kb_dir: Path) → ConvertResult`
  - Hash-checks file (skip if already known)
  - Copies to `raw/` directory
  - Detects if PDF is "long" (≥20 pages threshold)
  - Converts to Markdown (uses markitdown or pymupdf)
  - Extracts and saves base64 images separately
  - Registers file hash for deduplication

**Key Classes**:
- `ConvertResult`: Dataclass with:
  - `raw_path`: Path to copied file in raw/
  - `source_path`: Path to converted Markdown in wiki/sources/
  - `is_long_doc`: Boolean (long PDFs need PageIndex)
  - `skipped`: Already processed
  - `file_hash`: SHA-256 for deduplication

**Document Support**:
- Short docs: PDF, Word, Markdown, HTML, Excel, plain text, CSV, PowerPoint
- Long docs: PDFs ≥20 pages (via PageIndex)
- Images: Extracted and saved relative to document

---

### 2. **state.py** — Hash Registry
**Purpose**: Track processed files to prevent reprocessing.

**Key Class**: `HashRegistry`
- Persistent JSON file at `.openkb/hashes.json`
- Maps SHA-256 hash → metadata dict
- Methods:
  - `is_known(hash)`: Check if file processed
  - `add(hash, metadata)`: Register new file
  - `all_entries()`: Get all processed files
  - `hash_file(path)`: Static method to compute SHA-256

**Why it matters**: Prevents duplicate compilation; enables efficient re-indexing

---

### 3. **indexer.py** — PageIndex Integration
**Purpose**: Index long PDFs using PageIndex (vectorless, tree-based retrieval).

**Key Function**: `index_long_document(pdf_path: Path, kb_dir: Path) → IndexResult`

**Process**:
1. Initialize PageIndex client with OpenKB's LLM model
2. Add PDF to PageIndex collection (retries up to 3 times)
3. Retrieve doc metadata: name, description, structure (TOC)
4. Convert PDF to pages (either via cloud or local pymupdf)
5. Write pages to `wiki/sources/{doc}.json` (one entry per page)
6. Return `IndexResult` with doc_id, description, structure

**Key Classes**:
- `IndexResult`: Contains:
  - `doc_id`: PageIndex document identifier
  - `description`: Auto-generated document summary
  - `tree`: Document structure (TOC with page ranges)

**Page Content Retrieval** (used during query):
- Cloud mode (with PAGEINDEX_API_KEY): Fetch OCR'd pages
- Local mode: Fall back to pymupdf extraction

---

### 4. **images.py** — Image Handling
**Purpose**: Extract images from documents and save them locally.

**Key Functions**:
- `extract_base64_images(markdown: str, images_dir: Path) → str`
  - Finds base64 images in Markdown
  - Decodes and saves as PNG files
  - Updates Markdown to reference local files

- `copy_relative_images(markdown: str, src_dir: Path, doc_name: str, images_dir: Path) → str`
  - Copies images referenced in Markdown (relative paths)
  - Updates references to point to wiki/sources/images/

- `convert_pdf_with_images(pdf_path: Path) → str`
  - Uses pymupdf to extract text + images from PDF
  - Returns Markdown with embedded images

---

### 5. **agent/compiler.py** — LLM Compilation Pipeline
**Purpose**: Convert document content into wiki summaries and concepts using LLM.

**Pipeline Overview**:
```
1. Build context:
   - Schema (wiki structure rules)
   - Document name, content
   - Language setting

2. Generate summary:
   - LLM writes brief (1-liner)
   - LLM writes summary (key concepts, findings)

3. Concept planning:
   - LLM decides which concepts to create/update/relate
   - Based on existing concept pages

4. Generate concepts (concurrent):
   - Create new concept pages
   - Update existing concept pages with new info
   - Add cross-reference links

5. Update index.md:
   - Add summaries to "Documents" section
   - Add new concepts to "Concepts" section
```

**Key Functions**:
- `compile_short_doc(doc_name: str, source_path: Path, kb_dir: Path, model: str)`
  - For short documents (converted directly)
  - Reads full markdown content
  - Calls compilation pipeline

- `compile_long_doc(doc_name: str, summary_path: Path, doc_id: str, kb_dir: Path, model: str, ...)`
  - For long documents (indexed via PageIndex)
  - Retrieves metadata from PageIndex (description, structure)
  - Calls compilation pipeline with page range hints

**LLM Prompting** (with caching):
- System: Schema definition (wiki rules, link format, language)
- User step 1: "Write a summary"
- User step 2: "Plan which concepts to create/update"
- User steps 3-4: "Generate new/updated concept pages" (parallel)

**Prompt Caching**:
- Base context (schema + doc content) cached once
- Subsequent LLM calls reuse cache (cheaper, faster)

---

### 6. **agent/query.py** — Q&A Agent
**Purpose**: Answer questions by intelligently searching the compiled wiki.

**Function**: `build_query_agent(wiki_root: str, model: str, language: str) → Agent`

**Agent Strategy**:
1. Read `index.md` to see all documents and concepts
2. Search relevant summary pages (`summaries/`)
3. Read concept pages (`concepts/`) for cross-document info
4. Fetch detailed source content when needed
5. Synthesize answer with citations

**Tools Available**:
- `read_file(path)`: Read Markdown from wiki
- `get_page_content(doc_name, pages)`: Fetch specific pages from long doc
- `get_image(image_path)`: View images referenced in content

**Key Classes**:
- `Agent` (from openai-agents SDK): Manages tool-use loop
- Tools return text or images; agent iterates until answering

---

### 7. **agent/chat_session.py** — Chat State Management
**Purpose**: Persist multi-turn conversations across sessions.

**Data Structure**: JSON file at `.openkb/chats/{id}.json`
```json
{
  "id": "20260502-123456-abc",
  "title": "Questions about attention",
  "created_at": "2026-05-02T10:23:45Z",
  "updated_at": "2026-05-02T10:26:15Z",
  "turn_count": 3,
  "history": [
    {"role": "user", "content": "What is attention?"},
    {"role": "assistant", "content": "Attention is..."}
  ]
}
```

**Key Functions**:
- `ChatSession.new(kb_dir, model, language)`: Create new session
- `ChatSession.save()`: Persist to disk
- `load_session(kb_dir, id)`: Load from disk
- `list_sessions(kb_dir)`: List all sessions
- `delete_session(kb_dir, id)`: Delete a session

**Image Handling**:
- Large base64 images replaced with lightweight references
- Prevents bloating session files
- Agent can call `get_image()` again if needed

---

### 8. **agent/chat.py** — Interactive Chat REPL
**Purpose**: Run multi-turn chat with rich terminal UI.

**Features**:
- Prompt history and editing (via prompt_toolkit)
- Colored output (query agent, tool calls, responses)
- Slash commands:
  - `/exit`: Exit chat
  - `/clear`: Start fresh session
  - `/save [name]`: Export to explorations/
  - `/status`: Show KB status
  - `/list`: List all documents
  - `/lint`: Run linting
  - `/add <path>`: Add documents
  - `/help`: Show help

**Flow**:
1. Create or resume session
2. Loop: Get user input → Run agent → Stream response
3. On exit, persist session

---

### 9. **lint.py** & **agent/linter.py** — Health Checks
**Purpose**: Detect and report wiki issues.

**Structural Lint** (lint.py):
- Broken `[[wikilinks]]`: Links pointing to non-existent pages
- Orphaned pages: Pages with no incoming/outgoing links
- Missing entries: raw files without corresponding summaries
- Index sync: index.md links vs actual files

**Knowledge Lint** (agent/linter.py):
- Uses LLM to check for:
  - Contradictions between concepts
  - Missing explanations
  - Stale content
  - Redundancy

**Output**: Lint report written to `wiki/reports/lint_{timestamp}.md`

---

### 10. **watcher.py** — Auto-Processing
**Purpose**: Watch `raw/` directory and auto-process new files.

**Key Class**: `DebouncedHandler`
- Watches for file creation/modification
- Debounces rapid bursts (waits 2s after last event)
- Calls callback with sorted list of paths
- Ignores directories and hidden files

**Use Case**: `openkb watch` command monitors raw/ and auto-runs `add`

---

### 11. **config.py** — Configuration Management
**Purpose**: Load/save configuration at KB and global levels.

**Files**:
- KB-level: `.openkb/config.yaml` (per knowledge base)
- Global: `~/.config/openkb/global.yaml` (system-wide settings)

**Config Keys**:
- `model`: LLM to use (e.g., "gpt-5.4", "anthropic/claude-sonnet-4-6")
- `language`: Output language (default: "en")
- `pageindex_threshold`: Page count for "long doc" classification (default: 20)

**API Key Management**:
- Checked in order:
  1. Environment variable `LLM_API_KEY`
  2. KB-local `.env` file
  3. Global `~/.config/openkb/.env`
  4. Provider-specific variables (OPENAI_API_KEY, etc.)

---

### 12. **log.py** — Append-only Logging
**Purpose**: Record all KB operations for audit trail.

**Function**: `append_log(wiki_dir: Path, operation: str, description: str)`

**Operations**:
- `ingest`: Document added
- `query`: Question asked
- `lint`: Health check run

**Format**: `## [YYYY-MM-DD HH:MM:SS] operation | description`

---

### 13. **cli.py** — Command-Line Interface
**Purpose**: User-facing commands for all workflows.

**Commands**:
- `openkb init`: Initialize new KB
- `openkb add <path>`: Add documents
- `openkb query <question>`: One-shot Q&A
- `openkb chat`: Interactive multi-turn chat
- `openkb watch`: Auto-process files from raw/
- `openkb lint`: Check KB health
- `openkb use <path>`: Set default KB

---

## Data Flow Workflows

### Workflow 1: Adding a Document

```
User runs: openkb add paper.pdf
│
├─ 1. find_kb_dir()
│    └─ Locate .openkb/ (walk up tree or global default)
│
├─ 2. convert_document(paper.pdf, kb_dir)
│    ├─ Hash file (SHA-256)
│    ├─ Skip if hash already in registry
│    ├─ Copy to raw/
│    ├─ Detect if long (≥20 pages)
│    ├─ Convert to Markdown (markitdown or pymupdf)
│    ├─ Extract images
│    └─ Return ConvertResult
│
├─ 3. If long PDF:
│    │
│    ├─ index_long_document(raw_path, kb_dir)
│    │  ├─ Init PageIndex client
│    │  ├─ Add PDF to PageIndex
│    │  ├─ Retrieve doc metadata, structure
│    │  ├─ Fetch/convert pages
│    │  ├─ Write wiki/sources/{doc}.json
│    │  └─ Return IndexResult
│    │
│    └─ compile_long_doc(doc_name, summary_path, doc_id, kb_dir, model)
│
│   Else (short document):
│    └─ compile_short_doc(doc_name, source_path, kb_dir, model)
│
├─ 4. Compilation Pipeline (both paths):
│    │
│    ├─ Build context:
│    │  ├─ Load schema (AGENTS.md)
│    │  ├─ Load document content (from sources/)
│    │  └─ Load config (model, language)
│    │
│    ├─ LLM Call 1: Generate Summary
│    │  └─ Write summaries/{doc}.md with brief + content
│    │
│    ├─ LLM Call 2: Plan Concepts
│    │  └─ Decide which concepts to create/update
│    │
│    ├─ LLM Calls 3-N: Generate Concepts (parallel)
│    │  ├─ Create new concepts/
│    │  ├─ Update existing concepts/
│    │  └─ Add cross-refs (wikilinks)
│    │
│    └─ Update index.md
│       ├─ Add document to ## Documents
│       └─ Add new concepts to ## Concepts
│
├─ 5. Register hash
│    └─ Add to .openkb/hashes.json (prevent reprocessing)
│
├─ 6. Append log
│    └─ Add entry to wiki/log.md
│
└─ Display: [OK] {filename} added to knowledge base.
```

**Files Modified**:
- `raw/{filename}` — Copied input
- `wiki/sources/{doc}.md` or `.json` — Converted content
- `wiki/sources/images/{doc}/` — Extracted images
- `wiki/summaries/{doc}.md` — Generated summary (frontmatter + content)
- `wiki/concepts/` — Generated/updated concept pages
- `wiki/index.md` — Updated catalog
- `wiki/log.md` — Appended operation
- `.openkb/hashes.json` — Registered hash

---

### Workflow 2: Querying the Knowledge Base

```
User runs: openkb query "What is attention?"
│
├─ 1. find_kb_dir() & load_config()
│
├─ 2. build_query_agent(wiki_root, model, language)
│    ├─ Load schema (AGENTS.md)
│    ├─ Define tools:
│    │  ├─ read_file(path) — Read wiki markdown
│    │  ├─ get_page_content(doc_name, pages) — Fetch from long doc
│    │  └─ get_image(path) — View images
│    └─ Create Agent with instructions
│
├─ 3. run_query(question, kb_dir, model, stream=True)
│    │
│    ├─ Agent iteration loop:
│    │  ├─ Run agent with question
│    │  │  └─ LLM sees schema, tools, wiki instructions
│    │  │
│    │  ├─ Agent decides which tools to call
│    │  │  ├─ read_file("index.md") — Overview
│    │  │  ├─ read_file("summaries/...") — Relevant summaries
│    │  │  ├─ read_file("concepts/...") — Cross-doc synthesis
│    │  │  ├─ get_page_content(...) — Detailed sources
│    │  │  └─ get_image(...) — View figures
│    │  │
│    │  ├─ Execute tools, get results
│    │  └─ LLM synthesizes answer
│    │
│    ├─ Stream response to stdout
│    └─ Return full answer text
│
├─ 4. Append log
│    └─ Add to wiki/log.md: query | question
│
└─ Optional: Save to explorations/
   └─ If --save flag: Write answer to explorations/{slug}.md
```

**Tools Used by Agent**:
- `read_file()` — Access wiki pages
- `get_page_content()` — For PageIndex docs, fetch specific pages
- `get_image()` — Display figures

---

### Workflow 3: Interactive Chat

```
User runs: openkb chat
│
├─ 1. Determine session:
│    ├─ --resume: Load existing session from .openkb/chats/{id}.json
│    └─ Default: Create new ChatSession
│
├─ 2. run_chat(kb_dir, session, no_color, raw)
│    │
│    ├─ Loop:
│    │  ├─ Prompt user for input (with history, editing)
│    │  ├─ Check for slash commands:
│    │  │  ├─ /exit → break
│    │  │  ├─ /clear → new session
│    │  │  ├─ /save → export to explorations/
│    │  │  ├─ /status → show KB stats
│    │  │  ├─ /list → list docs
│    │  │  ├─ /lint → run linting
│    │  │  ├─ /add → call add_single_file()
│    │  │  └─ /help → show commands
│    │  │
│    │  ├─ If text query:
│    │  │  ├─ Add to session history
│    │  │  ├─ Run query_agent() (same as query workflow)
│    │  │  ├─ Stream response
│    │  │  ├─ Save full response to session
│    │  │  └─ Update session.turn_count
│    │  │
│    │  └─ Save session to disk
│    │
│    └─ On Ctrl-D or /exit:
│       └─ Persist final session & exit
│
└─ Session file: .openkb/chats/{id}.json
   ├─ id: timestamp-random
   ├─ title: first user message (truncated)
   ├─ created_at, updated_at: ISO timestamps
   ├─ turn_count: number of user turns
   └─ history: [{role, content}, ...]
```

**Session Resumption**:
```
openkb chat --resume                # Latest session
openkb chat --resume 20260502-1     # By ID prefix
openkb chat --list                  # Show all sessions
openkb chat --delete 20260502-1     # Delete session
```

---

## CLI Commands & User Interactions

### Commands Summary

| Command | Purpose | Output |
|---------|---------|--------|
| `openkb init` | Initialize KB in cwd | Create .openkb/, wiki/, raw/ |
| `openkb add <path>` | Add document(s) | Process + compile, update wiki/ |
| `openkb query <q>` | Ask question | Answer with citations |
| `openkb chat` | Multi-turn dialog | Interactive REPL |
| `openkb watch` | Auto-process raw/ | Watch for new files |
| `openkb lint` | Health check | Report to wiki/reports/ |
| `openkb use <path>` | Set default KB | Update global config |

### Add Command Flow

```
openkb add paper.pdf               # Single file
openkb add ./papers/               # Directory (recurse, process all)
openkb add .                       # Current dir (all supported files)
```

**Supported Extensions**:
`.pdf`, `.md`, `.markdown`, `.docx`, `.pptx`, `.xlsx`, `.html`, `.htm`, `.txt`, `.csv`

**Progress Output**:
```
Adding: paper.pdf
  Long document detected — indexing with PageIndex...
  Compiling long doc (doc_id=abc123)...
  [OK] paper.pdf added to knowledge base.
```

### Query Command

```
openkb query "What is attention?"
openkb query "Compare concepts X and Y" --save
```

**Output**:
- Streamed agent thinking + tool calls (colored)
- Final answer with citations
- Optional: Saved to `wiki/explorations/{slug}.md`

---

## Configuration & State Management

### Files & Hierarchy

**Global** (`~/.config/openkb/`):
- `global.yaml` — Global settings
  - `default_kb`: Path to last-used KB
  - `known_kbs`: List of KB paths
- `.env` — Global LLM API key

**Per-KB** (`.openkb/`):
- `config.yaml` — KB-specific settings
  - `model`: LLM to use
  - `language`: Output language
  - `pageindex_threshold`: Long doc threshold
- `.env` — KB-local LLM API key (overrides global)
- `hashes.json` — File SHA-256 registry
- `pageindex/` — Cached PageIndex data
- `chats/` — Chat session files

### Configuration Loading

```
1. Load defaults from DEFAULT_CONFIG
2. Merge KB-level config.yaml
3. Override with environment variables:
   - OPENKB_DIR: KB directory
   - LLM_API_KEY: API key
   - LITELLM_LOCAL_MODEL_COST_MAP: Use local costs
```

### API Key Resolution

```
Checked in order:
1. LLM_API_KEY env var
2. KB-local .env file
3. Global ~/.config/openkb/.env
4. Provider-specific vars (OPENAI_API_KEY, etc.)

Propagated to:
- litellm.api_key
- Provider-specific env vars
```

---

## LLM Integration & Prompting

### Supported Models

Via LiteLLM (format: `provider/model`):
- **OpenAI**: `gpt-5.4`, `gpt-5.4-mini` (or `openai/gpt-5.4`)
- **Anthropic**: `anthropic/claude-sonnet-4-6`, `anthropic/claude-opus-4-6`
- **Gemini**: `gemini/gemini-3.1-pro-preview`, `gemini/gemini-3-flash-preview`
- Others: See https://docs.litellm.ai/docs/providers

### Compilation Prompts

**System Prompt**:
```
You are OpenKB's wiki compilation agent for a personal knowledge base.

[Schema definition: wiki structure, link format, etc.]

Write all content in {language} language.
Use [[wikilinks]] to connect related pages.
```

**User Step 1: Summary**
```
New document: {doc_name}

Full text:
{content}

Write a summary page for this document in Markdown.

Return a JSON object with two keys:
- "brief": Single sentence (under 100 chars) describing main contribution
- "content": Full summary in Markdown with [[wikilinks]] to related concepts

Return ONLY valid JSON, no fences.
```

**User Step 2: Concept Planning**
```
Based on the summary above, decide how to update the wiki's concept pages.

Existing concept pages:
{concept_briefs}

Return a JSON object with three keys:

1. "create" — new concepts not covered by existing pages:
   [{"name": "concept-slug", "title": "Human-Readable Title"}]

2. "update" — existing concepts with new info worth integrating:
   [{"name": "existing-slug", "title": "Existing Title"}]

3. "related" — existing concepts tangentially related:
   ["slug1", "slug2"]

Rules:
- For first few docs, create 2-3 foundational concepts max
- Do NOT create overlapping concepts—use "update"
- "related" is for lightweight cross-linking only
```

**User Steps 3-N: Generate Concepts** (parallel)
```
Create new concept:
{concept_name}: {concept_title}

Based on {doc_name}, write a new concept page for {concept_title}.

Return a JSON object:
{
  "content": "Full Markdown content with [[wikilinks]] and citations"
}

Return ONLY valid JSON.
```

### Query Agent Instructions

```
You are OpenKB, a knowledge-base Q&A agent. You answer questions by searching the wiki.

[Schema definition]

## Search strategy
1. Read index.md to see all documents and concepts
2. Read relevant summaries/ for overviews
3. Read concepts/ for cross-document synthesis
4. Fetch detailed source content when needed
5. Use get_image to view figures
6. Synthesize clear, concise, well-cited answer

Answer based only on wiki content. Be concise.
Before each tool call, explain the reason in one sentence.
```

### Prompt Caching

For compilation:
- **Cached Context**: Base context A (schema + document content)
  - Cost: Full price for first call
  - Subsequent calls: Cache hit (90% cheaper)
- **Cache Lifetime**: 5 minutes per session

For queries:
- No explicit caching in query; stateless per query

---

## Image & Document Handling

### Image Extraction & Storage

**From PDFs** (via pymupdf):
```python
# In sources/{doc}.md
![Figure 1](images/doc/p1_fig1.png)
```

**From Word/HTML** (via markitdown → base64):
```markdown
# MarkItDown gives base64 images:
![image](data:image/png;base64,iVBORw0KG...)

# converter.py extracts them:
Extract → Save as PNG → Update reference
```

**Directory Structure**:
```
wiki/sources/images/
├── paper/
│   ├── p1_img1.png
│   ├── p2_img2.png
│   └── p5_fig3.png
└── notes/
    └── img_001.png
```

### Long Document Page Structure

**PageIndex provides**:
- TOC (table of contents) with page ranges
- Per-page text content
- Per-page images

**Stored in** `wiki/sources/{doc}.json`:
```json
{
  "doc_name": "Attention Is All You Need",
  "doc_description": "Introduces the Transformer...",
  "pages": [
    {
      "page_num": 1,
      "content": "Introduction...",
      "images": ["p1_img1.png", "p1_img2.png"]
    },
    {
      "page_num": 2,
      "content": "Background...",
      "images": []
    }
  ],
  "structure": [
    {
      "title": "Introduction",
      "pages": "1-3"
    },
    {
      "title": "Background",
      "pages": "4-8"
    }
  ]
}
```

### Query Page Content

In `agent/query.py`, `get_page_content()` tool:
```python
def get_page_content(doc_name: str, pages: str) -> str:
    """Get text from specific pages of a long document.
    
    Args:
        doc_name: "attention-is-all-you-need"
        pages: "3-5,10-12" (parse_pages handles ranges)
    
    Returns:
        Combined text from requested pages
    """
```

**Examples**:
- `"1-5"` → Pages 1, 2, 3, 4, 5
- `"3,7,10"` → Pages 3, 7, 10
- `"1-3,10-12"` → Pages 1-3 and 10-12

---

## Example: Complete Document Add Flow

Let's trace adding a 25-page PDF "attention.pdf":

### Step 1: Trigger
```bash
$ openkb add attention.pdf
Adding: attention.pdf
```

### Step 2: Conversion
```python
# cli.py: add_single_file()
convert_document(Path("attention.pdf"), kb_dir)
  # converter.py
  ├─ Compute SHA-256 hash
  ├─ Check HashRegistry (.openkb/hashes.json) — NEW file
  ├─ Copy to raw/attention.pdf
  ├─ Count PDF pages: 25 pages
  ├─ 25 >= 20 threshold → is_long_doc=True
  └─ Return ConvertResult(is_long_doc=True, raw_path=...)
```

### Step 3: Indexing
```
  # cli.py: long doc branch
  index_long_document(raw/attention.pdf, kb_dir)
    # indexer.py
    ├─ Init PageIndex client (uses model from config)
    ├─ Add PDF to PageIndex:
    │  ├─ Retry up to 3 times (stochastic)
    │  ├─ PageIndex API processes PDF
    │  └─ Returns doc_id (e.g., "doc_789")
    ├─ Fetch complete document:
    │  ├─ Get metadata: name, description, structure
    │  ├─ Get pages (cloud or local pymupdf)
    │  └─ Write wiki/sources/attention.json
    └─ Return IndexResult(doc_id="doc_789", description="...", tree={...})
```

### Step 4: Compilation
```
  # cli.py: compile_long_doc()
  compile_long_doc(
    doc_name="attention",
    summary_path="wiki/summaries/attention.md",
    doc_id="doc_789",
    kb_dir=...,
    model="gpt-5.4"
  )
  
  # agent/compiler.py
  
  ├─ Load schema (AGENTS.md)
  ├─ Load config (language="en")
  │
  ├─ Build context:
  │  ├─ System: Schema + language
  │  └─ Content: doc_id, description, structure
  │
  ├─ LLM Call 1: Summary (cached context)
  │  ├─ Request: "Write summary for attention.pdf"
  │  ├─ Response: JSON with brief + content
  │  └─ Write wiki/summaries/attention.md with frontmatter
  │     ---
  │     doc_type: pageindex
  │     doc_name: attention
  │     brief: "Introduces the Transformer architecture..."
  │     full_text: sources/attention.json
  │     ---
  │     
  │     # Attention Is All You Need
  │     
  │     ## Summary
  │     The paper introduces the Transformer, a sequence-to-sequence
  │     model based entirely on attention mechanisms...
  │
  ├─ LLM Call 2: Concept Planning (cache reused)
  │  ├─ Request: "Plan concepts based on summary"
  │  ├─ List existing concepts: (empty first time)
  │  └─ Response:
  │     {
  │       "create": [
  │         {"name": "transformer", "title": "Transformer Architecture"},
  │         {"name": "attention", "title": "Attention Mechanism"}
  │       ],
  │       "update": [],
  │       "related": []
  │     }
  │
  ├─ LLM Calls 3-4: Parallel Concept Generation
  │  │
  │  ├─ Call 3a: Create "transformer"
  │  │  ├─ Request: "Create concept for Transformer Architecture"
  │  │  ├─ Response: JSON with markdown content
  │  │  └─ Write wiki/concepts/transformer.md
  │  │     # Transformer Architecture
  │  │     
  │  │     The Transformer is a neural network architecture based on
  │  │     self-attention mechanisms. From [[summaries/attention]], it
  │  │     was introduced to address limitations of RNNs...
  │  │     
  │  │     ## Key Components
  │  │     - [[attention]] (self-attention)
  │  │     - Multi-head attention
  │  │     - Feed-forward networks
  │  │
  │  └─ Call 3b: Create "attention"
  │     ├─ Request: "Create concept for Attention Mechanism"
  │     └─ Write wiki/concepts/attention.md
  │        # Attention Mechanism
  │        
  │        Attention allows models to focus on relevant parts of input.
  │        Introduced in [[summaries/attention]], it became fundamental...
  │
  ├─ Update index.md
  │  ├─ Add to ## Documents:
  │  │  - [attention](summaries/attention.md) — Introduces the Transformer 
  │  │    architecture and self-attention mechanisms (pageindex)
  │  │
  │  └─ Add to ## Concepts:
  │     - [transformer](concepts/transformer.md) — Transformer Architecture
  │     - [attention](concepts/attention.md) — Attention Mechanism
  │
  └─ Register hash
     └─ .openkb/hashes.json: {sha256: {name: "attention.pdf", type: "long_pdf"}}
```

### Step 5: Logging
```
  append_log(wiki/log.md)
  ## [2026-05-02 10:23:45] ingest | attention.pdf
```

### Step 6: Success
```
  [OK] attention.pdf added to knowledge base.
```

### Resulting Files

```
wiki/
├── index.md (UPDATED)
├── log.md (APPENDED)
├── sources/
│   └── attention.json (NEW - pages)
├── summaries/
│   └── attention.md (NEW)
└── concepts/
    ├── transformer.md (NEW)
    └── attention.md (NEW)

.openkb/
├── hashes.json (UPDATED)
└── pageindex/
    └── doc_789.json (CACHED)

raw/
└── attention.pdf (COPIED)
```

---

## Key Concepts for UI Development

### 1. **File-Based Architecture**
- **No database**: All data is Markdown files + JSON
- **Filesystem is source of truth**: Changes to wiki/ files are saved to disk
- **Atomic operations**: Each operation (add, query, compile) updates multiple files
- **Important for UI**: 
  - Real-time file watching can detect external changes
  - UI can parse Markdown directly (frontmatter + content)
  - Search is fast (filesystem grep, not DB queries)

### 2. **Hash-Based Deduplication**
- Files are identified by SHA-256 hash, not filename
- If user adds same file twice (renamed), system skips it
- **For UI**:
  - Show "already processed" message instead of reprocessing
  - Enable smart re-import: hash check first, then decide action

### 3. **Two Document Types**
- **Short documents** (< 20 pages): 
  - Converted to single Markdown file
  - Full content available immediately
  - Cheaper to compile (less LLM usage)

- **Long documents** (≥ 20 pages):
  - Indexed via PageIndex (tree structure)
  - Content split per-page (JSON format)
  - More expensive but enables targeted retrieval

- **For UI**:
  - Show which documents are "indexed" vs "flat"
  - Provide different visualization for structure (TOC for indexed docs)
  - Different query approaches (full read vs page-by-page fetch)

### 4. **Persistent Sessions**
- Chat sessions saved as JSON at `.openkb/chats/{id}.json`
- Can be resumed, listed, deleted
- History sanitized (large images replaced with references)

- **For UI**:
  - Show list of previous sessions
  - Allow resume/delete/export
  - Persist session state across app restarts
  - Export chat as Markdown

### 5. **Wikilinks & Graph Structure**
- `[[target]]` or `[[target|display text]]` format
- Enables graph view: documents → concepts → relationships
- Lint checks for broken links

- **For UI**:
  - Build graph visualization (nodes = pages, edges = wikilinks)
  - Show backlinks (incoming links to a page)
  - Highlight orphaned pages
  - Visual broken link detection

### 6. **LLM-Driven Pipeline**
- Compilation is LLM-intensive (not deterministic)
- Uses prompt caching for cost/speed
- Async operations (long docs take time)

- **For UI**:
  - Show progress indicators during compilation
  - Stream LLM responses (don't wait for full completion)
  - Handle retries gracefully (PageIndex retries 3 times)
  - Show LLM model, language, token usage

### 7. **Async Operations**
- Add, compile, query, lint, watch are all async
- CLI uses `asyncio.run()` to block until complete

- **For UI**:
  - Use async/await throughout (no blocking operations)
  - Show background job queue and progress
  - Allow cancellation mid-operation

### 8. **Tool-Use Loop**
- Query/chat agents iteratively call tools (read_file, get_page_content, get_image)
- Agent decides which tools to use, not user
- Need to show tool calls + reasoning for transparency

- **For UI**:
  - Display tool calls in real-time (show agent thinking)
  - Show which files agent accessed
  - Stream responses as they're generated
  - Allow agent to use up to 50 turns before giving up

### 9. **Configuration Levels**
- System-wide (global): `~/.config/openkb/`
- Per-KB: `.openkb/`
- API keys loaded from multiple sources

- **For UI**:
  - Settings modal with KB-level controls
  - Global preferences menu
  - Environment variable visualization
  - API key management (masked display)

### 10. **Lint & Health Checks**
- Two types: structural (file/link integrity) + knowledge (LLM-based)
- Reports saved to `wiki/reports/`
- Can detect: broken links, orphans, contradictions, stale content

- **For UI**:
  - Show KB health score
  - List issues with severity levels
  - Link issues to affected pages
  - Suggest fixes (fix broken links, update orphans)

---

## Summary: Mental Model for UI Development

Think of OpenKB as a **self-managing wiki engine**:

1. **Input**: Raw documents (PDFs, Word, Markdown, etc.)
2. **Processing**: Automatic conversion + LLM compilation
3. **Storage**: Wiki-style Markdown files + JSON
4. **Access**: Agent-based navigation + free-text search
5. **Maintenance**: Linting + health checks

**Key UI Features to Build**:
- **Document Management**: Upload → monitor processing → view status
- **Wiki Browser**: Search → view pages → follow wikilinks → see graph
- **Chat Interface**: Multi-turn conversation with session persistence
- **Query Sandbox**: Ask questions, see agent reasoning + citations
- **Admin Panel**: Configuration, API keys, health checks, logs
- **Progress Monitoring**: Show ongoing operations (add, compile, lint)

---

## Appendices

### File Format Reference

#### Frontmatter (YAML)
Used in summaries and exploration pages:
```yaml
---
doc_type: short|pageindex        # Document type
doc_name: paper                  # Identifier
brief: "One-liner description"   # 1-line summary
full_text: sources/paper.md      # Path to full content
query: "Optional: original query" # For exploration pages
---
```

#### Wikilinks
```markdown
# Basic link
[[concepts/attention]]

# Link with display text
See [[concepts/attention|attention mechanism]] for details.

# Link to document summary
From [[summaries/paper]], we learn...

# Link within same section
(automatically resolved to [[concepts/same-concept]])
```

#### Markdown Structure
- Top-level `#` → Document title
- Second-level `##` → Sections
- Third+ levels → Subsections
- `---` → Frontmatter (top of file only)
- `![]()` → Images (paths relative to wiki root)

### Tools Reference

#### Agent Tools (in query/chat)

| Tool | Args | Returns | Use Case |
|------|------|---------|----------|
| `read_file` | `path: str` | `str` | Read any wiki page |
| `get_page_content` | `doc_name, pages` | `str` | Fetch from long doc |
| `get_image` | `image_path: str` | `ToolOutputImage` | View images |
| `list_wiki_files` | `directory` | `str` | List files in directory |

#### CLI Tools (external commands)

| Command | Purpose | Must Call Before |
|---------|---------|------------------|
| `openkb init` | Create KB | Everything |
| `openkb add` | Add documents | Query/chat |
| `openkb query` | One-shot Q&A | N/A |
| `openkb chat` | Multi-turn | N/A |
| `openkb watch` | Auto-process | Long-term operation |
| `openkb lint` | Health check | N/A (optional) |

---

## Conclusion

OpenKB is a sophisticated **knowledge compilation system** that combines:
- **Document processing** (conversion, indexing)
- **LLM-driven synthesis** (summaries, concepts, cross-links)
- **Intelligent retrieval** (agent-based navigation)
- **Health management** (linting, contradictions, orphans)

For your UI, focus on:
1. **Visualizing the KB state** (documents, concepts, relationships)
2. **Monitoring operations** (add, compile, lint progress)
3. **Interacting with agents** (showing reasoning, streaming responses)
4. **Session persistence** (saving, resuming chats)
5. **Configuration management** (API keys, models, language)

The Markdown-based storage makes real-time updates possible without database overhead. The agent architecture enables intelligent navigation without explicit user direction.

---

**Happy building! 🚀**
