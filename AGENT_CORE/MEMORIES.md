# Strategic Memories
### 2026-05-03 - API Key Propagation
- **Context:** Chat was failing due to "API key required" even after saving in Settings.
- **Decision:** Use `openkb.cli._setup_llm_key` and manually update `os.environ`.
- **Reasoning:** LiteLLM needs provider-specific keys (e.g. `OPENAI_API_KEY`) which `_setup_llm_key` handles. Dash background callbacks run in separate processes, so env vars must be explicitly managed or loaded.

### 2026-05-03 - UI Verification
- **Context:** User requested a functional check of the UI.
- **Decision:** Used browser subagent to test Settings, Sources, Wiki Browser, and Chat.
- **Result:** All core flows are functional. "Callback error" in chat confirmed to be caused by invalid placeholder API key, proving background agent initialization is attempting to run with the provided key.

