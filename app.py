import os
import asyncio
import json
from pathlib import Path
import dash
from dash import dcc, html, Input, Output, State, ALL, callback_context
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
from dotenv import load_dotenv

# OpenKB imports
from openkb.config import load_config, save_config, DEFAULT_CONFIG
from openkb.cli import _find_kb_dir, add_single_file, _setup_llm_key
from openkb.agent.chat_session import ChatSession, list_sessions, load_session, resolve_session_id
from openkb.agent.query import build_query_agent, MAX_TURNS
from agents import Runner, RunItemStreamEvent

import diskcache
from dash import DiskcacheManager

# --- Initialization ---
KB_DIR = _find_kb_dir() or Path.cwd()
WIKI_DIR = KB_DIR / "wiki"
OPENKB_DIR = KB_DIR / ".openkb"
load_dotenv(KB_DIR / ".env")
_setup_llm_key(KB_DIR)
CACHE_DIR = OPENKB_DIR / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

cache = diskcache.Cache(str(CACHE_DIR))
background_callback_manager = DiskcacheManager(cache)

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    suppress_callback_exceptions=True,
    title="OpenKB",
    background_callback_manager=background_callback_manager
)

# --- Layout Components ---

def get_sidebar():
    sessions = list_sessions(KB_DIR)
    session_links = [
        html.A(
            [
                html.Div(s['title'] or "New Chat", className="text-truncate"),
                html.Small(s['updated_at'][:10], className="text-muted")
            ],
            href=f"/chat/{s['id']}",
            className="nav-link",
            id={'type': 'session-link', 'id': s['id']}
        ) for s in sessions[:10]
    ]
    
    return html.Div([
        html.Div("OpenKB", className="sidebar-title"),
        html.Hr(style={"borderColor": "var(--border-color)"}),
        
        dbc.Button([DashIconify(icon="mdi:plus", width=20, className="me-2"), "New Chat"], 
                   href="/chat", className="custom-button w-100 mb-4"),
        
        dcc.Link([DashIconify(icon="mdi:chat", width=20, className="me-2"), "Chat History"], href="/chat", className="nav-link"),
        dcc.Link([DashIconify(icon="mdi:book-open-variant", width=20, className="me-2"), "Wiki Browser"], href="/wiki", className="nav-link"),
        dcc.Link([DashIconify(icon="mdi:plus-box", width=20, className="me-2"), "Add Sources"], href="/add", className="nav-link"),
        dcc.Link([DashIconify(icon="mdi:cog", width=20, className="me-2"), "Settings"], href="/settings", className="nav-link"),
        
        html.Div("Recent Chats", className="mt-4 mb-2 small text-uppercase text-muted fw-bold"),
        html.Div(session_links, id="sidebar-sessions")
    ], className="sidebar")

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='current-session-id', storage_type='session'),
    dcc.Store(id='session-update-trigger', data=0),
    get_sidebar(),
    html.Div([
        html.Div(id='page-content'),
        html.Div(id='chat-history', className="chat-container fade-in", style={"display": "none"}),
        html.Div(id='chat-loading-out', className="chat-container pb-0", style={"display": "none"}),
    ], id='main-container', className="main-content"),
    html.Div([
        dbc.Input(id='chat-input', placeholder="Ask anything...", className="custom-input", autocomplete="off"),
        dbc.Button(DashIconify(icon="mdi:send", width=24), id='chat-send', className="custom-button ms-2")
    ], id='chat-input-container', className="fixed-bottom p-4 bg-dark", style={"left": "280px", "borderTop": "1px solid var(--border-color)", "display": "none", "alignItems": "center"}),

    html.Div(id='notifications-container', style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999})
])

# --- Views ---

def view_chat(session_id=None):
    return html.Div([]) # Page content is empty because history is global

def view_wiki():
    summaries = sorted((WIKI_DIR / "summaries").glob("*.md")) if (WIKI_DIR / "summaries").exists() else []
    concepts = sorted((WIKI_DIR / "concepts").glob("*.md")) if (WIKI_DIR / "concepts").exists() else []
    
    if not summaries and not concepts:
        return html.Div([
            html.H2("Wiki Browser", className="mb-4"),
            html.Div([
                html.P("No documents or concepts found in the wiki.", className="text-muted"),
                dcc.Link(dbc.Button("Add Sources", className="custom-button"), href="/add")
            ], className="glass-card text-center py-5")
        ], className="fade-in")

    return html.Div([
        html.H2("Wiki Browser", className="mb-4"),
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H5("Documents", className="mb-3"),
                    html.Div([
                        html.Div(f.stem, className="nav-link py-1", id={'type': 'wiki-item', 'path': str(f)}) for f in summaries
                    ])
                ], className="glass-card")
            ], width=4),
            dbc.Col([
                html.Div([
                    html.H5("Concepts", className="mb-3"),
                    html.Div([
                        html.Div(f.stem, className="nav-link py-1", id={'type': 'wiki-item', 'path': str(f)}) for f in concepts
                    ])
                ], className="glass-card")
            ], width=4)
        ]),
        html.Div(id='wiki-content', className="glass-card mt-4 fade-in", style={"display": "none"})
    ], className="fade-in")

def view_add():
    return html.Div([
        html.H2("Add Sources", className="mb-4"),
        html.Div([
            html.P("Enter a file or directory path to add to your knowledge base.", className="text-secondary"),
            dbc.Input(id='add-path-input', placeholder="/path/to/documents", className="custom-input mb-3"),
            dbc.Button([
                dbc.Spinner(size="sm", id="add-spinner", spinner_style={"display": "none"}, spinner_class_name="me-2"),
                "Process Documents"
            ], id='add-process-btn', className="custom-button"),
            html.Div(id='add-output', className="mt-4 p-3 bg-black text-success font-monospace", 
                     style={"borderRadius": "8px", "minHeight": "200px", "whiteSpace": "pre-wrap", "fontSize": "0.9rem", "border": "1px solid var(--border-color)"})
        ], className="glass-card")
    ], className="fade-in")

PROVIDER_PRESETS = {
    "openrouter": {
        "label": "OpenRouter",
        "model_prefix": "openrouter/",
        "key_env": "OPENROUTER_API_KEY",
        "placeholder": "sk-or-v1-...",
        "default_model": "openrouter/z-ai/glm-4.5-air:free",
    },
    "openai": {
        "label": "OpenAI",
        "model_prefix": "",
        "key_env": "OPENAI_API_KEY",
        "placeholder": "sk-...",
        "default_model": "gpt-4o-mini",
    },
    "anthropic": {
        "label": "Anthropic",
        "model_prefix": "anthropic/",
        "key_env": "ANTHROPIC_API_KEY",
        "placeholder": "sk-ant-...",
        "default_model": "anthropic/claude-3-haiku",
    },
    "gemini": {
        "label": "Google Gemini",
        "model_prefix": "gemini/",
        "key_env": "GEMINI_API_KEY",
        "placeholder": "AIza...",
        "default_model": "gemini/gemini-1.5-flash",
    },
}

def view_settings():
    config = load_config(OPENKB_DIR / "config.yaml")
    current_model = config.get('model', DEFAULT_CONFIG['model'])
    
    # Detect current provider from model string
    current_provider = "openrouter"
    for pid, preset in PROVIDER_PRESETS.items():
        if preset["model_prefix"] and current_model.startswith(preset["model_prefix"]):
            current_provider = pid
            break
    
    provider_options = [{"label": v["label"], "value": k} for k, v in PROVIDER_PRESETS.items()]
    current_placeholder = PROVIDER_PRESETS[current_provider]["placeholder"]
    
    return html.Div([
        html.H2("Settings", className="mb-4"),
        html.Div([
            html.Label("Provider", className="mb-2"),
            dbc.Select(
                id='settings-provider',
                options=provider_options,
                value=current_provider,
                className="custom-input mb-3",
            ),
            html.Label("Model (LiteLLM format)", className="mb-2"),
            dbc.Input(id='settings-model', value=current_model, className="custom-input mb-4"),
            
            html.Label("API Key (saved to .env)", className="mb-2"),
            dbc.Input(id='settings-api-key', type="password", placeholder=current_placeholder, className="custom-input mb-1"),
            html.Small(id='settings-key-hint', className="text-muted mb-4 d-block"),
            
            dbc.Button("Save Settings", id='settings-save-btn', className="custom-button mt-3")
        ], className="glass-card", style={"maxWidth": "600px"}),
        dbc.Toast(
            "Settings saved successfully!",
            id="settings-toast",
            header="Settings",
            is_open=False,
            dismissable=True,
            duration=3000,
            icon="success",
            style={"position": "fixed", "top": 66, "right": 10, "width": 350, "zIndex": 9999},
        ),
        html.Div(id='settings-status', style={"display": "none"})
    ], className="fade-in")

# --- Callbacks ---

@app.callback(
    Output('page-content', 'children'),
    Output('chat-history', 'style'),
    Output('chat-loading-out', 'style'),
    Output('chat-input-container', 'style'),
    Input('url', 'pathname')
)
def display_page(pathname):
    hide_style = {"display": "none"}
    chat_container_style = {"display": "flex"} # chat-container is flex by default in CSS
    chat_input_style = {"left": "280px", "borderTop": "1px solid var(--border-color)", "display": "flex", "alignItems": "center"}
    
    if pathname == '/wiki':
        return view_wiki(), hide_style, hide_style, hide_style
    elif pathname == '/add':
        return view_add(), hide_style, hide_style, hide_style
    elif pathname == '/settings':
        return view_settings(), hide_style, hide_style, hide_style
    elif pathname and (pathname == '/chat' or pathname.startswith('/chat/')):
        session_id = pathname.split('/')[-1] if pathname.startswith('/chat/') else None
        return view_chat(session_id), chat_container_style, chat_container_style, chat_input_style
    else:
        # Default to chat
        return view_chat(), chat_container_style, chat_container_style, chat_input_style

@app.callback(
    Output('wiki-content', 'children'),
    Output('wiki-content', 'style'),
    Output({'type': 'wiki-item', 'path': ALL}, 'className'),
    Input({'type': 'wiki-item', 'path': ALL}, 'n_clicks'),
    State({'type': 'wiki-item', 'path': ALL}, 'id'),
    prevent_initial_call=True
)
def show_wiki_item(n_clicks, ids):
    if not any(n_clicks):
        return dash.no_update, dash.no_update, dash.no_update
    
    ctx = callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update
    
    triggered_id = dash.ctx.triggered_id
    selected_path = triggered_id['path']
    
    with open(selected_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove frontmatter
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            content = parts[2]
            
    # Update class names for highlighting
    new_classes = [
        f"nav-link py-1 {'active' if item['path'] == selected_path else ''}"
        for item in ids
    ]
    
    return dcc.Markdown(content, className="wiki-markdown-body"), {"display": "block"}, new_classes

@app.callback(
    Output('add-output', 'children'),
    Input('add-process-btn', 'n_clicks'),
    State('add-path-input', 'value'),
    background=True,
    running=[
        (Output("add-process-btn", "disabled"), True, False),
        (Output("add-spinner", "spinner_style"), {"display": "inline-block"}, {"display": "none"}),
    ],
    progress=Output('add-output', 'children'),
    prevent_initial_call=True
)
def process_add(set_progress, n_clicks, path):
    if not path:
        return "Please enter a path."
    
    target = Path(path)
    if not target.exists():
        return f"Error: Path does not exist: {path}"
    
    output_log = [f"Scanning {path}...\n"]
    set_progress("".join(output_log))
    
    try:
        if target.is_file():
            add_single_file(target, KB_DIR)
            output_log.append(f"[OK] Added {target.name}")
        else:
            files = [f for f in sorted(target.rglob("*")) if f.is_file() and f.suffix.lower() in {'.pdf', '.md', '.docx', '.pptx', '.xlsx', '.html', '.txt'}]
            output_log.append(f"Found {len(files)} files.\n")
            set_progress("".join(output_log))
            for f in files:
                add_single_file(f, KB_DIR)
                output_log.append(f"[OK] Added {f.name}\n")
                set_progress("".join(output_log))
    except Exception as e:
        output_log.append(f"[ERROR] {str(e)}")
        
    return "".join(output_log)

@app.callback(
    Output('settings-model', 'value'),
    Output('settings-api-key', 'placeholder'),
    Output('settings-key-hint', 'children'),
    Input('settings-provider', 'value'),
    prevent_initial_call=True
)
def update_provider_fields(provider):
    preset = PROVIDER_PRESETS.get(provider, PROVIDER_PRESETS["openrouter"])
    hint = f"Saved as {preset['key_env']} in .env"
    return preset["default_model"], preset["placeholder"], hint

@app.callback(
    Output('settings-status', 'children'),
    Input('settings-save-btn', 'n_clicks'),
    State('settings-model', 'value'),
    State('settings-api-key', 'value'),
    State('settings-provider', 'value'),
    prevent_initial_call=True
)
def save_settings(n_clicks, model, api_key, provider):
    config = load_config(OPENKB_DIR / "config.yaml")
    config['model'] = model
    save_config(OPENKB_DIR / "config.yaml", config)
    
    if api_key:
        preset = PROVIDER_PRESETS.get(provider, PROVIDER_PRESETS["openrouter"])
        key_env = preset["key_env"]
        
        env_path = KB_DIR / ".env"
        lines = []
        if env_path.exists():
            with open(env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        
        # Replace or append both LLM_API_KEY and the provider-specific key
        keys_to_set = {"LLM_API_KEY": api_key, key_env: api_key}
        for key_name, key_val in keys_to_set.items():
            found = False
            for i, line in enumerate(lines):
                if line.strip().startswith(f"{key_name}="):
                    lines[i] = f"{key_name}={key_val}\n"
                    found = True
                    break
            if not found:
                lines.append(f"{key_name}={key_val}\n")
            
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
            
        # Immediate propagation
        os.environ["LLM_API_KEY"] = api_key
        os.environ[key_env] = api_key
        _setup_llm_key(KB_DIR)
            
    return True
    
@app.callback(
    Output('settings-toast', 'is_open'),
    Input('settings-status', 'children'),
    prevent_initial_call=True
)
def toggle_settings_toast(status):
    if status:
        return True
    return False

# --- Chat Implementation ---

@app.callback(
    Output('chat-history', 'children', allow_duplicate=True),
    Output('chat-input', 'value'),
    Output('current-session-id', 'data'),
    Output('session-update-trigger', 'data'),
    Input('chat-send', 'n_clicks'),
    Input('chat-input', 'n_submit'),
    State('url', 'pathname'),
    State('chat-input', 'value'),
    State('current-session-id', 'data'),
    State('session-update-trigger', 'data'),
    background=True,
    running=[
        (Output("chat-send", "disabled"), True, False),
        (Output("chat-input", "disabled"), True, False),
    ],
    progress=[Output("chat-history", "children"), Output("chat-loading-out", "children")],
    prevent_initial_call=True
)
def handle_chat(set_progress, n_clicks, n_submit, pathname, message, session_id, trigger_count):
    if not pathname or not pathname.startswith('/chat'):
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    if not message:
        return dash.no_update, "", session_id, trigger_count

    # Process new message
    config = load_config(OPENKB_DIR / "config.yaml")
    model = config.get('model', DEFAULT_CONFIG['model'])
    language = config.get('language', 'en')
    
    # Ensure keys are loaded in background process
    _setup_llm_key(KB_DIR)
    
    is_new_session = False
    if not session_id:
        session = ChatSession.new(KB_DIR, model, language)
        session_id = session.id
        is_new_session = True
    else:
        session = load_session(KB_DIR, session_id)
    
    # Render existing history + new user message
    history = []
    for u, a in zip(session.user_turns, session.assistant_texts):
        history.append(html.Div(u, className="bubble bubble-user fade-in"))
        history.append(html.Div(dcc.Markdown(a), className="bubble bubble-ai fade-in"))
    
    history.append(html.Div(message, className="bubble bubble-user fade-in"))
    set_progress((history, html.Div([
        dbc.Spinner(size="sm", color="primary", spinner_class_name="me-2"),
        "Initializing agent..."
    ], className="text-muted small ms-4 mb-2")))

    # Run agent
    wiki_root = str(KB_DIR / "wiki")
    agent = build_query_agent(wiki_root, model, language)
    
    reasoning_steps = []
    response_text = ""
    
    async def run_agent_stream():
        nonlocal response_text
        try:
            run_result = Runner.run_streamed(agent, message, max_turns=MAX_TURNS)
            async for event in run_result.stream_events():
                if isinstance(event, RunItemStreamEvent):
                    item = event.item
                    if item.type == "tool_call_item":
                        raw_item = item.raw_item
                        name = getattr(raw_item, "name", "?")
                        args = getattr(raw_item, "arguments", {})
                        reasoning_steps.append(html.Div([
                            DashIconify(icon="mdi:cog", className="me-1"),
                            f"Thinking: {name}({json.dumps(args)})"
                        ], className="reasoning-block fade-in"))
                        set_progress((history, html.Div(reasoning_steps, className="ms-4 mb-2")))
            response_text = run_result.final_output or ""
        except Exception as e:
            err_str = str(e)
            if "RateLimitError" in type(e).__name__ or "rate" in err_str.lower():
                response_text = (
                    "**Rate limit reached** — the model provider is temporarily limiting requests. "
                    "Please wait a moment and try again, or switch to a different model in Settings."
                )
            else:
                response_text = f"**Error:** {err_str}"

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_agent_stream())
    
    # Record turn
    session.record_turn(message, response_text, [])
    
    # Final history render
    final_history = []
    for u, a in zip(session.user_turns, session.assistant_texts):
        final_history.append(html.Div(u, className="bubble bubble-user fade-in"))
        final_history.append(html.Div(dcc.Markdown(a), className="bubble bubble-ai fade-in"))

    # Clear the loading indicator now that the response is complete
    set_progress((final_history, ""))

    return final_history, "", session_id, trigger_count + 1 if is_new_session else trigger_count

@app.callback(
    Output('sidebar-sessions', 'children'),
    Input('session-update-trigger', 'data'),
    Input('url', 'pathname')
)
def update_sidebar_sessions(trigger, pathname):
    sessions = list_sessions(KB_DIR)
    current_id = pathname.split('/')[-1] if pathname and pathname.startswith('/chat/') else None
    
    session_links = []
    for s in sessions[:15]:
        is_active = s['id'] == current_id
        session_links.append(
            dcc.Link(
                [
                    html.Div(s['title'] or "New Chat", className="text-truncate"),
                    html.Small(s['updated_at'][:10], className="text-muted", style={"fontSize": "0.7rem"})
                ],
                href=f"/chat/{s['id']}",
                className=f"nav-link {'active' if is_active else ''}",
            )
        )
    return session_links

@app.callback(
    Output('chat-history', 'children', allow_duplicate=True),
    Output('current-session-id', 'data', allow_duplicate=True),
    Input('url', 'pathname'),
    State('current-session-id', 'data'),
    prevent_initial_call='initial_duplicate'
)
def load_chat_on_navigation(pathname, current_session_id):
    if pathname and pathname.startswith('/chat/'):
        session_id = pathname.split('/')[-1]
        try:
            session = load_session(KB_DIR, session_id)
            history = []
            for u, a in zip(session.user_turns, session.assistant_texts):
                history.append(html.Div(u, className="bubble bubble-user fade-in"))
                history.append(html.Div(dcc.Markdown(a), className="bubble bubble-ai fade-in"))
            return history, session_id
        except:
            return [], None
    elif pathname == '/chat':
        return [], None
    return dash.no_update, dash.no_update

if __name__ == '__main__':
    app.run(debug=True, port=8051)
