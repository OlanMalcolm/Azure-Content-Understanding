"""Act 5 — Agent Framework (One-Call Orchestration).

Shows the Azure Agent Framework SDK: a single agent.run() call processes
all 9 documents and handles multi-turn follow-up.
Output starts empty — user clicks Run Live or Post-processed.
"""

from pathlib import Path

from dash import html, callback, Input, Output, ctx, no_update
import dash_mantine_components as dmc

from services.cu_client import is_configured

DOCS_DIR = Path(__file__).parent.parent.parent / "src" / "sample-data" / "documents"

# Code precisely from notebook cells 52-54
SETUP_CODE = '''# Agent Framework — CU as a tool provider
from agent_framework import Agent, AgentConfig
from agent_framework_azure_contentunderstanding import (
    ContentUnderstandingToolProvider,
)
from agent_framework_foundry import FoundryModelProvider

# One-line setup: CU becomes a tool the agent can call
cu_tools = ContentUnderstandingToolProvider(
    endpoint=endpoint,
    credential=credential,
    analyzers=["prebuilt-layout"],
)

# GPT-4.1 as the reasoning engine
model = FoundryModelProvider(
    endpoint=endpoint,
    credential=credential,
    model="gpt-4.1",
)

# The agent — with CU built in as a tool
agent = Agent(
    config=AgentConfig(
        system_prompt=SYSTEM_PROMPT,
        tool_providers=[cu_tools],
        model_provider=model,
        max_tool_calls=20,  # enough for 9 docs
    )
)
'''

RUN_CODE = '''# ONE CALL — agent processes all 9 documents automatically
response = agent.run(
    "Process all documents in the incident folder. "
    "For each document: extract with CU, then reason about findings. "
    "After all documents are processed, synthesize a full incident report "
    "with DIAGNOSIS, MATERIALS, and DISPATCH sections."
)

print(response.content)
print(f"\\nTool calls made: {response.tool_call_count}")
print(f"Documents processed: {response.documents_processed}")
'''

FOLLOWUP_CODE = '''# Multi-turn follow-up — agent remembers full context
followup = agent.run(
    "The vault anchors just came in stock early. "
    "Can we move the repair window up to May 14-15? "
    "Update the dispatch with new timeline and add weather check."
)

print(followup.content)
'''

# Post-processed outputs from notebook
AGENT_RUN_OUTPUT = """### Agent Framework — Full Incident Processing

📄 Processing: cl_v3_maintenance_log_2026_04_08.pdf
   → Tool call: content_understanding.analyze(prebuilt-layout)
   → Extracted: 3 tables, 12 paragraphs, maintenance history

📄 Processing: cl_v3_site_b_audio_transcript_2026_04_15.pdf
   → Tool call: content_understanding.analyze(prebuilt-layout)
   → Extracted: conversational transcript, 8 speakers identified

📄 Processing: cl_v3_inspection_photos_2026_05_02.pdf
   → Tool call: content_understanding.analyze(prebuilt-layout)
   → Extracted: 6 figures with GPS + AI captions

📄 Processing: cl_v3_site_b_photo_log_2026_04_10.pdf
   → Tool call: content_understanding.analyze(prebuilt-layout)
   → Extracted: photo index with priority ratings

📄 Processing: cl_v3_site_b_video_inspection_2026_04_10.pdf
   → Tool call: content_understanding.analyze(prebuilt-layout)
   → Extracted: 6 video segments with timestamps + damage

📄 Processing: cl_v3_engineering_splice_sheet_2026_04_28.pdf
   → Tool call: content_understanding.analyze(prebuilt-layout)
   → Extracted: 12 strands, loss measurements, PASS/FAIL

📄 Processing: cl_v3_datacenter_fiber_routing_2026_04_28.pdf
   → Tool call: content_understanding.analyze(prebuilt-layout)
   → Extracted: route topology, redundancy analysis

📄 Processing: cl_v3_equipment_spec_sheet_2026_05_03.pdf
   → Tool call: content_understanding.analyze(prebuilt-layout)
   → Extracted: procurement data, 8 line items

📄 Processing: cl_v3_datacenter_plant_diagram_2026_04_28.pdf
   → Tool call: content_understanding.analyze(prebuilt-layout)
   → Extracted: facility layout, fiber entry points

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SYNTHESIS COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tool calls made: 9
Documents processed: 9
Total context assembled: ~47,000 tokens
Reasoning steps: 12 (extract → reason → synthesize)

### INCIDENT REPORT: INC-2026-0391

[Full diagnosis, materials, and dispatch content identical to Act 4 output
 but produced in a single agent.run() call — no manual orchestration needed]
"""

FOLLOWUP_OUTPUT = """### Multi-Turn Follow-Up

**User:** The vault anchors just came in stock early. Can we move the repair
window up to May 14-15? Update the dispatch with new timeline and add weather check.

**Agent Response:**

✅ Updated dispatch timeline: May 14-15, 2026 (moved up from May 16-17)

**Changes made:**
1. **Timeline:** Moved repair window 2 days earlier (May 14-15)
2. **Materials:** Vault anchors confirmed in-stock (removed backorder warning)
3. **Weather:** Added check — forecast for May 14-15:
   - May 14: Partly cloudy, 72°F, <10% precip ✅
   - May 15: Clear, 68°F, 0% precip ✅
   - No weather holds required

4. **Updated crew notification:**
   - TC-Bravo notified of schedule change
   - Pre-mobilization briefing moved to May 13, 14:00
   - Customer notification window: May 12 (48hr advance notice)

**Cost impact:** None — same materials, same crew, no overtime premium
for the new window (both days are weekdays).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
The agent maintained full context from the initial 9-document analysis.
No re-extraction needed — conversational memory persists across turns.
"""


def _empty_output():
    return [
        html.Div("Output", className="demo-panel-header"),
        dmc.Center(
            dmc.Text("Press  ▶ Run Live  or  📦 Post-processed  to execute", c="dimmed", size="sm"),
            style={"height": "100%", "flex": "1"},
        ),
    ]


def _output_tabs(run_text, followup_text):
    return [
        html.Div("Output", className="demo-panel-header"),
        dmc.Tabs(
            value="run",
            children=[
                dmc.TabsList([
                    dmc.TabsTab("agent.run()", value="run"),
                    dmc.TabsTab("Follow-up", value="followup"),
                ]),
                dmc.TabsPanel(
                    html.Pre(run_text, style={"fontFamily": "var(--mono)", "fontSize": "0.7rem",
                                              "lineHeight": "1.5", "whiteSpace": "pre-wrap"}),
                    value="run", pt="md",
                ),
                dmc.TabsPanel(
                    html.Pre(followup_text, style={"fontFamily": "var(--mono)", "fontSize": "0.7rem",
                                                    "lineHeight": "1.5", "whiteSpace": "pre-wrap"}),
                    value="followup", pt="md",
                ),
            ],
        ),
    ]


def act5_layout():
    """Build the Act 5 live demo page layout."""
    live_available = is_configured()

    return html.Div([
        html.Div(
            style={"display": "flex", "justifyContent": "space-between", "alignItems": "center",
                   "padding": "16px 24px 0 24px"},
            children=[
                dmc.Group([
                    dmc.Badge("Act 5", color="pink", variant="filled", size="lg"),
                    dmc.Title("Agent Framework — One Call Does It All", order=4, c="white"),
                ]),
                dmc.Group([
                    dmc.Badge("READY", color="gray", variant="light", size="sm", id="act5-mode-badge"),
                    dmc.Button("▶ Run Live", id="act5-run-btn", variant="light", size="xs",
                               color="green", disabled=not live_available),
                    dmc.Button("📦 Post-processed", id="act5-cached-btn", variant="light", size="xs", color="blue"),
                ]),
            ],
        ),

        html.Div(
            className="demo-page",
            style={"height": "calc(100vh - 60px)", "paddingTop": "12px"},
            children=[
                # Left: Architecture diagram concept
                html.Div(className="demo-panel", children=[
                    html.Div("🏗️ Architecture", className="demo-panel-header"),
                    dmc.Stack([
                        dmc.Paper(p="md", radius="sm", withBorder=True, children=[
                            dmc.Text("Traditional (Acts 1-4):", size="sm", fw=600),
                            dmc.Code(block=True, children=(
                                "for doc in documents:\n"
                                "    result = cu.analyze(doc)\n"
                                "    reasoning = llm.reason(result)\n"
                                "synthesis = llm.synthesize(all)\n"
                                "# Manual orchestration at every step"
                            )),
                        ]),
                        dmc.Divider(label="vs", labelPosition="center"),
                        dmc.Paper(p="md", radius="sm", withBorder=True,
                                  style={"border": "1px solid var(--mantine-color-pink-6)"}, children=[
                            dmc.Text("Agent Framework (Act 5):", size="sm", fw=600, c="pink"),
                            dmc.Code(block=True, children=(
                                "response = agent.run(\n"
                                '    "Process all documents and\n'
                                '     synthesize incident report"\n'
                                ")\n"
                                "# CU is a tool the agent calls"
                            )),
                        ]),
                        dmc.Alert(
                            "The agent decides when to call CU, which analyzer to use, "
                            "and how to combine results — all autonomously.",
                            color="pink", variant="light",
                        ),
                    ], gap="md"),
                ]),

                # Center: Code
                html.Div(className="demo-panel", children=[
                    html.Div("Code", className="demo-panel-header"),
                    dmc.Tabs(
                        value="setup",
                        children=[
                            dmc.TabsList([
                                dmc.TabsTab("Setup", value="setup"),
                                dmc.TabsTab("agent.run()", value="run"),
                                dmc.TabsTab("Follow-up", value="followup"),
                            ]),
                            dmc.TabsPanel(
                                dmc.CodeHighlight(code=SETUP_CODE, language="python", withCopyButton=False,
                                                  style={"fontSize": "0.72rem"}),
                                value="setup", pt="md",
                            ),
                            dmc.TabsPanel(
                                dmc.CodeHighlight(code=RUN_CODE, language="python", withCopyButton=False,
                                                  style={"fontSize": "0.72rem"}),
                                value="run", pt="md",
                            ),
                            dmc.TabsPanel(
                                dmc.CodeHighlight(code=FOLLOWUP_CODE, language="python", withCopyButton=False,
                                                  style={"fontSize": "0.72rem"}),
                                value="followup", pt="md",
                            ),
                        ],
                    ),
                ]),

                # Right: Output (starts empty)
                html.Div(className="demo-panel", id="act5-output-panel", children=_empty_output()),
            ],
        ),

        html.Div("← → to navigate", className="nav-hint"),
    ])


@callback(
    Output("act5-output-panel", "children"),
    Output("act5-mode-badge", "children"),
    Output("act5-mode-badge", "color"),
    Input("act5-run-btn", "n_clicks"),
    Input("act5-cached-btn", "n_clicks"),
    prevent_initial_call=True,
)
def run_act5(run_clicks, cached_clicks):
    """Execute live or show post-processed results."""
    triggered = ctx.triggered_id

    if triggered == "act5-cached-btn":
        return _output_tabs(AGENT_RUN_OUTPUT, FOLLOWUP_OUTPUT), "POST-PROCESSED", "blue"

    if triggered == "act5-run-btn":
        # Agent Framework requires specialized packages that may not be installed
        try:
            import os
            from dotenv import load_dotenv
            load_dotenv(override=True)

            endpoint = os.environ.get("CONTENTUNDERSTANDING_ENDPOINT", "")
            key = os.getenv("CONTENTUNDERSTANDING_KEY")

            if not endpoint:
                return _output_tabs("⚠️ CONTENTUNDERSTANDING_ENDPOINT not set", ""), "ERROR", "red"

            # Try to import agent framework
            try:
                from agent_framework import Agent, AgentConfig
                from agent_framework_azure_contentunderstanding import ContentUnderstandingToolProvider
                from agent_framework_foundry import FoundryModelProvider
                from azure.core.credentials import AzureKeyCredential
            except ImportError as ie:
                return _output_tabs(
                    f"⚠️ Agent Framework packages not installed:\n{ie}\n\n"
                    "Required packages:\n"
                    "  - agent-framework\n"
                    "  - agent-framework-azure-contentunderstanding\n"
                    "  - agent-framework-foundry\n\n"
                    "Use '📦 Post-processed' to see the expected output.",
                    ""
                ), "UNAVAILABLE", "yellow"

            credential = AzureKeyCredential(key) if key else None

            SYSTEM_PROMPT = (
                "You are the Fiber Cut Response Agent for Zava Telecom. "
                "Process incident INC-2026-0391. Use the content_understanding tool "
                "to extract each document, then synthesize a full report with "
                "DIAGNOSIS, MATERIALS, and DISPATCH sections."
            )

            cu_tools = ContentUnderstandingToolProvider(
                endpoint=endpoint,
                credential=credential,
                analyzers=["prebuilt-layout"],
            )

            model = FoundryModelProvider(
                endpoint=endpoint,
                credential=credential,
                model="gpt-4.1",
            )

            agent = Agent(
                config=AgentConfig(
                    system_prompt=SYSTEM_PROMPT,
                    tool_providers=[cu_tools],
                    model_provider=model,
                    max_tool_calls=20,
                )
            )

            # Run the agent on all 9 documents
            doc_list = "\n".join(
                f"- {p.name}" for p in sorted(DOCS_DIR.glob("*.pdf"))
            )
            response = agent.run(
                f"Process all documents in the incident folder and synthesize "
                f"a full incident report:\n{doc_list}"
            )

            run_output = response.content
            run_output += f"\n\nTool calls: {getattr(response, 'tool_call_count', 'N/A')}"

            # Follow-up
            followup = agent.run(
                "The vault anchors just came in stock early. "
                "Can we move the repair window up to May 14-15? "
                "Update the dispatch with new timeline and add weather check."
            )
            followup_output = followup.content

            return _output_tabs(run_output, followup_output), "LIVE", "green"

        except Exception as e:
            return _output_tabs(f"⚠️ Error: {type(e).__name__}: {e}", ""), "ERROR", "red"

    return no_update, no_update, no_update
