"""Act 3 — Custom Analyzers & Classification.

Shows custom analyzer definitions, classifier routing, and structured
field extraction from 6 specialized engineering documents.
Output starts empty — user clicks Run Live or Post-processed.
"""

from pathlib import Path

from dash import html, callback, Input, Output, ctx, no_update
import dash_mantine_components as dmc

from services.cu_client import is_configured

DOCS_DIR = Path(__file__).parent.parent.parent / "src" / "sample-data" / "documents"

# Code precisely from notebook cells 21-22
ANALYZER_CODE = '''# Define ALL custom analyzers for the remaining 6 documents
CUSTOM_ANALYZERS = {
    "photoLogTriageAnalyzer": {
        "description": "Triage field photo logs — extract priority findings "
                       "and recommend dispatch urgency for the repair agent.",
        "baseAnalyzerId": "prebuilt-document",
        "scenario": "document",
        "models": {"completion": "gpt-4.1"},
        "fieldSchema": {"fields": {
            "HighPriorityCount": {"type": "integer", "method": "generate",
                "description": "Count of photos/entries marked HIGH priority."},
            "CriticalFindings": {"type": "string", "method": "generate",
                "description": "Summarize all HIGH-priority findings in one paragraph."},
            "DispatchUrgency": {"type": "string", "method": "generate",
                "description": "IMMEDIATE / URGENT / SCHEDULED. Explain reasoning."},
        }}
    },
    "videoInspectionAnalyzer": {
        "fields": ["CriticalSegments", "EscalationRequired", "DamageProgression"]
    },
    "fiberSpliceExtractor": {
        "fields": ["CableType", "StrandCount", "FailedStrands",
                   "FailureMode", "MaxLoss", "EngineeringRecommendation"]
    },
    "fiberRoutingAnalyzer": {
        "fields": ["RedundancyGap", "AffectedCustomers",
                   "SinglePointOfFailure", "RerouteOption"]
    },
    "equipmentProcurementAnalyzer": {
        "fields": ["TotalCost", "BackorderRisk",
                   "CriticalPathDays", "BudgetVerdict"]
    },
    "plantDiagramAnalyzer": {
        "fields": ["FiberEntryPoint", "ThermalRisk",
                   "AffectedZone", "FieldNotes"]
    },
}

# Deploy all custom analyzers
from azure.ai.contentunderstanding.models import (
    ContentAnalyzer, ContentFieldSchema,
    ContentFieldDefinition, ContentFieldType, GenerationMethod,
)

for name, schema in CUSTOM_ANALYZERS.items():
    fields = {
        fname: ContentFieldDefinition(
            type=ContentFieldType.STRING,
            method=GenerationMethod.GENERATE,
            description=fdef["description"],
        )
        for fname, fdef in schema["fieldSchema"]["fields"].items()
    }
    poller = client.begin_create_analyzer(
        analyzer_id=name,
        resource=ContentAnalyzer(
            base_analyzer_id="prebuilt-document",
            description=schema["description"],
            field_schema=ContentFieldSchema(fields=fields),
            models=schema["models"],
        ),
        allow_replace=True,
    )
    result = poller.result()
    print(f"  {name}: ✅ ready")
'''

# Classifier code from notebook cell 24-25
CLASSIFIER_CODE = '''# Create a classifier that routes documents to custom analyzers
CLASSIFIER_ID = "fiberFieldDocClassifier"

categories = {
    "Photo_Log": ContentCategoryDefinition(
        description="GPS-indexed photo logs with priority ratings",
        analyzer_id="photoLogTriageAnalyzer"),
    "Video_Inspection": ContentCategoryDefinition(
        description="Video inspection index with timestamps and damage",
        analyzer_id="videoInspectionAnalyzer"),
    "Splice_Sheet": ContentCategoryDefinition(
        description="Fiber splice sheets with OTDR loss measurements",
        analyzer_id="fiberSpliceExtractor"),
    "Fiber_Routing": ContentCategoryDefinition(
        description="Network fiber routing diagrams",
        analyzer_id="fiberRoutingAnalyzer"),
    "Equipment_Spec": ContentCategoryDefinition(
        description="Equipment specs and materials orders",
        analyzer_id="equipmentProcurementAnalyzer"),
    "Plant_Diagram": ContentCategoryDefinition(
        description="Facility plant diagrams with fiber paths",
        analyzer_id="plantDiagramAnalyzer"),
}

poller = client.begin_create_analyzer(
    analyzer_id=CLASSIFIER_ID,
    resource=classifier,
    allow_replace=True,
)
result = poller.result()
print(f"✅ Classifier '{CLASSIFIER_ID}' deployed!")

# Classify and route — single call handles both
with open(test_doc, "rb") as f:
    classify_result = client.begin_analyze_binary(
        analyzer_id=CLASSIFIER_ID, binary_input=f.read()
    ).result()

# Result has category + extracted fields
doc_content = classify_result.contents[0]
print(f"Category: {doc_content.segments[0].category}")
for fname, fval in doc_content.fields.items():
    print(f"  {fname}: {fval.value}")
'''

# Post-processed outputs from notebook
EXTRACTION_RESULTS = """━━━ photoLogTriageAnalyzer ━━━━━━━━━━━━━━━━━━━━
  HighPriorityCount: 3
  CriticalFindings: Vault crack propagation, water intrusion at conduit entry,
    strand displacement at bracket contact points (strands 4 & 7)
  DispatchUrgency: IMMEDIATE (>3 HIGH items or safety risk)

━━━ videoInspectionAnalyzer ━━━━━━━━━━━━━━━━━━━━
  CriticalSegments: VID-05 (52:30-78:00): Vault TV-3 -- CRITICAL (recurring);
    VID-06 (78:00-95:00): Section 5 -- heave
  EscalationRequired: YES. Recurring and worsening crack in Vault TV-3
  DamageProgression: Worsening — Vault TV-3 crack increased from <1cm in
    January to 2cm in April

━━━ fiberSpliceExtractor ━━━━━━━━━━━━━━━━━━━━━━
  CableType: G.652D Single-Mode, 12-strand SM OS2
  StrandCount: 12
  FailedStrands: SM-5 (Slate, 0.52 dB/km, MARGINAL); SM-11 (Rose, 0.55 dB/km, FAIL)
  FailureMode: micro-bend from conduit pressure
  MaxLoss: 0.55
  EngineeringRecommendation: Full segment replacement — re-splice insufficient

━━━ fiberRoutingAnalyzer ━━━━━━━━━━━━━━━━━━━━━━━
  RedundancyGap: Route 2 shares conduit with Route 1 in Sections 3-5
  AffectedCustomers: 42
  SinglePointOfFailure: Shared conduit at Vault TV-3, segment 9
  RerouteOption: No alternative — full conduit replacement required

━━━ equipmentProcurementAnalyzer ━━━━━━━━━━━━━━━
  TotalCost: $6,829
  BackorderRisk: Vault Anchors (VA-HEL-6FT): backorder (ETA pushed to 05/15)
  CriticalPathDays: 10
  BudgetVerdict: WITHIN BUDGET ($6,829 of $120,000)

━━━ plantDiagramAnalyzer ━━━━━━━━━━━━━━━━━━━━━━━
  FiberEntryPoint: North penetration, Bay 7 ODF
  ThermalRisk: No thermal issues noted
  AffectedZone: Zone C — rows 3-5, racks C3-1 through C5-4
  FieldNotes: "Segment 9 shared conduit — recommend full replacement by Q3"
    — annotated by K. Okonkwo, 2026-04-28
"""

CLASSIFICATION_TABLE = """### Classifier Results: 6/6 Correct

Document                                           Classified As        Correct?
────────────────────────────────────────────────── ──────────────────── ────────
cl_v3_site_b_photo_log_2026_04_10.pdf              Photo_Log            ✅
cl_v3_site_b_video_inspection_2026_04_10.pdf       Video_Inspection     ✅
cl_v3_engineering_splice_sheet_2026_04_28.pdf      Splice_Sheet         ✅
cl_v3_datacenter_fiber_routing_2026_04_28.pdf      Fiber_Routing        ✅
cl_v3_equipment_spec_sheet_2026_05_03.pdf          Equipment_Spec       ✅
cl_v3_datacenter_plant_diagram_2026_04_28.pdf      Plant_Diagram        ✅

✅ Classifier correctly identifies all document types.
   In production, a single endpoint call handles classification and extraction.
"""


def _empty_output():
    return [
        html.Div("Output", className="demo-panel-header"),
        dmc.Center(
            dmc.Text("Press  ▶ Run Live  or  📦 Post-processed  to execute", c="dimmed", size="sm"),
            style={"height": "100%", "flex": "1"},
        ),
    ]


def _output_tabs(extraction_text, classification_text):
    return [
        html.Div("Output", className="demo-panel-header"),
        dmc.Tabs(
            value="extractions",
            children=[
                dmc.TabsList([
                    dmc.TabsTab("Field Extractions", value="extractions"),
                    dmc.TabsTab("Classification", value="classification"),
                ]),
                dmc.TabsPanel(
                    html.Pre(extraction_text, style={"fontFamily": "var(--mono)", "fontSize": "0.7rem",
                                                     "lineHeight": "1.5", "whiteSpace": "pre-wrap"}),
                    value="extractions", pt="md",
                ),
                dmc.TabsPanel(
                    html.Pre(classification_text, style={"fontFamily": "var(--mono)", "fontSize": "0.7rem",
                                                         "lineHeight": "1.5", "whiteSpace": "pre-wrap"}),
                    value="classification", pt="md",
                ),
            ],
        ),
    ]


def _doc_card(title, desc, color):
    return dmc.Paper(
        p="xs", radius="sm", withBorder=True,
        children=dmc.Group([
            dmc.Badge(title[:2].upper(), color=color, variant="light", size="sm"),
            dmc.Stack([
                dmc.Text(title, size="xs", fw=600),
                dmc.Text(desc, size="xs", c="dimmed"),
            ], gap=2),
        ], gap="sm"),
    )


def act3_layout():
    """Build the Act 3 live demo page layout."""
    live_available = is_configured()

    return html.Div([
        html.Div(
            style={"display": "flex", "justifyContent": "space-between", "alignItems": "center",
                   "padding": "16px 24px 0 24px"},
            children=[
                dmc.Group([
                    dmc.Badge("Act 3", color="teal", variant="filled", size="lg"),
                    dmc.Title("Deep Extraction — Custom Analyzers & Classification", order=4, c="white"),
                ]),
                dmc.Group([
                    dmc.Badge("READY", color="gray", variant="light", size="sm", id="act3-mode-badge"),
                    dmc.Button("▶ Run Live", id="act3-run-btn", variant="light", size="xs",
                               color="green", disabled=not live_available),
                    dmc.Button("📦 Post-processed", id="act3-cached-btn", variant="light", size="xs", color="blue"),
                ]),
            ],
        ),

        html.Div(
            className="demo-page",
            style={"height": "calc(100vh - 60px)", "paddingTop": "12px"},
            children=[
                # Left: Code
                html.Div(className="demo-panel", children=[
                    html.Div("Code", className="demo-panel-header"),
                    dmc.Tabs(
                        value="analyzers",
                        children=[
                            dmc.TabsList([
                                dmc.TabsTab("Custom Analyzers", value="analyzers"),
                                dmc.TabsTab("Classifier", value="classifier"),
                            ]),
                            dmc.TabsPanel(
                                dmc.CodeHighlight(code=ANALYZER_CODE, language="python", withCopyButton=False,
                                                  style={"fontSize": "0.72rem"}),
                                value="analyzers", pt="md",
                            ),
                            dmc.TabsPanel(
                                dmc.CodeHighlight(code=CLASSIFIER_CODE, language="python", withCopyButton=False,
                                                  style={"fontSize": "0.72rem"}),
                                value="classifier", pt="md",
                            ),
                        ],
                    ),
                ]),

                # Center: 6 Documents
                html.Div(className="demo-panel", children=[
                    html.Div("📁 6 Field Documents", className="demo-panel-header"),
                    dmc.Stack([
                        _doc_card("Photo Log", "GPS-indexed field photos with priority ratings", "teal"),
                        _doc_card("Video Inspection", "6 segments with damage classification", "blue"),
                        _doc_card("Splice Sheet", "Strand-level loss measurements", "violet"),
                        _doc_card("Fiber Routing", "Primary & backup path topology", "orange"),
                        _doc_card("Equipment Spec", "Procurement data & budget", "green"),
                        _doc_card("Plant Diagram", "Facility layout with fiber paths", "pink"),
                    ], gap="xs"),
                ]),

                # Right: Output (starts empty)
                html.Div(className="demo-panel", id="act3-output-panel", children=_empty_output()),
            ],
        ),

        html.Div("← → to navigate", className="nav-hint"),
    ])


@callback(
    Output("act3-output-panel", "children"),
    Output("act3-mode-badge", "children"),
    Output("act3-mode-badge", "color"),
    Input("act3-run-btn", "n_clicks"),
    Input("act3-cached-btn", "n_clicks"),
    prevent_initial_call=True,
)
def run_act3(run_clicks, cached_clicks):
    """Execute live or show post-processed results."""
    triggered = ctx.triggered_id

    if triggered == "act3-cached-btn":
        return _output_tabs(EXTRACTION_RESULTS, CLASSIFICATION_TABLE), "POST-PROCESSED", "blue"

    if triggered == "act3-run-btn":
        import os
        from typing import cast
        from dotenv import load_dotenv
        from azure.ai.contentunderstanding import ContentUnderstandingClient, to_llm_input
        from azure.ai.contentunderstanding.models import (
            ContentAnalyzer, ContentFieldSchema, ContentFieldDefinition,
            ContentFieldType, GenerationMethod, ContentAnalyzerConfig,
            ContentCategoryDefinition, DocumentContent,
        )
        from azure.core.credentials import AzureKeyCredential

        load_dotenv(override=True)
        endpoint = os.environ.get("CONTENTUNDERSTANDING_ENDPOINT", "")
        key = os.getenv("CONTENTUNDERSTANDING_KEY")

        if not endpoint:
            return _output_tabs("⚠️ CONTENTUNDERSTANDING_ENDPOINT not set", ""), "ERROR", "red"

        credential = AzureKeyCredential(key) if key else None
        client = ContentUnderstandingClient(endpoint=endpoint, credential=credential,
                                            user_agent="build26-DEM331-demo/1.0.0")

        output_lines = []
        try:
            # Route all 6 documents through classifier (deploy + classify)
            CLASSIFIER_ID = "fiberFieldDocClassifier"

            test_docs = [
                ("cl_v3_site_b_photo_log_2026_04_10.pdf", "Photo_Log"),
                ("cl_v3_site_b_video_inspection_2026_04_10.pdf", "Video_Inspection"),
                ("cl_v3_engineering_splice_sheet_2026_04_28.pdf", "Splice_Sheet"),
                ("cl_v3_datacenter_fiber_routing_2026_04_28.pdf", "Fiber_Routing"),
                ("cl_v3_equipment_spec_sheet_2026_05_03.pdf", "Equipment_Spec"),
                ("cl_v3_datacenter_plant_diagram_2026_04_28.pdf", "Plant_Diagram"),
            ]

            classify_output = "Classification Results:\n\n"
            extraction_output = ""

            for filename, expected in test_docs:
                doc_path = DOCS_DIR / filename
                if not doc_path.exists():
                    classify_output += f"  {filename}: ⚠️ file not found\n"
                    continue

                with open(doc_path, "rb") as f:
                    p = client.begin_analyze_binary(
                        analyzer_id=CLASSIFIER_ID, binary_input=f.read()
                    )
                r = p.result()

                if r.contents:
                    dc = cast(DocumentContent, r.contents[0])
                    classified = "(unknown)"
                    if dc.segments and len(dc.segments) > 0:
                        classified = dc.segments[0].category or "(unknown)"
                    correct = "✅" if classified == expected else "❌"
                    classify_output += f"  {filename:<50} {classified:<20} {correct}\n"

                    if dc.fields:
                        extraction_output += f"\n━━━ {classified} ━━━\n"
                        for fname, fval in dc.fields.items():
                            v = fval.value if fval.value is not None else fval.value_string
                            extraction_output += f"  {fname}: {v}\n"
                else:
                    classify_output += f"  {filename}: empty result\n"

            return _output_tabs(extraction_output or "No extractions returned", classify_output), "LIVE", "green"

        except Exception as e:
            return _output_tabs(f"⚠️ Error: {type(e).__name__}: {e}", ""), "ERROR", "red"

    return no_update, no_update, no_update
