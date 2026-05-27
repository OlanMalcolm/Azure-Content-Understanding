"""Act 1 — CU Extraction vs Local PyMuPDF Comparison.

Shows the maintenance log document, the extraction code, and side-by-side output
comparing local PyMuPDF text vs Azure Content Understanding structured output.
Output panel starts empty — user clicks "Run Live" or "Cached" to populate.
"""

from pathlib import Path

from dash import html, callback, Input, Output, ctx, no_update
import dash_mantine_components as dmc

from components.doc_viewer import create_doc_viewer
from services.cu_client import is_configured

# Path to the sample PDF
SAMPLE_PDF = Path(__file__).parent.parent.parent / "src" / "sample-data" / "documents" / "cl_v3_maintenance_log_2026_Q2.pdf"

# Code shown to the audience
EXTRACTION_CODE = '''import os
from pathlib import Path
from dotenv import load_dotenv
from azure.ai.contentunderstanding import ContentUnderstandingClient
from azure.core.credentials import AzureKeyCredential

load_dotenv(override=True)
ENDPOINT = os.environ["CONTENTUNDERSTANDING_ENDPOINT"]
KEY = os.getenv("CONTENTUNDERSTANDING_KEY")

# Initialize CU client
credential = AzureKeyCredential(KEY) if KEY else DefaultAzureCredential()
client = ContentUnderstandingClient(
    endpoint=ENDPOINT,
    credential=credential,
)

# Single API call — handles tables, figures,
# selection marks, QR codes, signatures
maintenance_log = Path("sample-data/documents/cl_v3_maintenance_log_2026_Q2.pdf")

with open(maintenance_log, "rb") as f:
    poller = client.begin_analyze_binary(
        analyzer_id="prebuilt-documentSearch",
        binary_input=f.read(),
    )
result = poller.result()

# What the agent receives:
cu_markdown = result.contents[0].markdown
print(cu_markdown[:2000])
'''

PYMUPDF_CODE = '''import pymupdf
from pathlib import Path

# Local extraction — no cloud service needed
maintenance_log = Path("sample-data/documents/cl_v3_maintenance_log_2026_Q2.pdf")
doc = pymupdf.open(str(maintenance_log))
raw_text = ""
for page in doc:
    raw_text += page.get_text()

# What the agent receives:
print(f"Pages: {len(doc)}")
print(raw_text[:2000])
'''

# Pre-cached outputs (used when "Cached" button is pressed)
PYMUPDF_OUTPUT = """Pages: 2
══════════════════════════════════════════════════════════════
RAW TEXT OUTPUT (first 2000 chars):
══════════════════════════════════════════════════════════════

ZAVA TELECOM — SITE MAINTENANCE LOG
Reporting Period: Q2 2026 (April–June)
Site: Tower Ridge Corridor, Site B
Segment: 9 — Primary backbone, shared conduit
Document ID: ML-2026-Q2-009
QR: [Unable to extract]
──────────────────────────────────────────────
MAINTENANCE ACTIVITY RECORD
Date Activity Type Tech Crew Status Notes Cost Estimate
2026-04-01 Scheduled Inspection Visual Survey TC-Alpha Complete Baseline check $0
2026-04-08 Emergency Repair Splice Repair TC-Bravo Complete 2 strands failed $1,200
2026-04-15 Follow-up Inspection Physical + Audio TC-Alpha Complete Post-repair verify $0
2026-04-22 Conduit Assessment Structural TC-Charlie In Progress Crack documented $400
...
(columns misaligned, table structure lost, selection marks missing)
"""

CU_OUTPUT = """### CU Extraction: Structured Markdown

| Date | Activity | Type | Crew | Status | Notes | Cost |
|------|----------|------|------|--------|-------|------|
| 2026-04-01 | Scheduled Inspection | Visual Survey | TC-Alpha | ✅ Complete | Baseline check | $0 |
| 2026-04-08 | Emergency Repair | Splice Repair | TC-Bravo | ✅ Complete | 2 strands failed | $1,200 |
| 2026-04-15 | Follow-up Inspection | Physical + Audio | TC-Alpha | ✅ Complete | Post-repair verify | $0 |
| 2026-04-22 | Conduit Assessment | Structural | TC-Charlie | 🔄 In Progress | Crack documented | $400 |
| 2026-04-28 | Engineering Review | Splice + Routing | TC-Alpha | ✅ Complete | Full strand test | $0 |
| 2026-05-02 | Visual Inspection | Photo Documentation | TC-Delta | ✅ Complete | 6 photos captured | $0 |
| 2026-05-03 | Equipment Order | Procurement | Admin | ✅ Approved | Materials sourced | $6,829 |

**REVIEW CHECKLIST**
☑ Site safety assessment complete
☑ Prior incident history reviewed
☑ Budget approval obtained (≤$10,000 threshold)
☐ Crew dispatch authorized
☑ Equipment availability confirmed

**QR Code:** ML-2026-Q2-009-VERIFIED
**Signatures:** J. Martinez (Site Lead), K. Okonkwo (Safety Officer)
**Addendum:** "Segment 9 shared conduit — recommend full replacement by Q3"

---
**CU extracted:** **2 table(s)** • **12 paragraphs** • **1 barcode/QR** • **5☑ 1☐ selection marks**
"""


def _empty_output():
    """The initial empty state for the output panel."""
    return [
        html.Div("Output", className="demo-panel-header"),
        dmc.Center(
            dmc.Stack([
                dmc.Text("Press  ▶ Run Live  or  📦 Cached  to execute", c="dimmed", size="sm"),
            ], align="center", gap="sm"),
            style={"height": "100%", "flex": "1"},
        ),
    ]


def _output_tabs(cu_text, pymupdf_text):
    """Build the output tabs with results."""
    return [
        html.Div("Output", className="demo-panel-header"),
        dmc.Tabs(
            value="cu",
            children=[
                dmc.TabsList([
                    dmc.TabsTab("CU Output", value="cu"),
                    dmc.TabsTab("PyMuPDF Output", value="pymupdf"),
                ]),
                dmc.TabsPanel(
                    html.Pre(cu_text, style={"fontFamily": "var(--mono)", "fontSize": "0.72rem",
                                             "lineHeight": "1.5", "whiteSpace": "pre-wrap"}),
                    value="cu", pt="md",
                ),
                dmc.TabsPanel(
                    html.Pre(pymupdf_text, style={"fontFamily": "var(--mono)", "fontSize": "0.72rem",
                                                   "lineHeight": "1.5", "whiteSpace": "pre-wrap"}),
                    value="pymupdf", pt="md",
                ),
            ],
        ),
    ]


def act1_layout():
    """Build the Act 1 live demo page layout."""
    live_available = is_configured()

    return html.Div([
        # Page title bar
        html.Div(
            style={"display": "flex", "justifyContent": "space-between", "alignItems": "center",
                   "padding": "16px 24px 0 24px"},
            children=[
                dmc.Group([
                    dmc.Badge("Act 1", color="blue", variant="filled", size="lg"),
                    dmc.Title("What Happened Here? — Local vs Cloud Extraction", order=4, c="white"),
                ]),
                dmc.Group([
                    dmc.Badge("READY", color="gray", variant="light", size="sm", id="act1-mode-badge"),
                    dmc.Button(
                        "▶ Run Live",
                        id="act1-run-btn",
                        variant="light",
                        size="xs",
                        color="green",
                        disabled=not live_available,
                    ),
                    dmc.Button(
                        "📦 Post-processed",
                        id="act1-cached-btn",
                        variant="light",
                        size="xs",
                        color="blue",
                    ),
                ]),
            ],
        ),

        # Main 3-panel layout
        html.Div(
            className="demo-page",
            style={"height": "calc(100vh - 60px)", "paddingTop": "12px"},
            children=[
                # Left: Document view
                create_doc_viewer(
                    image_src="/static/docs/maintenance_log.png",
                    title="📄 Site Maintenance Log — Q2 2026",
                    description="cl_v3_maintenance_log_2026_Q2.pdf",
                ),

                # Center: Code comparison
                html.Div(className="demo-panel", children=[
                    html.Div("Code", className="demo-panel-header"),
                    dmc.Tabs(
                        value="cu",
                        children=[
                            dmc.TabsList([
                                dmc.TabsTab("Content Understanding", value="cu"),
                                dmc.TabsTab("PyMuPDF (local)", value="pymupdf"),
                            ]),
                            dmc.TabsPanel(
                                dmc.CodeHighlight(code=EXTRACTION_CODE, language="python", withCopyButton=False,
                                                  style={"fontSize": "0.78rem"}),
                                value="cu", pt="md",
                            ),
                            dmc.TabsPanel(
                                dmc.CodeHighlight(code=PYMUPDF_CODE, language="python", withCopyButton=False,
                                                  style={"fontSize": "0.78rem"}),
                                value="pymupdf", pt="md",
                            ),
                        ],
                    ),
                ]),

                # Right: Output (starts empty)
                html.Div(className="demo-panel", id="act1-output-panel", children=_empty_output()),
            ],
        ),

        # Navigation hint
        html.Div("← → to navigate", className="nav-hint"),
    ])


@callback(
    Output("act1-output-panel", "children"),
    Output("act1-mode-badge", "children"),
    Output("act1-mode-badge", "color"),
    Input("act1-run-btn", "n_clicks"),
    Input("act1-cached-btn", "n_clicks"),
    prevent_initial_call=True,
)
def run_act1(run_clicks, cached_clicks):
    """Execute live or load cached results based on which button was pressed."""
    triggered = ctx.triggered_id

    if triggered == "act1-cached-btn":
        # Always show the static pre-cached outputs from the notebook
        return _output_tabs(CU_OUTPUT, PYMUPDF_OUTPUT), "POST-PROCESSED", "blue"

    if triggered == "act1-run-btn":
        # Run live — follow all notebook prerequisites
        import os
        import pymupdf
        from dotenv import load_dotenv
        from azure.ai.contentunderstanding import ContentUnderstandingClient
        from azure.core.credentials import AzureKeyCredential

        load_dotenv(override=True)
        endpoint = os.environ.get("CONTENTUNDERSTANDING_ENDPOINT", "")
        key = os.getenv("CONTENTUNDERSTANDING_KEY")

        if not endpoint:
            return (
                _output_tabs("⚠️ CONTENTUNDERSTANDING_ENDPOINT not set in .env", PYMUPDF_OUTPUT),
                "ERROR", "red",
            )

        # --- PyMuPDF extraction (local) ---
        pymupdf_result = PYMUPDF_OUTPUT
        if SAMPLE_PDF.exists():
            doc = pymupdf.open(str(SAMPLE_PDF))
            raw_text = ""
            for page in doc:
                raw_text += page.get_text()
            pymupdf_result = (
                f"Pages: {len(doc)}\n{'═' * 60}\n"
                f"RAW TEXT OUTPUT:\n{'═' * 60}\n\n"
                f"{raw_text}"
            )
            doc.close()

        # --- CU extraction (live API call) ---
        try:
            credential = AzureKeyCredential(key) if key else __import__(
                "azure.identity", fromlist=["DefaultAzureCredential"]
            ).DefaultAzureCredential()
            client = ContentUnderstandingClient(
                endpoint=endpoint,
                credential=credential,
                user_agent="build26-DEM331-demo/1.0.0",
            )

            with open(SAMPLE_PDF, "rb") as f:
                poller = client.begin_analyze_binary(
                    analyzer_id="prebuilt-layout",
                    binary_input=f.read(),
                )
            result = poller.result()

            if result and result.contents:
                cu_markdown = result.contents[0].markdown
            else:
                cu_markdown = "⚠️ CU returned empty result"
        except Exception as e:
            cu_markdown = f"⚠️ CU Error: {type(e).__name__}: {e}"

        return _output_tabs(cu_markdown, pymupdf_result), "LIVE", "green"

    return no_update, no_update, no_update
