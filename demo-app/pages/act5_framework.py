"""Act 5 — Microsoft Agent Framework integration.

Mirrors notebook cells 52 (setup), 53 (one-call 9-doc run), 54 (multi-turn
follow-up). Uses the real Agent Framework imports:
  from agent_framework import Agent, AgentSession, Content, Message
  from agent_framework.foundry import ContentUnderstandingContextProvider, FoundryChatClient

If the package isn't installed, the live run returns a clear install message
and Pre-processed still works.
"""

import os
from pathlib import Path

import dash_mantine_components as dmc
from dash import Input, Output, callback, ctx, html, no_update
from dotenv import load_dotenv

from services.cu_client import AGENT_MODEL, is_configured

DOCS_DIR = Path(__file__).parent.parent.parent / "src" / "sample-data" / "documents"


# ---------------------------------------------------------------------------
# Displayed code — verbatim from notebook cells 52, 53, 54
# ---------------------------------------------------------------------------

SETUP_CODE = '''# Agent Framework setup
import asyncio
from agent_framework import Agent, AgentSession, Content, Message
from agent_framework.foundry import (
    ContentUnderstandingContextProvider,
    FoundryChatClient,
)
from azure.identity import DefaultAzureCredential as DACred

# The CU context provider — handles CU analysis as part of the agent loop
cu_provider = ContentUnderstandingContextProvider(
    endpoint=ENDPOINT,
    credential=AzureKeyCredential(KEY) if KEY else DACred(),
    analyzer_id="prebuilt-documentSearch",
    max_wait=None,  # block until extraction completes
)

# FoundryChatClient uses the Responses API via AIProjectClient.
foundry_client = FoundryChatClient(
    project_endpoint=ENDPOINT,
    model=AGENT_MODEL,
    credential=DACred(),
)

print("✅ ContentUnderstandingContextProvider configured")
print(f"   Endpoint: {ENDPOINT}")
print(f"   Analyzer: prebuilt-documentSearch")
print(f"   Model: {AGENT_MODEL}")
'''


RUN_CODE = '''# ONE call: 9 PDFs → diagnosis + dispatch
all_pdfs = sorted(DOCS_DIR.glob("cl_v3_*.pdf"))   # 9 documents

async def run_agent_framework_demo():
    async with cu_provider:
        agent = Agent(
            client=foundry_client,
            name="FiberCutResponseAgent",
            instructions=(
                "You are the Fiber Cut Response Agent for Zava Telecom. "
                "You are responding to incident INC-2026-0391 ...\\n"
                "Analyze all attached documents and produce:\\n"
                "1. ROOT CAUSE DIAGNOSIS\\n"
                "2. MATERIALS PLAN\\n"
                "3. DISPATCH SUMMARY\\n"
                "Be precise. Cite specific values from the documents."
            ),
            context_providers=[cu_provider],
        )

        session = AgentSession()

        contents = [Content.from_text(
            "Incident INC-2026-0391 is critical. Analyze all attached field "
            "documents and provide (1) root cause diagnosis, "
            "(2) materials/budget plan, (3) dispatch summary."
        )]
        for pdf in all_pdfs:
            contents.append(Content.from_data(
                pdf.read_bytes(),
                "application/pdf",
                additional_properties={"filename": pdf.name},
            ))

        # ONE call — CU analyzes all 9 docs, injects, agent reasons
        response = await agent.run(
            Message(role="user", contents=contents),
            session=session,
        )
        usage = response.usage_details or {}
        print(response.text)
        print(f"Input tokens:  {usage.get('input_token_count')}")
        print(f"Output tokens: {usage.get('output_token_count')}")
        return session, agent

session, agent = await run_agent_framework_demo()
'''


FOLLOWUP_CODE = '''# Multi-turn follow-up uses cached CU results
async def run_followup():
    async with cu_provider:
        agent = Agent(
            client=foundry_client,
            name="FiberCutResponseAgent",
            instructions=(
                "You have already analyzed all documents for INC-2026-0391. "
                "Answer follow-up questions using the cached document context."
            ),
            context_providers=[cu_provider],
        )

        followup = await agent.run(
            Message(role="user", contents=[Content.from_text(
                "If Vault TV-3 fails entirely, what's the fallback? "
                "How many customers would go dark before we can reroute?"
            )]),
            session=session,   # reuses prior session — CU results cached
        )
        usage = followup.usage_details or {}
        print(followup.text)
        print(f"Input tokens: {usage.get('input_token_count')}")
        print("No CU re-analysis — cached from previous turn.")

await run_followup()
'''


# ---------------------------------------------------------------------------
# Cached outputs — verbatim from notebook cells 53 + 54
# ---------------------------------------------------------------------------

RUN_CACHED = """Documents attached: 9
  cl_v3_datacenter_fiber_routing_2026_04_28.pdf
  cl_v3_datacenter_plant_diagram_2026_04_28.pdf
  cl_v3_engineering_splice_sheet_2026_04_28.pdf
  cl_v3_equipment_spec_sheet_2026_05_03.pdf
  cl_v3_inspection_photos_2026_05_02.pdf
  cl_v3_maintenance_log_2026_Q2.pdf
  cl_v3_site_b_audio_transcript_2026_04_15.pdf
  cl_v3_site_b_photo_log_2026_04_10.pdf
  cl_v3_site_b_video_inspection_2026_04_10.pdf

════════════════════════════════════════════════════════════
AGENT RESPONSE:
════════════════════════════════════════════════════════════
**Incident INC-2026-0391 — Tower Ridge Corridor, Site B, Segment 9**
**Customer Risk:** 42 customers (primary + backup; no redundancy; shared conduit Sections 3-5)

---

## 1. ROOT CAUSE DIAGNOSIS

**Primary Failure:**
- **Vault TV-3 conduit crack progressing:**
  - Crack measured <1cm (Jan), 2cm (Apr), 3cm (May).
  - Water intrusion evident (cl_v3_inspection_photos_2026_05_02.pdf, Photo 1; cl_v3_site_b_video_inspection_2026_04_10.pdf, timestamps 52:30–56:00).
- **Cable stress/micro-bend:**
  - Protective sleeve displaced by 8cm; micro-bend at conduit entry is documented (cl_v3_inspection_photos_2026_05_02.pdf, Photo 2).
  - Fiber strand test (cl_v3_engineering_splice_sheet_2026_04_28.pdf):
    - SM-11: 0.55 dB/km, **FAIL**
    - SM-5, SM-7: Marginal (0.52, 0.48 dB/km), **Conduit pressure, not splice issue** (cl_v3_site_b_audio_transcript_2026_04_15.pdf, 16:15).
- **Pavement heave and ground movement:**
  - 3cm pavement uplift, barriers shifted 15cm (cl_v3_inspection_photos_2026_05_02.pdf, Photos 4 & 5).
  - Cause: recurring ground movement and insufficient conduit mechanical strength.

**Secondary Contributors:**
- **Conduit used is Schedule 40 (installed 2019, pre-standard):**
  - Crush rating inadequate (450 N/100mm, spec requires ≥1000 N/100mm; cl_v3_equipment_spec_sheet_2026_05_03.pdf, table "Conduit Specification Comparison").
  - Not upgraded in 2022–2023 compliance program (cl_v3_datacenter_fiber_routing_2026_04_28.pdf).

**Critical condition:**
- **No redundancy:** Both Route 1 (34 cust) + Route 2 (8 cust) share conduit Sections 3-5 (cl_v3_datacenter_fiber_routing_2026_04_28.pdf, "Redundancy Gap Analysis").
- **Single point of failure:** Conduit crack + mechanical stress → fiber attenuation + imminent outage (confirmed by OTDR and direct observation).

**Conclusion:**
**Root cause is progressive conduit mechanical failure from ground movement/erosion, combined with legacy installation of insufficient conduit specification (Schedule 40 PVC). This resulted in conduit cracking, cable sleeve displacement, fiber micro-bend, and attenuation spikes. Immediate risk of multi-customer outage due to shared, non-redundant conduit.**

---

## 2. MATERIALS PLAN (Budget, Schedule Risk)

**Materials Required** (WO-2026-0391, cl_v3_equipment_spec_sheet_2026_05_03.pdf):
- **Conduit (Schedule 80, orange, solvent weld):**
  - 65m, $28.50/m, **$1,853** (spec-compliant, ≥1000 N/100mm crush).
- **12-SM OS2 fiber cable:**
  - 200m, $4.80/m, **$960**
- **Splice enclosures (SE-24F-UG):**
  - 3 ea, $185, **$555**
- **Splice protectors, cable ties, JB cover, vault anchors:**
  - Miscellaneous, **$2,926** (vault anchors on backorder, ETA 05/15).
- **Subtotal:** **$6,294**
- **Tax (8.5%):** **$535**
- **Total:** **$6,829**

**Schedule Risks:**
- **Vault anchors (critical for secure installation)** on backorder (ETA 05/15; temp shims required until arrival).
- **Lead times:**
  - Conduit: 5 days
  - Cable: 3 days
  - Enclosures: 2 days
  - JB Cover: 7 days
  - Materials overall: **Ready by ~05/15 for full build, temp fix prior**
- **Aerial bypass for Route 2 required during repair:**
  - ~$12K, 2–3 days, ensures backup path while main conduit is replaced (cl_v3_datacenter_fiber_routing_2026_04_28.pdf).

**Budget Confirmation:**
- **Project estimate:** ~$64K (materials + labor, all-inclusive rehab; cl_v3_equipment_spec_sheet_2026_05_03.pdf).
- **Budget cap:** $120K (approved, BUD-2026-TR-009).
- **Current reactive spend:** $74,200 (as of 05/06; cl_v3_maintenance_log_2026_Q2.pdf).

---

## 3. DISPATCH SUMMARY (Crew Assignment, Key Details)

**Primary Crew:**
- **Team A (Fiber Crew):**
  - 11h Q2, $180/h; experienced in conduit and emergency work (cl_v3_maintenance_log_2026_Q2.pdf).
- **GeoCorp (External, for vault measurement/anchors):**
  - $220/h, critical for ensuring proper anchor installation (vault anchors arrive 05/15).

**Personnel:**
- **J. Alvarez (Inspector):**
  - Lead field inspection, validation, and documentation
- **P. Sharma (Senior Field Tech):**
  - Strand and OTDR testing, barrier management

**Tasks:**
1. **Aerial bypass (Route 2):**
   - Deploy prior to conduit replacement, 2–3 days, temporary backup for 8 customers.
2. **Conduit replacement (Schedule 80):**
   - Excavate, remove damaged conduit (Sections 3–5, Vault TV-3), install new; schedule replacement 05/19 (cl_v3_maintenance_log_2026_Q2.pdf).
3. **Fiber pull and splicing:**
   - Install new 12-SM OS2 cable, test all strands post-install (expected loss <0.35 dB/km).
4. **Barrier and pavement restoration:**
   - Reinstall/reinforce Jersey barriers, repair pavement heave, anchor vault(s); use temp shims until permanent anchors delivered.
5. **Verification/Documentation:**
   - Full OTDR test, strand loss verification, photograph and video documentation, sign-off.

**Schedule:**
- **Start aerial bypass ASAP (in-stock materials)**
- **Conduit replacement targeted for 05/19 (pending vault anchor delivery)**
- **Full restoration and verification by 05/22 (allowance for weather/late delivery)**

---

## **Summary Table**

| Item               | Qty   | Cost      | Schedule Risk            |
|--------------------|-------|-----------|--------------------------|
| Conduit (Sch80)    | 65m   | $1,853    | 5 days lead time         |
| Fiber cable        | 200m  | $960      | 3 days lead time         |
| Enclosures         | 3     | $555      | 2 days                   |
| Vault anchors      | 24    | $2,136    | Backordered, ETA 05/15   |
| Bypass (Route 2)   | 1     | $12,000   | 2–3 days (before conduit)|
| Labor (Team A + GeoCorp) | ~40h | $6,680+ | Crew ready, external coordination |
| Total              | —     | ~$64,000  | Within budget cap        |

────────────────────────────────────────────────────────────
Input tokens: 14778
Output tokens: 2021
"""


FOLLOWUP_CACHED = """FOLLOW-UP RESPONSE:
────────────────────────────────────────────────────────────
**Vault TV-3 Failure — Fallback & Customer Impact**

### **1. Fallback Options**

**Field Evidence:**
- **No native redundancy:**
  - Both Route 1 (34 customers) and Route 2 (8 customers) share the same conduit (Sections 3–5) through Vault TV-3.
    - Reference:
      - cl_v3_datacenter_fiber_routing_2026_04_28.pdf ("Redundancy Gap Analysis": "No alternative physical path exists. Single point of failure.")
      - cl_v3_engineering_splice_sheet_2026_04_28.pdf ("Route 2 shares conduit with Route 1 … NO redundancy.")
- **Fallback plan:**
  - **Aerial bypass for Route 2 backup** recommended as immediate (temporary) action.
    - Cost: ~$12,000, install time 2–3 days (cl_v3_datacenter_fiber_routing_2026_04_28.pdf).
    - Only covers Route 2 (8 customers). Route 1 remains unprotected until conduit repair is completed.

### **2. Customer Impact — Immediate Outage Upon Vault TV-3 Failure**

- **Total customers exposed:**
  - Route 1: 34
  - Route 2: 8
  - **Total: 42**
    - Reference: cl_v3_site_b_audio_transcript_2026_04_15.pdf ("Total exposure: 34 (Rt1) + 8 (Rt2) = 42 customers, no redundancy")
- **If conduit at Vault TV-3 fails before bypass is installed:**
  - **All 42 customers lose both primary and backup fiber connectivity (dark).**
    - "If conduit fails, BOTH routes down. 42 cust, NO redundancy." — cl_v3_datacenter_fiber_routing_2026_04_28.pdf

### **3. Restoration Timeline**

- **Route 2 aerial bypass (8 customers):**
  - Can be mobilized in ~2–3 days if materials/crew are available (cl_v3_equipment_spec_sheet_2026_05_03.pdf, "Immediate: Aerial bypass for Route 2 before conduit repair")
- **Route 1 (34 customers):**
  - **No bypass/fallback:** Remain dark until new conduit and fiber are installed (target: 05/19–05/22 per materials/anchors delivery).

### **Summary**

- **Immediate fallback:** Only available for Route 2 backup (8 customers), requires quick deployment.
- **If TV-3 fails before bypass:** **All 42 customers will go dark.**
- **As soon as bypass is active:** 34 customers (Route 1) remain down until partial/full repair; 8 customers (Route 2) are temporarily restored.

────────────────────────────────────────────────────────────
Input tokens: 16829
No CU re-analysis — cached from previous turn
"""


# ---------------------------------------------------------------------------
# Live runner — async one-call + follow-up. Falls back to clear message
# when agent_framework isn't installed.
# ---------------------------------------------------------------------------

AGENT_INSTRUCTIONS = (
    "You are the Fiber Cut Response Agent for Zava Telecom. "
    "You are responding to incident INC-2026-0391: signal degradation detected "
    "on Tower Ridge Corridor, Site B, Segment 9. 42 customers at risk — "
    "primary and backup share conduit, no redundancy path available.\n\n"
    "Analyze all attached documents and produce:\n"
    "1. ROOT CAUSE DIAGNOSIS — what failed and why\n"
    "2. MATERIALS PLAN — what's needed, cost, schedule risks\n"
    "3. DISPATCH SUMMARY — crew assignment with key details\n\n"
    "Be precise. Cite specific values from the documents."
)


def _run_live():
    try:
        import asyncio
        from agent_framework import Agent, AgentSession, Content, Message
        from agent_framework.foundry import (
            ContentUnderstandingContextProvider,
            FoundryChatClient,
        )
        from azure.identity import DefaultAzureCredential
        from azure.core.credentials import AzureKeyCredential
    except ImportError as e:
        msg = (
            f"⚠️ Agent Framework not installed: {e}\n\n"
            "To enable the live run:\n"
            "    pip install agent-framework-azure-contentunderstanding "
            "agent-framework-foundry --pre\n\n"
            "Use 📦 Pre-processed to see the notebook output."
        )
        return msg, ""

    load_dotenv(override=True)
    endpoint = os.environ.get("CONTENTUNDERSTANDING_ENDPOINT", "")
    key = os.environ.get("CONTENTUNDERSTANDING_KEY")

    if not endpoint:
        return "⚠️ CONTENTUNDERSTANDING_ENDPOINT not configured.", ""

    cu_credential = AzureKeyCredential(key) if key else DefaultAzureCredential()
    foundry_credential = DefaultAzureCredential()

    cu_provider = ContentUnderstandingContextProvider(
        endpoint=endpoint,
        credential=cu_credential,
        analyzer_id="prebuilt-documentSearch",
        max_wait=None,
    )
    foundry_client = FoundryChatClient(
        project_endpoint=endpoint,
        model=AGENT_MODEL,
        credential=foundry_credential,
    )

    all_pdfs = sorted(DOCS_DIR.glob("cl_v3_*.pdf"))

    async def _run():
        async with cu_provider:
            agent = Agent(
                client=foundry_client,
                name="FiberCutResponseAgent",
                instructions=AGENT_INSTRUCTIONS,
                context_providers=[cu_provider],
            )
            session = AgentSession()

            contents = [Content.from_text(
                "Incident INC-2026-0391 is critical. Analyze all attached field "
                "documents and provide: (1) root cause diagnosis, "
                "(2) materials/budget plan, (3) dispatch summary for the repair crew."
            )]
            for pdf in all_pdfs:
                contents.append(Content.from_data(
                    pdf.read_bytes(),
                    "application/pdf",
                    additional_properties={"filename": pdf.name},
                ))

            response = await agent.run(
                Message(role="user", contents=contents),
                session=session,
            )
            usage = response.usage_details or {}
            run_text = (
                f"Documents attached: {len(all_pdfs)}\n"
                + "\n".join(f"  {p.name}" for p in all_pdfs)
                + "\n\n══════════════════════════════════════════════\n"
                + "AGENT RESPONSE:\n"
                + "══════════════════════════════════════════════\n"
                + (response.text or "")
                + f"\n──────────────────────────────────────────────\n"
                + f"Input tokens:  {usage.get('input_token_count', 'N/A')}\n"
                + f"Output tokens: {usage.get('output_token_count', 'N/A')}"
            )

            # Follow-up — cached session, no new CU calls
            followup_response = await agent.run(
                Message(role="user", contents=[Content.from_text(
                    "If Vault TV-3 fails entirely, what's the fallback? "
                    "How many customers would go dark before we can reroute?"
                )]),
                session=session,
            )
            fu = followup_response.usage_details or {}
            followup_text = (
                "FOLLOW-UP RESPONSE:\n"
                "──────────────────────────────────────────────\n"
                + (followup_response.text or "")
                + f"\n──────────────────────────────────────────────\n"
                + f"Input tokens: {fu.get('input_token_count', 'N/A')}\n"
                + "No CU re-analysis — cached from previous turn"
            )
            return run_text, followup_text

    return asyncio.run(_run())


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

PRE_STYLE = {
    "fontFamily": "var(--mono)",
    "fontSize": "0.70rem",
    "lineHeight": "1.5",
    "whiteSpace": "pre-wrap",
}


def _empty_output():
    return [
        html.Div("Output", className="demo-panel-header"),
        dmc.Center(
            dmc.Text(
                "Press  \u25B6 Run Live  or  \U0001F4E6 Pre-processed  to execute",
                c="dimmed", size="sm",
            ),
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
                dmc.TabsPanel(html.Pre(run_text, style=PRE_STYLE),
                              value="run", pt="md"),
                dmc.TabsPanel(html.Pre(followup_text, style=PRE_STYLE),
                              value="followup", pt="md"),
            ],
        ),
    ]


def act5_layout():
    live_available = is_configured()

    return html.Div([
        html.Div(
            style={
                "display": "flex", "justifyContent": "space-between", "alignItems": "center",
                "padding": "16px 24px 0 24px",
            },
            children=[
                dmc.Group([
                    dmc.Badge("Act 5", color="grape", variant="filled", size="lg"),
                    dmc.Title("Agent Framework — One Call, Nine Documents",
                              order=4, c="white"),
                ]),
                dmc.Group([
                    dmc.Badge("READY", color="gray", variant="light", size="sm",
                              id="act5-mode-badge"),
                    dmc.Button("\u25B6 Run Live", id="act5-run-btn", variant="light",
                               size="xs", color="green", disabled=not live_available),
                    dmc.Button("\U0001F4E6 Pre-processed", id="act5-cached-btn",
                               variant="light", size="xs", color="blue"),
                ]),
            ],
        ),

        html.Div(
            className="demo-page",
            style={"height": "calc(100vh - 60px)", "paddingTop": "12px"},
            children=[
                # Left: Manual pipeline collapses into one agent call
                html.Div(className="demo-panel", children=[
                    html.Div("\u26A1 Manual Pipeline \u2192 Agent Framework",
                             className="demo-panel-header"),
                    dmc.Stack([
                        # Manual pipeline card (muted)
                        dmc.Paper(
                            p="sm", radius="md", withBorder=True,
                            style={
                                "background": "rgba(255,255,255,0.02)",
                                "borderColor": "rgba(255,255,255,0.12)",
                            },
                            children=[
                                dmc.Group([
                                    dmc.Badge("Acts 1\u20134", color="gray",
                                              variant="light", size="sm"),
                                    dmc.Text("Manual orchestration",
                                             size="xs", c="dimmed", fs="italic"),
                                ], justify="space-between", mb=8),
                                dmc.List(
                                    spacing=2, size="xs",
                                    children=[
                                        dmc.ListItem(dmc.Text(
                                            "client.begin_analyze_binary()",
                                            size="xs", ff="var(--mono)")),
                                        dmc.ListItem(dmc.Text(
                                            "poller.result()",
                                            size="xs", ff="var(--mono)")),
                                        dmc.ListItem(dmc.Text(
                                            "to_llm_input(result)",
                                            size="xs", ff="var(--mono)")),
                                        dmc.ListItem(dmc.Text(
                                            "Assemble FULL_CONTEXT",
                                            size="xs", ff="var(--mono)")),
                                        dmc.ListItem(dmc.Text(
                                            "3 \u00D7 chat.completions.create()",
                                            size="xs", ff="var(--mono)")),
                                    ],
                                ),
                                dmc.Text("~50 lines of glue code",
                                         size="xs", c="dimmed", mt=8, fs="italic"),
                            ],
                        ),

                        # Arrow connector
                        dmc.Center(
                            dmc.Stack([
                                dmc.Text("\u2193", size="xl", c="grape",
                                         fw=700, ta="center",
                                         style={"lineHeight": "1"}),
                                dmc.Text("collapses to", size="xs",
                                         c="dimmed", ta="center"),
                            ], gap=2),
                        ),

                        # Agent Framework card (accent/grape)
                        dmc.Paper(
                            p="sm", radius="md", withBorder=True,
                            style={
                                "background": "rgba(167,139,250,0.06)",
                                "borderColor": "var(--purple)",
                                "boxShadow": "0 0 0 1px rgba(167,139,250,0.15)",
                            },
                            children=[
                                dmc.Group([
                                    dmc.Badge("Act 5", color="grape",
                                              variant="filled", size="sm"),
                                    dmc.Text("Agent Framework",
                                             size="xs", c="grape.3", fw=600),
                                ], justify="space-between", mb=8),
                                dmc.List(
                                    spacing=2, size="xs",
                                    children=[
                                        dmc.ListItem(dmc.Text(
                                            "ContentUnderstandingContextProvider",
                                            size="xs", ff="var(--mono)")),
                                        dmc.ListItem(dmc.Text(
                                            "FoundryChatClient",
                                            size="xs", ff="var(--mono)")),
                                        dmc.ListItem(dmc.Text(
                                            "await agent.run(message)",
                                            size="xs", ff="var(--mono)")),
                                        dmc.ListItem(dmc.Text(
                                            "Multi-turn cache via AgentSession",
                                            size="xs", ff="var(--mono)")),
                                    ],
                                ),
                                dmc.Text("~10 lines \u2014 one call",
                                         size="xs", c="grape.3",
                                         mt=8, fw=600),
                            ],
                        ),

                        # Insight callout
                        dmc.Alert(
                            color="grape", variant="light", radius="md",
                            icon="\U0001F4A1",
                            children=dmc.Text(
                                "The provider auto-detects file attachments, "
                                "runs CU analysis, formats results, and caches "
                                "across turns. No glue code.",
                                size="xs",
                            ),
                            p="xs",
                        ),
                    ], gap="sm"),
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
                                dmc.CodeHighlight(code=SETUP_CODE, language="python",
                                                  withCopyButton=False,
                                                  style={"fontSize": "0.70rem"}),
                                value="setup", pt="md",
                            ),
                            dmc.TabsPanel(
                                dmc.CodeHighlight(code=RUN_CODE, language="python",
                                                  withCopyButton=False,
                                                  style={"fontSize": "0.70rem"}),
                                value="run", pt="md",
                            ),
                            dmc.TabsPanel(
                                dmc.CodeHighlight(code=FOLLOWUP_CODE, language="python",
                                                  withCopyButton=False,
                                                  style={"fontSize": "0.70rem"}),
                                value="followup", pt="md",
                            ),
                        ],
                    ),
                ]),

                # Right: Output (starts empty)
                html.Div(className="demo-panel", id="act5-output-panel",
                         children=_empty_output()),
            ],
        ),

        html.Div("\u2190 \u2192 to navigate", className="nav-hint"),
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
    triggered = ctx.triggered_id

    if triggered == "act5-cached-btn":
        return (_output_tabs(RUN_CACHED, FOLLOWUP_CACHED),
                "PRE-PROCESSED", "blue")

    if triggered == "act5-run-btn":
        try:
            run_text, followup_text = _run_live()
            badge = "ERROR" if run_text.startswith("\u26A0") else "LIVE"
            color = "red" if badge == "ERROR" else "green"
            return _output_tabs(run_text, followup_text), badge, color
        except Exception as e:
            return (_output_tabs(f"\u26A0\uFE0F {type(e).__name__}: {e}", ""),
                    "ERROR", "red")

    return no_update, no_update, no_update
