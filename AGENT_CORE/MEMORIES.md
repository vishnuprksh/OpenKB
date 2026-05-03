# Strategic Memories

### [2026-05-03] - UI Framework Choice: Dash
- **Context**: User requested a UI for OpenKB.
- **Decision**: Use Plotly Dash with Bootstrap components and custom premium CSS.
- **Reasoning**: Dash allows for rapid development of data-rich interfaces in pure Python, making it easy to integrate with the existing OpenKB logic without needing a separate frontend/backend split. It also satisfies the "Modern/Premium" requirement through custom styling.

### [2026-05-03] - Integration Strategy: Direct Module Import
- **Context**: Need to call OpenKB functionality from Dash.
- **Decision**: Import `openkb` modules directly instead of wrapping CLI calls.
- **Reasoning**: Provides better control over progress updates and error handling; more efficient than spawning subprocesses.

### [2026-05-03] - UI Strategy: Reasoning Transparency
- **Context**: Agent uses tools (read_file, search) which can take time.
- **Decision**: Display tool-use events as "Reasoning" blocks in the chat UI.
- **Reasoning**: Improves UX by showing the user what the agent is doing during wait times, aligning with modern agentic UI patterns.

### [2026-05-03] - Session Management: Dynamic Sidebar
- **Context**: New chats created via the interface weren't appearing in the sidebar until page refresh.
- **Decision**: Use a `dcc.Store` named `session-update-trigger` and a dedicated callback to refresh the sidebar session list.
- **Reasoning**: Ensures a seamless "New Chat" experience without full page reloads, maintaining the SPA feel of the Dash application.
