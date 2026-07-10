"""Act 3 — Custom analyzers and classifier routing.

Mirrors notebook cells 21 (analyzer definitions), 22 (deploy), 24 (classifier),
25 (single-doc classify), 26 (classify all 6), and 28-40 (per-doc custom extraction
+ agent reasoning).
Output starts empty — user clicks Run Live or Pre-processed.
"""

from pathlib import Path
from typing import Optional

from dash import Input, Output, callback, ctx, html, no_update
import dash_mantine_components as dmc

from services.cu_client import (
    CLASSIFIER_ID,
    agent_reason,
    get_cu_client,
    is_configured,
)

DOCS_DIR = Path(__file__).parent.parent.parent / "src" / "sample-data" / "documents"


# Files routed by classifier → analyzer. Tuple format:
#   (filename, expected_category, analyzer_id, doc_description_for_agent, question_for_agent)
DOC_PIPELINE = [
    ("cl_v3_site_b_photo_log_2026_04_10.pdf",       "Photo_Log",
     "photoLogTriageAnalyzer",
     "Photo Log — GPS-indexed field photos with priority ratings",
     "What's the triage assessment? How urgent is dispatch?"),
    ("cl_v3_site_b_video_inspection_2026_04_10.pdf", "Inspection_Report",
     "inspectionReportAnalyzer",
     "Inspection Report — 6 segments with damage classification",
     "Does video confirm photo evidence? Is damage stable or worsening?"),
    ("cl_v3_engineering_splice_sheet_2026_04_28.pdf", "Splice_Sheet",
     "fiberSpliceExtractor",
     "Engineering Splice Sheet — strand-level OTDR loss measurements",
     "What is the root cause? Should we re-splice or replace conduit?"),
    ("cl_v3_datacenter_fiber_routing_2026_04_28.pdf", "Fiber_Routing",
     "fiberRoutingAnalyzer",
     "Fiber Routing Diagram — primary and backup paths with customer counts",
     "Is there redundancy? What happens if this conduit fails?"),
    ("cl_v3_equipment_spec_sheet_2026_05_03.pdf",    "Equipment_Spec",
     "equipmentProcurementAnalyzer",
     "Equipment Spec & Materials Order — procurement data with costs and lead times",
     "Are we within budget? Any schedule risks from backorders?"),
    ("cl_v3_datacenter_plant_diagram_2026_04_28.pdf", "Plant_Diagram",
     "plantDiagramAnalyzer",
     "Data Center Plant Diagram — facility layout with fiber paths and cooling",
     "Where does fiber enter? Any secondary risks in the affected zone?"),
]


# ---------------------------------------------------------------------------
# Displayed code — condensed from notebook cells 21, 22, 24, 26
# ---------------------------------------------------------------------------

ANALYZER_CODE = '''# Define ALL 6 custom analyzers — mirrors notebook cell 21
CUSTOM_ANALYZERS = {
    "photoLogTriageAnalyzer": {
        "description": "Triage field photo logs — priority findings + dispatch urgency.",
        "baseAnalyzerId": "prebuilt-document",
        "models": {"completion": "prebuilt-analyzer-completion"},
        "fieldSchema": {"fields": {
            "HighPriorityCount": {"type": "integer", "method": "generate",
                "description": "Count of photos marked HIGH priority."},
            "CriticalFindings":  {"type": "string",  "method": "generate",
                "description": "Summarize HIGH-priority findings with locations."},
            "DispatchUrgency":   {"type": "string",  "method": "generate",
                "description": "IMMEDIATE (>3 HIGH) / URGENT (1-3 HIGH) / SCHEDULED."},
        }},
    },
    "inspectionReportAnalyzer": {
        "description": "Extract critical segments and escalation needs from inspection report indices.",
        "baseAnalyzerId": "prebuilt-document",
        "models": {"completion": "prebuilt-analyzer-completion"},
        "fieldSchema": {"fields": {
            "CriticalSegments":   {"type": "string", "method": "generate",
                "description": "Segments marked CRITICAL with timestamps and content."},
            "EscalationRequired": {"type": "string", "method": "generate",
                "description": "YES / NO with one-sentence reasoning."},
            "DamageProgression":  {"type": "string", "method": "generate",
                "description": "Stable / worsening / deteriorating with evidence."},
        }},
    },
    "fiberSpliceExtractor": {
        "description": "Extract strand-level OTDR loss data and failure modes from splice sheets.",
        "baseAnalyzerId": "prebuilt-document",
        "models": {"completion": "prebuilt-analyzer-completion"},
        "fieldSchema": {"fields": {
            "CableType":                 {"type": "string",  "method": "generate",
                "description": "Cable type/standard (e.g. 'G.652D Single-Mode')."},
            "StrandCount":               {"type": "integer", "method": "generate",
                "description": "Total fiber strands tested."},
            "FailedStrands":             {"type": "string",  "method": "generate",
                "description": "MARGINAL/FAIL strands with ID, color, loss, status."},
            "FailureMode":               {"type": "string",  "method": "generate",
                "description": "Root cause from engineering notes."},
            "MaxLoss":                   {"type": "number",  "method": "generate",
                "description": "Highest loss value (dB/km) among all strands."},
            "EngineeringRecommendation": {"type": "string",  "method": "generate",
                "description": "Re-splice / conduit replacement / other."},
        }},
    },
    "fiberRoutingAnalyzer": {
        "description": "Identify redundancy gaps and single points of failure in fiber routes.",
        "baseAnalyzerId": "prebuilt-document",
        "models": {"completion": "prebuilt-analyzer-completion"},
        "fieldSchema": {"fields": {
            "RedundancyGap":        {"type": "string",  "method": "generate",
                "description": "Where primary + backup share infrastructure."},
            "AffectedCustomers":    {"type": "integer", "method": "generate",
                "description": "Customers at risk from the single point of failure."},
            "SinglePointOfFailure": {"type": "string",  "method": "generate",
                "description": "Element that takes down both paths if it fails."},
            "RerouteOption":        {"type": "string",  "method": "generate",
                "description": "Alternative route or 'No alternative'."},
        }},
    },
    "equipmentProcurementAnalyzer": {
        "description": "Extract procurement-critical data — costs, lead times, budget verdict.",
        "baseAnalyzerId": "prebuilt-document",
        "models": {"completion": "prebuilt-analyzer-completion"},
        "fieldSchema": {"fields": {
            "TotalCost":        {"type": "number",  "method": "generate",
                "description": "Sum of line item totals (no currency symbol)."},
            "BackorderRisk":    {"type": "string",  "method": "generate",
                "description": "Items backordered or with >5 day lead time."},
            "CriticalPathDays": {"type": "integer", "method": "generate",
                "description": "Longest lead time — determines earliest start date."},
            "BudgetVerdict":    {"type": "string",  "method": "generate",
                "description": "WITHIN / OVER BUDGET ($X of $Y)."},
        }},
    },
    "plantDiagramAnalyzer": {
        "description": "Identify affected zones, thermal risks, and fiber connectivity in plant diagrams.",
        "baseAnalyzerId": "prebuilt-document",
        "models": {"completion": "prebuilt-analyzer-completion"},
        "fieldSchema": {"fields": {
            "FiberEntryPoint": {"type": "string", "method": "generate",
                "description": "Where external fiber enters (ODF, MDF, demarc)."},
            "ThermalRisk":     {"type": "string", "method": "generate",
                "description": "Cooling concerns or 'No thermal issues noted'."},
            "AffectedZone":    {"type": "string", "method": "generate",
                "description": "Racks/rows/zones affected by the fiber issue."},
            "FieldNotes":      {"type": "string", "method": "generate",
                "description": "Handwritten notes, annotations, approval stamps."},
        }},
    },
}

# Deploy each analyzer with the SDK — mirrors notebook cell 22
from azure.ai.contentunderstanding.models import (
    ContentAnalyzer, ContentFieldSchema, ContentFieldDefinition,
    ContentFieldType, GenerationMethod,
)

_TYPE_MAP = {"string":  ContentFieldType.STRING,
             "integer": ContentFieldType.INTEGER,
             "number":  ContentFieldType.NUMBER}

for analyzer_id, schema in CUSTOM_ANALYZERS.items():
    fields = {
        name: ContentFieldDefinition(
            type=_TYPE_MAP[fdef["type"]],
            method=GenerationMethod.GENERATE,
            description=fdef["description"],
        )
        for name, fdef in schema["fieldSchema"]["fields"].items()
    }
    analyzer = ContentAnalyzer(
        base_analyzer_id=schema["baseAnalyzerId"],
        description=schema["description"],
        field_schema=ContentFieldSchema(fields=fields),
        models=schema["models"],
    )
    client.begin_create_analyzer(
        analyzer_id=analyzer_id, resource=analyzer, allow_replace=True
    ).result()
    print(f"  {analyzer_id:<32} ✅ ready")
'''

CLASSIFIER_CODE = '''# Deploy the classifier that auto-routes to custom analyzers — mirrors notebook cell 24
from azure.ai.contentunderstanding.models import (
    ContentAnalyzer, ContentAnalyzerConfig, ContentCategoryDefinition,
)

CLASSIFIER_ID = "fiberFieldDocClassifier"

# Each category description guides routing; analyzer_id points to a deployed analyzer.
categories = {
    "Photo_Log": ContentCategoryDefinition(
        description="GPS-indexed photo logs with HIGH/MEDIUM/LOW priority ratings.",
        analyzer_id="photoLogTriageAnalyzer",
    ),
    "Inspection_Report": ContentCategoryDefinition(
        description="Inspection report indices with numbered segments and timestamps.",
        analyzer_id="inspectionReportAnalyzer",
    ),
    "Splice_Sheet": ContentCategoryDefinition(
        description="Engineering splice sheets with strand-level OTDR loss data.",
        analyzer_id="fiberSpliceExtractor",
    ),
    "Fiber_Routing": ContentCategoryDefinition(
        description="Network fiber routing diagrams (primary + backup paths).",
        analyzer_id="fiberRoutingAnalyzer",
    ),
    "Equipment_Spec": ContentCategoryDefinition(
        description="Equipment specs / materials orders with costs and lead times.",
        analyzer_id="equipmentProcurementAnalyzer",
    ),
    "Plant_Diagram": ContentCategoryDefinition(
        description="Data-center plant diagrams (racks, fiber paths, cooling).",
        analyzer_id="plantDiagramAnalyzer",
    ),
}

classifier = ContentAnalyzer(
    base_analyzer_id="prebuilt-document",
    description="Classifies field service documents and routes to the correct custom analyzer",
    config=ContentAnalyzerConfig(
        return_details=True,
        enable_segment=False,
        content_categories=categories,
    ),
    models={"completion": "prebuilt-analyzer-completion"},
)
client.begin_create_analyzer(
    analyzer_id=CLASSIFIER_ID, resource=classifier, allow_replace=True
).result()

# Classify + extract in a single call — mirrors notebook cell 25
from typing import cast
from azure.ai.contentunderstanding.models import DocumentContent

with open(test_doc, "rb") as f:
    result = client.begin_analyze_binary(
        analyzer_id=CLASSIFIER_ID, binary_input=f.read()
    ).result()

doc = cast(DocumentContent, result.contents[0])
category = doc.segments[0].category if doc.segments else "(unknown)"
print(f"Category: {category}")
for name, fval in (doc.fields or {}).items():
    v = fval.value if fval.value is not None else fval.value_string
    print(f"  {name}: {v}")
'''


# ---------------------------------------------------------------------------
# Cached outputs — directly from notebook cells 26 + 29 + 31 + 33 + 36 + 38 + 40
# ---------------------------------------------------------------------------

CLASSIFICATION_CACHED = """Document                                           Classified As        Correct?
-------------------------------------------------- -------------------- --------
cl_v3_site_b_photo_log_2026_04_10.pdf              Photo_Log            ✅
cl_v3_site_b_video_inspection_2026_04_10.pdf       Inspection_Report    ✅
cl_v3_engineering_splice_sheet_2026_04_28.pdf      Splice_Sheet         ✅
cl_v3_datacenter_fiber_routing_2026_04_28.pdf      Fiber_Routing        ✅
cl_v3_equipment_spec_sheet_2026_05_03.pdf          Equipment_Spec       ✅
cl_v3_datacenter_plant_diagram_2026_04_28.pdf      Plant_Diagram        ✅
"""

EXTRACTIONS_CACHED = """━━━ Photo_Log → photoLogTriageAnalyzer ━━━━━━━━━━━━━━━━━━━━
  HighPriorityCount: 3
  CriticalFindings: Three HIGH-priority findings: (1) Pole TR-38 base erosion at GPS 34.0522,-118.2437, (2) Surface crack above conduit at GPS 34.0530,-118.2420, and (3) Section 5 pavement heave at GPS 34.0540,-118.2400. These are critical due to structural risks to the corridor, potential conduit failure, and possible service disruption.
  DispatchUrgency: URGENT (1-3 HIGH items). There are 3 HIGH-priority findings, which require prompt attention but do not exceed the threshold for IMMEDIATE dispatch.

AGENT [1/6]:
- The photo log identifies 3 HIGH-priority findings: pole base erosion, surface crack above conduit, and pavement heave, all posing structural and conduit risks.
- GPS coordinates confirm these issues are distributed along the Tower Ridge Corridor, directly affecting Segment 9 and potentially impacting 42 customers.
- The triage assessment rates dispatch urgency as URGENT, indicating prompt action is required, but it does not meet the IMMEDIATE threshold (more than 3 HIGH items).
- The critical findings specifically threaten conduit integrity and service continuity, increasing the risk of signal degradation.

Conclusion: Dispatch should be prioritized urgently for Segment 9, but immediate mobilization is not mandated based on current triage.


━━━ Inspection_Report → inspectionReportAnalyzer ━━━━━━━━━━━━━━━━━━
  CriticalSegments: VID-05 (52:30-78:00): Vault TV-3 -- CRITICAL (recurring); VID-06 (78:00-95:00): Section 5 -- heave (shared conduit)
  EscalationRequired: YES. Escalation to engineering is required due to the recurring and worsening crack in Vault TV-3 and pavement heave in Section 5, both of which threaten service continuity.
  DamageProgression: The damage is worsening, as evidenced by the Vault TV-3 conduit crack increasing from less than 1cm in January to 2cm in April, patch separation, and new ground movement and pavement heave observed.

AGENT [2/6]:
- Video inspection confirms photo evidence, showing recurring and worsening damage in Vault TV-3 (crack increased from <1cm in January to 2cm in April).
- Section 5 exhibits new ground movement and pavement heave, matching prior photo documentation and indicating shared conduit risk.
- Patch separation and escalation to engineering are recommended due to the threat to service continuity for 42 customers.
- Damage is not stable; it is actively worsening, as shown by crack progression and new heave.

Conclusion: Video evidence corroborates photo findings, and damage is worsening, requiring immediate engineering escalation.


━━━ Splice_Sheet → fiberSpliceExtractor ━━━━━━━━━━━━━━━━━━━━
  CableType: 12-SM OS2 Tight
  StrandCount: 12
  FailedStrands: SM-5 (Slate, 0.52 dB/km, MARGINAL); SM-7 (Red, 0.48 dB/km, MARGINAL); SM-11 (Rose, 0.55 dB/km, FAIL)
  FailureMode: Conduit is root cause.
  MaxLoss: 0.55
  EngineeringRecommendation: Aerial bypass for Route 2 BEFORE conduit replacement.

AGENT [3/6]:
- OTDR loss measurements show three strands with elevated attenuation: SM-5 (0.52 dB/km, marginal), SM-7 (0.48 dB/km, marginal), and SM-11 (0.55 dB/km, fail).
- The failure mode is explicitly identified as "Conduit is root cause," indicating physical conduit damage or contamination is impacting fiber performance.
- Engineering recommendation is to implement an aerial bypass for Route 2 before proceeding with conduit replacement, suggesting re-splicing alone will not resolve the issue.
- Max strand loss (0.55 dB/km) exceeds acceptable thresholds, confirming conduit-related degradation rather than splice faults.

Conclusion: The root cause is conduit failure; replacing the conduit (with interim aerial bypass) is necessary, not just re-splicing.


━━━ Fiber_Routing → fiberRoutingAnalyzer ━━━━━━━━━━━━━━━━━━━━
  RedundancyGap: Route 2 shares conduit with Route 1 in Sections 3-5
  AffectedCustomers: 42
  SinglePointOfFailure: Conduit CDT-TR-003, CDT-TR-004, CDT-TR-005 through Section 5 (shared by Route 1 and Route 2)
  RerouteOption: No alternative — full conduit replacement required

AGENT [4/6]:
- Both primary (Route 1) and backup (Route 2) fiber routes share the same conduit (CDT-TR-003, CDT-TR-004, CDT-TR-005) through Sections 3-5, creating a single point of failure.
- If this shared conduit fails, all 42 customers in the affected segment will lose service, as both routes are compromised.
- There is no alternative reroute option available; full conduit replacement is required to restore connectivity.
- The redundancy gap means that the backup path does not provide true protection in this segment.

Conclusion: There is no effective redundancy in Sections 3-5—failure of the shared conduit will result in total service loss for 42 customers.


━━━ Equipment_Spec → equipmentProcurementAnalyzer ━━━━━━━━━━━━━━━━━━━━
  TotalCost: 6829.0
  BackorderRisk: Vault Anchors (VA-HEL-6FT): backorder (ETA pushed to 05/15)
  CriticalPathDays: 10
  BudgetVerdict: WITHIN BUDGET ($6829 of $120000)

AGENT [5/6]:
- The total procurement cost is $6,829, which is well within the allocated budget of $120,000.
- Vault Anchors (VA-HEL-6FT) are on backorder, with their estimated arrival date pushed to 05/15.
- The critical path for equipment delivery is 10 days, but the backorder could extend this timeline if anchors are essential for restoration.
- No other materials are flagged for backorder, minimizing broader supply chain risks.
- Schedule risk exists due to the delayed Vault Anchors, potentially impacting restoration for 42 customers.

Conclusion: We are within budget, but the Vault Anchor backorder (ETA 05/15) poses a schedule risk for Segment 9 restoration.


━━━ Plant_Diagram → plantDiagramAnalyzer ━━━━━━━━━━━━━━━━━━━━
  FiberEntryPoint: CARRIER DEMARC
  ThermalRisk: CRAC-2 issue. If conduit fails, ODF-A+B down.
  AffectedZone: C05-C08
  FieldNotes: NOTE (05/01): FIBER: ODF-A/B fed via Sec 3-5 (42 cust). C05-C08 hot. CRAC-2 issue. If conduit fails, ODF-A+B down.
Ref: FRD-2026-04-28, FSE-2026-0041. --Sharma

APPROVED:

K. Nakamura, PE 2026-04-28

M. Webb, Ops Mgr 2026-04-29

AGENT [6/6]:
- Fiber enters the facility at the CARRIER DEMARC point, as indicated in the diagram.
- The affected zone is C05-C08, which is currently experiencing elevated temperatures ("hot"), increasing operational risk.
- There is a secondary risk from the CRAC-2 cooling unit; if it fails, both ODF-A and ODF-B (fiber distribution frames) will go down.
- The fiber serving 42 customers is routed via Sections 3-5, directly through the affected zone.
- If the conduit in C05-C08 fails, signal loss will impact both ODF-A and ODF-B, amplifying customer impact.

Conclusion: Fiber enters at CARRIER DEMARC; secondary risk is high in C05-C08 due to CRAC-2 issues and potential conduit failure affecting ODF-A/B and 42 customers.
"""


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


def _output_tabs(extractions_text, classification_text):
    return [
        html.Div("Output", className="demo-panel-header"),
        dmc.Tabs(
            value="extractions",
            children=[
                dmc.TabsList([
                    dmc.TabsTab("Field Extractions", value="extractions"),
                    dmc.TabsTab("Classification", value="classification"),
                ]),
                dmc.TabsPanel(html.Pre(extractions_text, style=PRE_STYLE),
                              value="extractions", pt="md"),
                dmc.TabsPanel(html.Pre(classification_text, style=PRE_STYLE),
                              value="classification", pt="md"),
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
    live_available = is_configured()

    return html.Div([
        html.Div(
            style={
                "display": "flex", "justifyContent": "space-between", "alignItems": "center",
                "padding": "16px 24px 0 24px",
            },
            children=[
                dmc.Group([
                    dmc.Badge("Act 3", color="teal", variant="filled", size="lg"),
                    dmc.Title("Deep Extraction — Custom Analyzers & Classification",
                              order=4, c="white"),
                ]),
                dmc.Group([
                    dmc.Badge("READY", color="gray", variant="light", size="sm",
                              id="act3-mode-badge"),
                    dmc.Button("\u25B6 Run Live", id="act3-run-btn", variant="light",
                               size="xs", color="green", disabled=not live_available),
                    dmc.Button("\U0001F4E6 Pre-processed", id="act3-cached-btn",
                               variant="light", size="xs", color="blue"),
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
                                dmc.CodeHighlight(code=ANALYZER_CODE, language="python",
                                                  withCopyButton=False,
                                                  style={"fontSize": "0.70rem"}),
                                value="analyzers", pt="md",
                            ),
                            dmc.TabsPanel(
                                dmc.CodeHighlight(code=CLASSIFIER_CODE, language="python",
                                                  withCopyButton=False,
                                                  style={"fontSize": "0.70rem"}),
                                value="classifier", pt="md",
                            ),
                        ],
                    ),
                ]),

                # Center: 6 Documents
                html.Div(className="demo-panel", children=[
                    html.Div("\U0001F4C1 6 Field Documents", className="demo-panel-header"),
                    dmc.Stack([
                        _doc_card("Photo Log", "GPS-indexed field photos with priority ratings", "teal"),
                        _doc_card("Inspection Report", "6 segments with damage classification", "blue"),
                        _doc_card("Splice Sheet", "Strand-level OTDR loss measurements", "violet"),
                        _doc_card("Fiber Routing", "Primary & backup path topology", "orange"),
                        _doc_card("Equipment Spec", "Procurement data & budget", "green"),
                        _doc_card("Plant Diagram", "Facility layout with fiber paths", "pink"),
                    ], gap="xs"),
                ]),

                # Right: Output (starts empty)
                html.Div(className="demo-panel", id="act3-output-panel", children=_empty_output()),
            ],
        ),

        html.Div("\u2190 \u2192 to navigate", className="nav-hint"),
    ])


# ---------------------------------------------------------------------------
# Live runner — classify + extract for all 6 docs, then agent_reason per doc
# ---------------------------------------------------------------------------


def _format_field_value(fval) -> str:
    v = fval.value if fval.value is not None else fval.value_string
    return str(v)


def _run_live_extractions():
    """Run classifier on each doc for classification table, then the matched
    custom analyzer for field extraction + agent_reason. Mirrors notebook
    cells 26 + 28-40."""
    from azure.ai.contentunderstanding import to_llm_input
    from typing import cast
    from azure.ai.contentunderstanding.models import DocumentContent

    client = get_cu_client()
    if client is None:
        return ("\u26A0\uFE0F CU client not configured", "\u26A0\uFE0F CU client not configured")

    try:
        from scripts.deploy_analyzers import ensure_deployed
        ensure_deployed(client)
    except Exception as exc:
        warn = f"\u26A0\uFE0F Could not deploy custom analyzers: {exc}"
        return (warn, warn)

    classify_lines = [
        f"{'Document':<50} {'Classified As':<20} {'Correct?'}",
        f"{'-'*50} {'-'*20} {'-'*8}",
    ]
    extract_lines: list[str] = []

    for i, (filename, expected, analyzer_id, doc_desc, question) in enumerate(DOC_PIPELINE, start=1):
        doc_path = DOCS_DIR / filename
        if not doc_path.exists():
            classify_lines.append(f"{filename:<50} {'(missing)':<20} ❌")
            continue

        pdf_bytes = doc_path.read_bytes()

        # Classify (cell 26 pattern)
        try:
            classify_result = client.begin_analyze_binary(
                analyzer_id=CLASSIFIER_ID, binary_input=pdf_bytes
            ).result()
            cdc = cast(DocumentContent, classify_result.contents[0]) if classify_result.contents else None
            category = (cdc.segments[0].category if cdc and cdc.segments else None) or "(unknown)"
        except Exception as e:
            category = f"(error: {type(e).__name__})"
            classify_lines.append(f"{filename:<50} {category:<20} ❌")
            extract_lines.append(f"━━━ {filename} ━━━\n  ⚠️ Classify error: {e}\n")
            continue
        correct = "✅" if category == expected else "❌"
        classify_lines.append(f"{filename:<50} {category:<20} {correct}")

        # Extract fields via the actual custom analyzer (cells 28-40 pattern)
        extract_lines.append(f"━━━ {category} → {analyzer_id} ━━━━━━━━━━━━━━━━━━━━")
        try:
            extract_result = client.begin_analyze_binary(
                analyzer_id=analyzer_id, binary_input=pdf_bytes
            ).result()
            edc = cast(DocumentContent, extract_result.contents[0]) if extract_result.contents else None
            if edc and edc.fields:
                for fname, fval in edc.fields.items():
                    extract_lines.append(f"  {fname}: {_format_field_value(fval)}")
            else:
                extract_lines.append("  (no fields returned)")
        except Exception as e:
            extract_lines.append(f"  ⚠️ Extract error: {type(e).__name__}: {e}")
            extract_result = None

        # Agent reasoning per doc (notebook cells 29/31/33/36/38/40)
        if extract_result is not None:
            try:
                reasoning = agent_reason(
                    to_llm_input(extract_result, include_markdown=False),
                    doc_desc, question,
                )
            except Exception as e:  # pragma: no cover
                reasoning = f"(agent reasoning failed: {e})"
            extract_lines.append("")
            extract_lines.append(f"AGENT [{i}/6]:")
            extract_lines.append(reasoning)
        extract_lines.append("")

    return ("\n".join(extract_lines), "\n".join(classify_lines))


@callback(
    Output("act3-output-panel", "children"),
    Output("act3-mode-badge", "children"),
    Output("act3-mode-badge", "color"),
    Input("act3-run-btn", "n_clicks"),
    Input("act3-cached-btn", "n_clicks"),
    prevent_initial_call=True,
)
def run_act3(run_clicks, cached_clicks):
    triggered = ctx.triggered_id

    if triggered == "act3-cached-btn":
        return _output_tabs(EXTRACTIONS_CACHED, CLASSIFICATION_CACHED), "PRE-PROCESSED", "blue"

    if triggered == "act3-run-btn":
        try:
            extractions, classification = _run_live_extractions()
            return _output_tabs(extractions, classification), "LIVE", "green"
        except Exception as e:
            return (
                _output_tabs(f"⚠️ Error: {type(e).__name__}: {e}", ""),
                "ERROR", "red",
            )

    return no_update, no_update, no_update
