"""Act 4 — Synthesis & Dispatch.

Shows the agent assembling all 9 extracted documents into a unified context,
running DIAGNOSE / IDENTIFY / DISPATCH steps, and producing dispatch email.
Output starts empty — user clicks Run Live or Post-processed.
"""

from pathlib import Path

from dash import html, callback, Input, Output, ctx, no_update
import dash_mantine_components as dmc

from services.cu_client import is_configured

DOCS_DIR = Path(__file__).parent.parent.parent / "src" / "sample-data" / "documents"

# Code precisely from notebook cells 42-45
ASSEMBLE_CODE = '''# Assemble ALL 9 documents into unified context
all_documents = [
    maintenance_log, audio_transcript, inspection_photos,
    photo_log, video_inspection, splice_sheet,
    fiber_routing, equipment_spec, plant_diagram,
]
all_results = [
    maint_result, audio_result, photos_result,
    photo_log_result, video_result, splice_result,
    routing_result, equipment_result, plant_result,
]
LABELS = [
    "Maintenance Log (Apr 8)", "Audio Transcript (Apr 15)",
    "Inspection Photos (May 2)", "Photo Log (Apr 10)",
    "Video Inspection (Apr 10)", "Splice Sheet (Apr 28)",
    "Fiber Routing (Apr 28)", "Equipment Spec (May 3)",
    "Plant Diagram (Apr 28)",
]

# Assemble the full context
context = ""
for label, result in zip(LABELS, all_results):
    context += f"\\n{'═'*60}\\n📄 {label}\\n{'═'*60}\\n"
    context += to_llm_input(result) + "\\n"

print(f"✅ 9 documents assembled — {len(context):,} chars of context")
'''

DIAGNOSE_CODE = '''# STEP 1: DIAGNOSE — What happened?
diagnosis = agent_client.chat.completions.create(
    model="gpt-4.1",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": context + "\\n\\nDIAGNOSE this incident. "
         "Root cause, affected segments, severity, timeline."},
    ],
    temperature=0.2, max_tokens=800,
)
print(diagnosis.choices[0].message.content)
'''

DISPATCH_CODE = '''# STEP 2: IDENTIFY materials + STEP 3: DISPATCH
materials = agent_client.chat.completions.create(
    model="gpt-4.1",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": context + "\\n\\nIDENTIFY required materials, "
         "crew, and estimated cost. Reference the equipment spec."},
    ],
    temperature=0.2, max_tokens=600,
)

dispatch = agent_client.chat.completions.create(
    model="gpt-4.1",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": context + "\\n\\nDISPATCH: Write a crew "
         "dispatch email with timeline, materials, safety notes. "
         "Include budget reference."},
    ],
    temperature=0.3, max_tokens=800,
)
print("═══ MATERIALS ═══")
print(materials.choices[0].message.content)
print("\\n═══ DISPATCH EMAIL ═══")
print(dispatch.choices[0].message.content)
'''

# Post-processed outputs from notebook
DIAGNOSIS_OUTPUT = """### ROOT CAUSE ANALYSIS — Incident INC-2026-0391

**Primary Finding:** Recurring fiber degradation in shared conduit at Vault TV-3,
Segment 9 (~847m mark). Progressive structural failure of concrete vault wall
creating sustained pressure on fiber bundle.

**Root Cause Chain:**
1. Concrete crack (NE-SW) propagating due to thermal cycling + ground settling
2. Water intrusion through crack → mineral deposits on cable sheath
3. Conduit compression at crack point → micro-bend on strands 4, 5, 7, 11
4. January emergency splice was palliative — did not address structural cause
5. Crack grew from 6" (Jan) → 18" (May) — 3× in 4 months

**Severity:** CRITICAL — no redundancy path exists. Route 2 shares conduit
with Route 1 in Sections 3-5. Total loss = 42 enterprise customers dark.

**Timeline:**
- Apr 8: Maintenance log flags "recurring" + 0.82 dB loss (was 0.15 baseline)
- Apr 10: Photo log confirms crack propagation; video finds heave in Section 5
- Apr 15: Audio transcript — techs confirm "worse than January"
- Apr 28: Splice sheet — strands SM-5 & SM-11 at FAIL/MARGINAL thresholds
- May 2: Inspection photos — crack now 18", active water flow confirmed
- May 3: Equipment spec ordered for full segment replacement

**Estimated time to failure:** 2-3 weeks at current deterioration rate.
"""

MATERIALS_OUTPUT = """### MATERIALS & CREW REQUIREMENTS

**Crew Dispatch:**
- 2× certified splicers (OS2 rated) — 4 hours each
- 1× civil crew (vault repair) — 6 hours
- 1× project engineer (on-site supervision)

**Critical Materials (from Equipment Spec):**
| Item                         | Qty  | Status       | Cost    |
|------------------------------|------|--------------|---------|
| G.652D 12-strand SM OS2     | 50m  | In Stock     | $1,450  |
| Vault repair kit (concrete) | 1    | In Stock     | $890    |
| Splice protection sleeves   | 24   | In Stock     | $144    |
| OTDR calibration reference  | 1    | In Stock     | $0      |
| Conduit sealant (hydro)     | 2L   | In Stock     | $215    |
| Vault Anchors (VA-HEL-6FT)  | 6    | ⚠️ BACKORDER | $780    |

**Total:** $6,829 of $120,000 budget (5.7%)
**Critical Path:** Vault anchors on backorder — ETA May 15.
Schedule repair for May 16-17 window.
"""

DISPATCH_OUTPUT = """### DISPATCH EMAIL — Crew Orders

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TO: Fiber Repair Crew Bravo (TC-Bravo)
CC: K. Okonkwo (Inspector), J. Martinez (Lead Tech)
SUBJECT: [URGENT] Segment 9 Full Replacement — Vault TV-3
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DISPATCH ORDER: DO-2026-0391-A
PRIORITY: IMMEDIATE (no redundancy)
WINDOW: May 16-17, 2026 (06:00 - 18:00 both days)

SCOPE OF WORK:
1. Full segment replacement — Section 9, Vault TV-3 to TV-4 (50m)
2. Vault structural repair (concrete + sealant)
3. Re-splice all 12 strands with 0.10 dB target per splice
4. OTDR verification: full span + per-splice validation
5. Conduit separation: isolate Route 1 from Route 2

SAFETY NOTES:
⚠️ Active water intrusion — dewatering required before entry
⚠️ Shared vault — confirm Route 2 customer notification (42 affected)
⚠️ Confined space — 2-person minimum with gas monitoring

BUDGET: Pre-approved $6,829 (PO #PO-2026-0391)
NOTE: Vault anchors ETA May 15. Confirm delivery before mobilization.

— Zava Telecom Fiber Response Agent (automated)
   Incident INC-2026-0391
"""


def _empty_output():
    return [
        html.Div("Output", className="demo-panel-header"),
        dmc.Center(
            dmc.Text("Press  ▶ Run Live  or  📦 Post-processed  to execute", c="dimmed", size="sm"),
            style={"height": "100%", "flex": "1"},
        ),
    ]


def _output_tabs(diagnosis_text, materials_text, dispatch_text):
    return [
        html.Div("Output", className="demo-panel-header"),
        dmc.Tabs(
            value="diagnosis",
            children=[
                dmc.TabsList([
                    dmc.TabsTab("Diagnosis", value="diagnosis"),
                    dmc.TabsTab("Materials", value="materials"),
                    dmc.TabsTab("Dispatch", value="dispatch"),
                ]),
                dmc.TabsPanel(
                    html.Pre(diagnosis_text, style={"fontFamily": "var(--mono)", "fontSize": "0.7rem",
                                                    "lineHeight": "1.5", "whiteSpace": "pre-wrap"}),
                    value="diagnosis", pt="md",
                ),
                dmc.TabsPanel(
                    html.Pre(materials_text, style={"fontFamily": "var(--mono)", "fontSize": "0.7rem",
                                                    "lineHeight": "1.5", "whiteSpace": "pre-wrap"}),
                    value="materials", pt="md",
                ),
                dmc.TabsPanel(
                    html.Pre(dispatch_text, style={"fontFamily": "var(--mono)", "fontSize": "0.7rem",
                                                    "lineHeight": "1.5", "whiteSpace": "pre-wrap"}),
                    value="dispatch", pt="md",
                ),
            ],
        ),
    ]


def act4_layout():
    """Build the Act 4 live demo page layout."""
    live_available = is_configured()

    return html.Div([
        html.Div(
            style={"display": "flex", "justifyContent": "space-between", "alignItems": "center",
                   "padding": "16px 24px 0 24px"},
            children=[
                dmc.Group([
                    dmc.Badge("Act 4", color="orange", variant="filled", size="lg"),
                    dmc.Title("The Agent Thinks — Synthesis & Dispatch", order=4, c="white"),
                ]),
                dmc.Group([
                    dmc.Badge("READY", color="gray", variant="light", size="sm", id="act4-mode-badge"),
                    dmc.Button("▶ Run Live", id="act4-run-btn", variant="light", size="xs",
                               color="green", disabled=not live_available),
                    dmc.Button("📦 Post-processed", id="act4-cached-btn", variant="light", size="xs", color="blue"),
                ]),
            ],
        ),

        html.Div(
            className="demo-page",
            style={"height": "calc(100vh - 60px)", "paddingTop": "12px"},
            children=[
                # Left: Document overview
                html.Div(className="demo-panel", children=[
                    html.Div("📚 9 Documents Assembled", className="demo-panel-header"),
                    dmc.Stack([
                        dmc.Paper(p="xs", radius="sm", withBorder=True, children=[
                            dmc.Text("All 9 extracted documents feed into the synthesis agent:", size="xs", c="dimmed"),
                        ]),
                        dmc.List([
                            dmc.ListItem(dmc.Text("Maintenance Log (Apr 8)", size="xs")),
                            dmc.ListItem(dmc.Text("Audio Transcript (Apr 15)", size="xs")),
                            dmc.ListItem(dmc.Text("Inspection Photos (May 2)", size="xs")),
                            dmc.ListItem(dmc.Text("Photo Log (Apr 10)", size="xs")),
                            dmc.ListItem(dmc.Text("Video Inspection (Apr 10)", size="xs")),
                            dmc.ListItem(dmc.Text("Splice Sheet (Apr 28)", size="xs")),
                            dmc.ListItem(dmc.Text("Fiber Routing (Apr 28)", size="xs")),
                            dmc.ListItem(dmc.Text("Equipment Spec (May 3)", size="xs")),
                            dmc.ListItem(dmc.Text("Plant Diagram (Apr 28)", size="xs")),
                        ], size="sm"),
                        dmc.Divider(),
                        dmc.Text("Agent performs 3 reasoning steps:", size="xs", fw=600),
                        dmc.List([
                            dmc.ListItem(dmc.Text("DIAGNOSE — root cause analysis", size="xs")),
                            dmc.ListItem(dmc.Text("IDENTIFY — materials & crew", size="xs")),
                            dmc.ListItem(dmc.Text("DISPATCH — crew deployment email", size="xs")),
                        ], size="sm", type="ordered"),
                    ], gap="sm"),
                ]),

                # Center: Code
                html.Div(className="demo-panel", children=[
                    html.Div("Code", className="demo-panel-header"),
                    dmc.Tabs(
                        value="assemble",
                        children=[
                            dmc.TabsList([
                                dmc.TabsTab("Assemble", value="assemble"),
                                dmc.TabsTab("Diagnose", value="diagnose"),
                                dmc.TabsTab("Dispatch", value="dispatch"),
                            ]),
                            dmc.TabsPanel(
                                dmc.CodeHighlight(code=ASSEMBLE_CODE, language="python", withCopyButton=False,
                                                  style={"fontSize": "0.72rem"}),
                                value="assemble", pt="md",
                            ),
                            dmc.TabsPanel(
                                dmc.CodeHighlight(code=DIAGNOSE_CODE, language="python", withCopyButton=False,
                                                  style={"fontSize": "0.72rem"}),
                                value="diagnose", pt="md",
                            ),
                            dmc.TabsPanel(
                                dmc.CodeHighlight(code=DISPATCH_CODE, language="python", withCopyButton=False,
                                                  style={"fontSize": "0.72rem"}),
                                value="dispatch", pt="md",
                            ),
                        ],
                    ),
                ]),

                # Right: Output (starts empty)
                html.Div(className="demo-panel", id="act4-output-panel", children=_empty_output()),
            ],
        ),

        html.Div("← → to navigate", className="nav-hint"),
    ])


@callback(
    Output("act4-output-panel", "children"),
    Output("act4-mode-badge", "children"),
    Output("act4-mode-badge", "color"),
    Input("act4-run-btn", "n_clicks"),
    Input("act4-cached-btn", "n_clicks"),
    prevent_initial_call=True,
)
def run_act4(run_clicks, cached_clicks):
    """Execute live or show post-processed results."""
    triggered = ctx.triggered_id

    if triggered == "act4-cached-btn":
        return _output_tabs(DIAGNOSIS_OUTPUT, MATERIALS_OUTPUT, DISPATCH_OUTPUT), "POST-PROCESSED", "blue"

    if triggered == "act4-run-btn":
        import os
        from dotenv import load_dotenv
        from azure.ai.contentunderstanding import ContentUnderstandingClient, to_llm_input
        from azure.core.credentials import AzureKeyCredential
        from openai import AzureOpenAI

        load_dotenv(override=True)
        endpoint = os.environ.get("CONTENTUNDERSTANDING_ENDPOINT", "")
        key = os.getenv("CONTENTUNDERSTANDING_KEY")

        if not endpoint:
            return _output_tabs("⚠️ CONTENTUNDERSTANDING_ENDPOINT not set", "", ""), "ERROR", "red"

        credential = AzureKeyCredential(key) if key else None
        client = ContentUnderstandingClient(endpoint=endpoint, credential=credential,
                                            user_agent="build26-DEM331-demo/1.0.0")
        agent_client = AzureOpenAI(azure_endpoint=endpoint, api_key=key, api_version="2025-04-01-preview")

        SYSTEM_PROMPT = (
            "You are the Fiber Cut Response Agent for Zava Telecom. "
            "You are processing incident INC-2026-0391 — a critical shared-conduit fiber degradation. "
            "You have 9 extracted documents as context. Provide structured, actionable analysis."
        )

        # Analyze all 9 documents
        ALL_DOCS = [
            "cl_v3_maintenance_log_2026_04_08.pdf",
            "cl_v3_site_b_audio_transcript_2026_04_15.pdf",
            "cl_v3_inspection_photos_2026_05_02.pdf",
            "cl_v3_site_b_photo_log_2026_04_10.pdf",
            "cl_v3_site_b_video_inspection_2026_04_10.pdf",
            "cl_v3_engineering_splice_sheet_2026_04_28.pdf",
            "cl_v3_datacenter_fiber_routing_2026_04_28.pdf",
            "cl_v3_equipment_spec_sheet_2026_05_03.pdf",
            "cl_v3_datacenter_plant_diagram_2026_04_28.pdf",
        ]
        LABELS = [
            "Maintenance Log (Apr 8)", "Audio Transcript (Apr 15)",
            "Inspection Photos (May 2)", "Photo Log (Apr 10)",
            "Video Inspection (Apr 10)", "Splice Sheet (Apr 28)",
            "Fiber Routing (Apr 28)", "Equipment Spec (May 3)",
            "Plant Diagram (Apr 28)",
        ]

        # Build full context from CU extraction of all docs
        context = ""
        try:
            for label, filename in zip(LABELS, ALL_DOCS):
                doc_path = DOCS_DIR / filename
                if not doc_path.exists():
                    context += f"\n{'═'*60}\n📄 {label}\n{'═'*60}\n(file not found)\n"
                    continue
                with open(doc_path, "rb") as f:
                    poller = client.begin_analyze_binary(analyzer_id="prebuilt-layout", binary_input=f.read())
                result = poller.result()
                context += f"\n{'═'*60}\n📄 {label}\n{'═'*60}\n"
                if result.contents:
                    context += to_llm_input(result) + "\n"
                else:
                    context += "(empty extraction)\n"
        except Exception as e:
            return _output_tabs(f"⚠️ Error extracting documents: {e}", "", ""), "ERROR", "red"

        # DIAGNOSE
        try:
            diag = agent_client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": context + "\n\nDIAGNOSE this incident. "
                     "Root cause, affected segments, severity, timeline."},
                ],
                temperature=0.2, max_tokens=800,
            )
            diagnosis = diag.choices[0].message.content
        except Exception as e:
            diagnosis = f"⚠️ Error: {e}"

        # IDENTIFY materials
        try:
            mat = agent_client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": context + "\n\nIDENTIFY required materials, "
                     "crew, and estimated cost. Reference the equipment spec."},
                ],
                temperature=0.2, max_tokens=600,
            )
            materials = mat.choices[0].message.content
        except Exception as e:
            materials = f"⚠️ Error: {e}"

        # DISPATCH
        try:
            disp = agent_client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": context + "\n\nDISPATCH: Write a crew "
                     "dispatch email with timeline, materials, safety notes. "
                     "Include budget reference."},
                ],
                temperature=0.3, max_tokens=800,
            )
            dispatch = disp.choices[0].message.content
        except Exception as e:
            dispatch = f"⚠️ Error: {e}"

        return _output_tabs(diagnosis, materials, dispatch), "LIVE", "green"

    return no_update, no_update, no_update
