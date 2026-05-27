"""Act 1 — Local PyMuPDF vs Azure Content Understanding extraction.

Mirrors notebook cells 9 (PyMuPDF) and 11–12 (CU extraction + table preview).
Output starts empty — user clicks Run Live or Pre-processed.
"""

from pathlib import Path

from dash import Input, Output, callback, ctx, html, no_update
import dash_mantine_components as dmc

from components.doc_viewer import create_doc_viewer
from services.cu_client import (
    agent_reason,
    analyze_document,
    extraction_summary,
    get_agent_client,
    is_configured,
)

DOC_NAME = "cl_v3_maintenance_log_2026_Q2.pdf"
SAMPLE_PDF = Path(__file__).parent.parent.parent / "src" / "sample-data" / "documents" / DOC_NAME


# ---------------------------------------------------------------------------
# Displayed code (literally from notebook cells 9 + 11 + 13, lightly trimmed)
# ---------------------------------------------------------------------------

PYMUPDF_CODE = '''# Local PDF library output — flat text, no structure
import pymupdf
from pathlib import Path

maintenance_log = Path("sample-data/documents/cl_v3_maintenance_log_2026_Q2.pdf")

doc = pymupdf.open(str(maintenance_log))
print(f"Pages: {len(doc)}")
print(f"{'═' * 70}")
print("RAW TEXT OUTPUT (first 2500 chars):")
print(f"{'═' * 70}\\n")

raw_text = ""
for page_num in range(len(doc)):
    page = doc[page_num]
    raw_text += page.get_text()
doc.close()

print(raw_text[:2500])
print(f"\\n{'─' * 70}")
print(f"Total raw text: {len(raw_text):,} chars")
'''

CU_CODE = '''# Same PDF, single Content Understanding call
from azure.ai.contentunderstanding import ContentUnderstandingClient, to_llm_input
from azure.core.credentials import AzureKeyCredential

client = ContentUnderstandingClient(
    endpoint=ENDPOINT,
    credential=AzureKeyCredential(KEY),
    user_agent="build26-DEM331/1.0.0",
)

def analyze_document(pdf_path):
    with open(pdf_path, "rb") as f:
        poller = client.begin_analyze_binary(
            analyzer_id="prebuilt-documentSearch",
            binary_input=f.read(),
        )
    return poller.result()

maintenance_result = analyze_document(maintenance_log)
content = maintenance_result.contents[0]

# Programmatic access — tables, figures, barcodes, selection marks
print(f"{len(content.tables)} tables, {len(content.figures)} figures")
print(f"{sum(len(p.barcodes) for p in content.pages if p.barcodes)} barcodes/QR")
print(f"{content.markdown.count('☒')} checked + "
      f"{content.markdown.count('☐')} unchecked selection marks\\n")

# Agent reasoning over the structured extraction
reasoning = agent_reason(
    to_llm_input(maintenance_result),
    "Site Maintenance Log — Q2 2026 (tables, selection marks, cost data)",
    "Is this a new problem or a recurring one? Are we cleared to proceed?"
)
print(reasoning)
'''


# ---------------------------------------------------------------------------
# Cached outputs — captured directly from the notebook .ipynb
# ---------------------------------------------------------------------------

PYMUPDF_CACHED = """Pages: 1
══════════════════════════════════════════════════════════════════════
RAW TEXT OUTPUT (first 2500 chars):
══════════════════════════════════════════════════════════════════════

SITE MAINTENANCE LOG -- TOWER RIDGE CORRIDOR
Site B -- Segment 9 (Pole TR-38 to JB-9B) | Log Period: 2026-Q2
LOG-TR-2026-Q2
MAINTENANCE ACTIVITY LOG
Date
Time
Tech
Activity
Duration
Sign-Off
04/10
08:00
Alvarez
Full corridor walk + photo
6.5h
[signed]
04/10
08:00
Alvarez
Video documentation (incl.)
(incl.)
[signed]
04/15
14:30
Sharma
Follow-up walk + strand check
3.0h
[signed]
04/15
15:00
Sharma
Barrier reinstallation
0.5h
[signed]
04/20
09:00
Team C
Survey walk (Steps 1,3)
4.0h
[signed]
04/22
07:00
Team A
OTDR testing all routes
5.5h
[signed]
04/22
13:00
Team A
Emergency splice Str 7,11
3.5h
[signed]
04/28
08:30
Nakamura
Engineering assessment
4.0h
[signed]
04/28
08:30
Sharma
Splice verification
3.0h
[signed]
05/02
07:30
Alvarez
Post-storm inspection
5.0h
[signed]
05/02
14:00
Team A
Emergency barrier repair
2.0h
[signed]
05/05
09:00
GeoCorp
Vault measurement update
3.0h
[ext. sign]
LABOR SUMMARY -- REACTIVE MAINTENANCE
Crew/Person
Hours Q2
Rate
Cost
Budget Code
Alvarez (Inspector)
14.5
$85/h
$1,233
INSP-TR-Q2
Sharma (Field Tech)
11.0
$95/h
$1,045
TECH-TR-Q2
Team A (Fiber Crew)
11.0
$180/h
$1,980
CREW-TR-Q2
Team C (General)
4.0
$120/h
$480
CREW-TR-Q2
Nakamura (Engineer)
4.0
$150/h
$600
ENG-TR-Q2
GeoCorp (External)
3.0
$220/h
$660
EXT-TR-Q2
TOTAL: 47.5h
$5,998
RELATED INCIDENTS & DOCUMENTS
INC-2025-1187 | Micro-bend Jan 2026      | Repair Report 2026-01-15 | CLOSED
INC-2026-0089 | Fiber break Mar 2026     | Repair Report 2026-03-01 | CLOSED
WO-2026-0287  | Conduit replace Phase 1  | Completed 2026-03-25     | CLOSED
WO-2026-0391  | Emergency re-assessment  | In Progress              | OPEN
CR-2026-04-10 | Full corridor condition  | Condition Report         | ACTIVE
FSE-2026-0041 | Splice engineering sheet | As-Built 2026-04-28      | CURRENT
ADDENDUM -- Webb 05/06:
REVIEW CHECKLIST:
Field data verified
Budget codes confirmed
Escalation required
J. Alvarez
Lead Inspector
Date: 2026-05-06
P. Sharma
Senior Field Tech
Date: 2026-05-06
M. Webb
Operations Manager
Date: 2026-05-06
SCAN TO VERIFY
Total reactive spend this corridor since Jan: $74,200 (42 customers at risk)
Corridor rehab approved by VP Daniels ($120K, BUD-2026-TR-009).
Replacement 05/19. Team A + GeoCorp. See FRD-2026-04-28.
--- DOCUMENT CROSS-REFERENCE INDEX ---
PL-2026-04-10-TR9      Photo Log (Alvarez, 04/10)
VID-IDX-2026-04-10-TR9 Video Inspection (Alvarez, 04/10)
AUD-2026-04-15-TR9     Audio Transcript (Sharma/Alvarez, 04/15)
DOC-PHOTO-2026-05-02   Inspection Photos (Alvarez, 05/02)
FSE-2026-00

──────────────────────────────────────────────────────────────────────
Total raw text: 2,930 chars
"""

CU_CACHED = """**CU extracted:** **2 table(s)** • **158 paragraphs** • **1 barcode/QR** • **2☒ 1☐ selection marks**

LOCAL PyMuPDF                       │ CONTENT UNDERSTANDING
────────────────────────────────────┼────────────────────────────────────
Flat text stream                    │ Markdown with | table | syntax
No column alignment                 │ Columns preserved in pipe format
Selection marks lost or garbled     │ ☑ and ☐ rendered correctly
No heading hierarchy                │ # H1, ## H2 structure intact
Cross-page tables split             │ Tables merged across pages
Images = nothing                    │ Figures with AI-generated captions
QR codes = invisible                │ Decoded barcode/QR values

CU structural elements extracted from this single PDF:
   2 tables (with row/column structure)
   0 figures (with AI captions)
   1 barcodes/QR codes (decoded)
   2 checked + 1 unchecked selection marks


TABLES EXTRACTED (agent gets row/col access, not text blobs):

  Table 1: 13 rows × 6 cols
  ───────────────────────────────────────────────────────
    [0,0] Date
    [0,1] Time
    [0,2] Tech
    [0,3] Activity
    [0,4] Duration
    [0,5] Sign-Off
    [1,0] 04/10
    [1,1] 08:00
    [1,2] Alvarez
    [1,3] Full corridor walk + photo
    [1,4] 6.5h
    [1,5] [signed]
    [2,0] 04/10
    [2,1] 08:00
    [2,2] Alvarez
    [2,3] Video documentation (incl.)
    [2,4] (incl.)
    [2,5] [signed]
    ... (10 more rows)

  Table 2: 8 rows × 5 cols
  ───────────────────────────────────────────────────────
    [0,0] Crew/Person
    [0,1] Hours Q2
    [0,2] Rate
    [0,3] Cost
    [0,4] Budget Code
    [1,0] Alvarez (Inspector)
    [1,1] 14.5
    [1,2] $85/h
    [1,3] $1,233
    [1,4] INSP-TR-Q2
    [2,0] Sharma (Field Tech)
    [2,1] 11.0
    [2,2] $95/h
    [2,3] $1,045
    [2,4] TECH-TR-Q2
    ... (5 more rows)

────────────────────────────────────────────────────────────
REVIEW CHECKLIST:

☒
Field data verified

☒
Budget codes confirmed

☐
Escalation required

────────────────────────────────────────────────────────────
AGENT REASONING:
- The maintenance log lists multiple prior incidents in Segment 9: INC-2025-1187 (micro-bend, Jan 2026), INC-2026-0089 (fiber break, Mar 2026), and WO-2026-0287 (conduit replacement, Mar 2026), all at Vault TV-3, indicating recurring problems in this area.
- The addendum confirms total reactive spend since January is $74,200 for this corridor, showing ongoing costs and repeated interventions.
- Corridor rehabilitation has been formally approved by VP Daniels ($120K, BUD-2026-TR-009), and replacement work is scheduled for 05/19 with Team A and GeoCorp, confirming procurement clearance.
- The review checklist shows field data and budget codes are verified, with no escalation required, supporting readiness for procurement.
- Document cross-references and open work orders (WO-2026-0391) further indicate ongoing, unresolved issues.

Conclusion: This is a recurring problem in Segment 9, and procurement is fully cleared and approved for corridor rehabilitation and replacement.
"""


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

PRE_STYLE = {
    "fontFamily": "var(--mono)",
    "fontSize": "0.72rem",
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


def _output_tabs(cu_text, pymupdf_text):
    return [
        html.Div("Output", className="demo-panel-header"),
        dmc.Tabs(
            value="cu",
            children=[
                dmc.TabsList([
                    dmc.TabsTab("CU Output", value="cu"),
                    dmc.TabsTab("PyMuPDF Output", value="pymupdf"),
                ]),
                dmc.TabsPanel(html.Pre(cu_text, style=PRE_STYLE), value="cu", pt="md"),
                dmc.TabsPanel(html.Pre(pymupdf_text, style=PRE_STYLE), value="pymupdf", pt="md"),
            ],
        ),
    ]


def act1_layout():
    live_available = is_configured()

    return html.Div([
        html.Div(
            style={
                "display": "flex", "justifyContent": "space-between", "alignItems": "center",
                "padding": "16px 24px 0 24px",
            },
            children=[
                dmc.Group([
                    dmc.Badge("Act 1", color="blue", variant="filled", size="lg"),
                    dmc.Title("What Happened Here? — Local vs Cloud Extraction", order=4, c="white"),
                ]),
                dmc.Group([
                    dmc.Badge("READY", color="gray", variant="light", size="sm", id="act1-mode-badge"),
                    dmc.Button("\u25B6 Run Live", id="act1-run-btn", variant="light", size="xs",
                               color="green", disabled=not live_available),
                    dmc.Button("\U0001F4E6 Pre-processed", id="act1-cached-btn", variant="light",
                               size="xs", color="blue"),
                ]),
            ],
        ),

        html.Div(
            className="demo-page",
            style={"height": "calc(100vh - 60px)", "paddingTop": "12px"},
            children=[
                # Left: Document image
                create_doc_viewer(
                    image_src="/static/docs/maintenance_log.png",
                    title="\U0001F4C4 Site Maintenance Log — Q2 2026",
                    description=DOC_NAME,
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
                                dmc.CodeHighlight(code=CU_CODE, language="python",
                                                  withCopyButton=False,
                                                  style={"fontSize": "0.74rem"}),
                                value="cu", pt="md",
                            ),
                            dmc.TabsPanel(
                                dmc.CodeHighlight(code=PYMUPDF_CODE, language="python",
                                                  withCopyButton=False,
                                                  style={"fontSize": "0.74rem"}),
                                value="pymupdf", pt="md",
                            ),
                        ],
                    ),
                ]),

                # Right: Output (starts empty)
                html.Div(className="demo-panel", id="act1-output-panel", children=_empty_output()),
            ],
        ),

        html.Div("\u2190 \u2192 to navigate", className="nav-hint"),
    ])


# ---------------------------------------------------------------------------
# Live runner — mirrors notebook cells 9 + 11 + 12 + 13
# ---------------------------------------------------------------------------


def _run_pymupdf():
    """Reproduce notebook cell 9 output exactly (raw text + limitations footer)."""
    import pymupdf

    doc = pymupdf.open(str(SAMPLE_PDF))
    raw_text = ""
    for page in doc:
        raw_text += page.get_text()
    page_count = len(doc)
    doc.close()

    bar = "═" * 70
    rule = "─" * 70
    lines = [
        f"Pages: {page_count}",
        bar,
        "RAW TEXT OUTPUT (first 2500 chars):",
        bar + "\n",
        raw_text[:2500],
        f"\n{rule}",
        f"Total raw text: {len(raw_text):,} chars",
    ]
    return "\n".join(lines)


def _run_cu_live():
    """Reproduce notebook cells 11 + 12 + 13: comparison table, structural counts,
    table preview, REVIEW CHECKLIST excerpt, agent reasoning."""
    from azure.ai.contentunderstanding import to_llm_input

    result = analyze_document(SAMPLE_PDF, analyzer_id="prebuilt-documentSearch")
    if not result or not result.contents:
        return "⚠️ CU returned empty result"
    content = result.contents[0]
    cu_md = content.markdown or ""

    lines: list[str] = []
    lines.append(extraction_summary(result))
    lines.append("")
    lines.append(f"{'LOCAL PyMuPDF':<35} │ {'CONTENT UNDERSTANDING'}")
    lines.append(f"{'─' * 35}─┼─{'─' * 35}")
    lines.append(f"{'Flat text stream':<35} │ {'Markdown with | table | syntax'}")
    lines.append(f"{'No column alignment':<35} │ {'Columns preserved in pipe format'}")
    lines.append(f"{'Selection marks lost or garbled':<35} │ {'☑ and ☐ rendered correctly'}")
    lines.append(f"{'No heading hierarchy':<35} │ {'# H1, ## H2 structure intact'}")
    lines.append(f"{'Cross-page tables split':<35} │ {'Tables merged across pages'}")
    lines.append(f"{'Images = nothing':<35} │ {'Figures with AI-generated captions'}")
    lines.append(f"{'QR codes = invisible':<35} │ {'Decoded barcode/QR values'}")
    lines.append("")

    table_count = len(content.tables) if content.tables else 0
    figure_count = len(content.figures) if content.figures else 0
    barcode_count = (
        sum(len(p.barcodes) for p in content.pages if p.barcodes)
        if content.pages else 0
    )
    checked = cu_md.count("☒")
    unchecked = cu_md.count("☐")
    lines.append("CU structural elements extracted from this single PDF:")
    lines.append(f"   {table_count} tables (with row/column structure)")
    lines.append(f"   {figure_count} figures (with AI captions)")
    lines.append(f"   {barcode_count} barcodes/QR codes (decoded)")
    lines.append(f"   {checked} checked + {unchecked} unchecked selection marks")
    lines.append("")
    lines.append("")
    lines.append("TABLES EXTRACTED (agent gets row/col access, not text blobs):")

    if content.tables:
        for i, table in enumerate(content.tables):
            lines.append("")
            lines.append(f"  Table {i+1}: {table.row_count} rows × {table.column_count} cols")
            lines.append(f"  {'─' * 55}")
            for cell in table.cells:
                if cell.row_index <= 2:
                    lines.append(f"    [{cell.row_index},{cell.column_index}] {cell.content[:50]}")
            if table.row_count > 3:
                lines.append(f"    ... ({table.row_count - 3} more rows)")

    # REVIEW CHECKLIST excerpt (notebook cell 13)
    lines.append("")
    lines.append("─" * 60)
    if "REVIEW CHECKLIST" in cu_md:
        start = cu_md.find("REVIEW CHECKLIST")
        end = cu_md.find("\n\n", start + 80)
        excerpt = cu_md[start:end if end > 0 else start + 300]
        lines.append(excerpt)
        lines.append("")

    # Agent reasoning (notebook cell 13)
    lines.append("─" * 60)
    if get_agent_client():
        try:
            reasoning = agent_reason(
                to_llm_input(result),
                "Site Maintenance Log — Q2 2026 (tables, selection marks, cost data)",
                "Is this a new problem or a recurring one? Are we cleared to proceed with procurement?",
            )
        except Exception as e:  # pragma: no cover
            reasoning = f"(agent reasoning failed: {e})"
    else:
        reasoning = "(agent client not configured — skipped reasoning)"
    lines.append("AGENT REASONING:")
    lines.append(reasoning)

    return "\n".join(lines)


@callback(
    Output("act1-output-panel", "children"),
    Output("act1-mode-badge", "children"),
    Output("act1-mode-badge", "color"),
    Input("act1-run-btn", "n_clicks"),
    Input("act1-cached-btn", "n_clicks"),
    prevent_initial_call=True,
)
def run_act1(run_clicks, cached_clicks):
    triggered = ctx.triggered_id

    if triggered == "act1-cached-btn":
        return _output_tabs(CU_CACHED, PYMUPDF_CACHED), "PRE-PROCESSED", "blue"

    if triggered == "act1-run-btn":
        try:
            pymupdf_text = _run_pymupdf()
        except Exception as e:
            pymupdf_text = f"⚠️ PyMuPDF error: {type(e).__name__}: {e}"

        try:
            cu_text = _run_cu_live()
        except Exception as e:
            cu_text = f"⚠️ CU error: {type(e).__name__}: {e}"

        return _output_tabs(cu_text, pymupdf_text), "LIVE", "green"

    return no_update, no_update, no_update
