"""One-shot deploy of the six custom analyzers + classifier used by Act 3.

Mirrors notebook cells 21, 22, and 24 of `src/demo_fiber_cut_MAF.ipynb`.
Run this once after pointing `.env` at a new Content Understanding endpoint:

    cd demo-app
    .\.venv\Scripts\python.exe scripts\deploy_analyzers.py

Re-running is safe — every deploy uses `allow_replace=True`.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_DEMO_APP = Path(__file__).resolve().parent.parent
if str(REPO_DEMO_APP) not in sys.path:
    sys.path.insert(0, str(REPO_DEMO_APP))

from services.cu_client import CLASSIFIER_ID, get_cu_client, is_configured  # noqa: E402


CUSTOM_ANALYZERS: dict[str, dict] = {
    "photoLogTriageAnalyzer": {
        "description": "Triage field photo logs — extract priority findings and recommend dispatch urgency for the repair agent.",
        "baseAnalyzerId": "prebuilt-document",
        "models": {"completion": "gpt-4.1"},
        "fields": {
            "HighPriorityCount": ("integer", "Count of photos/entries marked HIGH priority."),
            "CriticalFindings":  ("string",  "Summarize all HIGH-priority findings in one paragraph. Include location (GPS if available), subject, and why it's critical."),
            "DispatchUrgency":   ("string",  "Based on the priority distribution and findings, classify overall dispatch urgency as: IMMEDIATE (>3 HIGH items or safety risk), URGENT (1-3 HIGH items), or SCHEDULED (no HIGH items). Explain your reasoning in one sentence."),
        },
    },
    "inspectionReportAnalyzer": {
        "description": "Extract critical segments and escalation needs from video inspection indices for the repair agent.",
        "baseAnalyzerId": "prebuilt-document",
        "models": {"completion": "gpt-4.1"},
        "fields": {
            "CriticalSegments":   ("string", "List video segments marked CRITICAL or 'Concern' with their timestamps and content. Format: 'VID-05 (52:30-78:00): Vault TV-3 CRITICAL damage; VID-06 (78:00-95:00): pavement heave'."),
            "EscalationRequired": ("string", "YES or NO — is escalation to engineering required based on the video findings? Explain in one sentence."),
            "DamageProgression":  ("string", "Infer whether the damage is stable, worsening, or rapidly deteriorating based on segment descriptions, action items, and any temporal references. One sentence with evidence."),
        },
    },
    "fiberSpliceExtractor": {
        "description": "Extract critical fiber splice data for the repair response agent.",
        "baseAnalyzerId": "prebuilt-document",
        "models": {"completion": "gpt-4.1"},
        "fields": {
            "CableType":                 ("string",  "The fiber cable type/standard (e.g., 'G.652D Single-Mode', '12-strand SM OS2')."),
            "StrandCount":               ("integer", "Total number of fiber strands tested (exclude header row)."),
            "FailedStrands":             ("string",  "List strands with MARGINAL or FAIL status: 'SM-5 (Slate, 0.52 dB/km, MARGINAL); SM-11 (Rose, 0.55 dB/km, FAIL)'. Include strand ID, color, loss, status."),
            "FailureMode":               ("string",  "Root cause of degradation from engineering notes (e.g., 'micro-bend from conduit pressure')."),
            "MaxLoss":                   ("number",  "Highest loss value (dB/km) among all strands."),
            "EngineeringRecommendation": ("string",  "Engineer's recommendation: re-splice, conduit replacement, or other."),
        },
    },
    "fiberRoutingAnalyzer": {
        "description": "Analyze fiber routing diagrams to identify redundancy gaps and single points of failure for the repair agent.",
        "baseAnalyzerId": "prebuilt-document",
        "models": {"completion": "gpt-4.1"},
        "fields": {
            "RedundancyGap":        ("string",  "Identify where primary and backup routes share infrastructure (conduit, vault, pole). Format: 'Route 2 shares conduit with Route 1 in Sections 3-5'. If none found, say 'No gap identified'."),
            "AffectedCustomers":    ("integer", "Number of customers at risk if the identified single point of failure is hit. Look for customer counts in route tables."),
            "SinglePointOfFailure": ("string",  "The specific infrastructure element that, if it fails, takes down BOTH primary and backup paths. Include location and what it is."),
            "RerouteOption":        ("string",  "Infer if there's any alternative route available based on the network topology. If yes, describe it. If no, state 'No alternative — full conduit replacement required'."),
        },
    },
    "equipmentProcurementAnalyzer": {
        "description": "Extract procurement-critical data from equipment specs and materials orders for budget/scheduling decisions.",
        "baseAnalyzerId": "prebuilt-document",
        "models": {"completion": "gpt-4.1"},
        "fields": {
            "TotalCost":         ("number",  "Total cost of all materials in the order (sum of line item totals). Return as a number without currency symbol."),
            "BackorderRisk":     ("string",  "List any items that are backordered, out of stock, or have lead times >5 days. Format: 'Item (P/N): lead time or status'. If none, say 'All items available'."),
            "CriticalPathDays":  ("integer", "The longest lead time (in days) among all items — this determines earliest possible start date for the repair."),
            "BudgetVerdict":     ("string",  "Compare total cost against any mentioned approved budget. State: 'WITHIN BUDGET ($X of $Y)' or 'OVER BUDGET ($X of $Y)'. If no budget mentioned, state 'No budget reference found'."),
        },
    },
    "plantDiagramAnalyzer": {
        "description": "Analyze data center plant diagrams to identify affected zones, thermal risks, and fiber connectivity for repair planning.",
        "baseAnalyzerId": "prebuilt-document",
        "models": {"completion": "gpt-4.1"},
        "fields": {
            "FiberEntryPoint": ("string", "Where external fiber enters the facility. Look for ODF, MDF, fiber tray, or demarc labels."),
            "ThermalRisk":     ("string", "Any thermal or cooling concerns mentioned (hot spots, CRAC issues, blocked airflow). If none, say 'No thermal issues noted'."),
            "AffectedZone":    ("string", "Which racks, rows, or zones would be affected by the fiber issue being investigated. Look for highlighted areas, field notes, or damage annotations."),
            "FieldNotes":      ("string", "Any handwritten or appended field notes, engineer annotations, or approval stamps with dates."),
        },
    },
}

CLASSIFIER_CATEGORIES = {
    "Photo_Log":        ("photoLogTriageAnalyzer",
                         "GPS-indexed photo logs from field inspections with priority ratings (HIGH/MEDIUM/LOW) for each photo entry, documenting site conditions and damage."),
    "Inspection_Report": ("inspectionReportAnalyzer",
                         "Video inspection index documents listing numbered video segments with timestamps, locations, damage classifications, and action items."),
    "Splice_Sheet":     ("fiberSpliceExtractor",
                         "Engineering fiber splice sheets with strand-level OTDR loss measurements, color codes, pass/fail status, and technician notes about failure modes."),
    "Fiber_Routing":    ("fiberRoutingAnalyzer",
                         "Network fiber routing diagrams showing primary and backup paths, conduit sections, customer counts per route, and redundancy information."),
    "Equipment_Spec":   ("equipmentProcurementAnalyzer",
                         "Equipment specification and materials order documents with part numbers, quantities, costs, lead times, and procurement status."),
    "Plant_Diagram":    ("plantDiagramAnalyzer",
                         "Data center or facility plant diagrams showing rack layouts, fiber paths, cooling systems, and field annotations."),
}


def deploy_all(client, *, log=print) -> None:
    """Deploy all 6 custom analyzers + the classifier (idempotent via allow_replace=True)."""
    from azure.ai.contentunderstanding.models import (
        ContentAnalyzer,
        ContentAnalyzerConfig,
        ContentCategoryDefinition,
        ContentFieldDefinition,
        ContentFieldSchema,
        ContentFieldType,
        GenerationMethod,
    )

    type_map = {
        "string":  ContentFieldType.STRING,
        "integer": ContentFieldType.INTEGER,
        "number":  ContentFieldType.NUMBER,
    }

    log(f"{'Analyzer':<32} {'Status':<12}")
    log(f"{'-'*32} {'-'*12}")

    for analyzer_id, spec in CUSTOM_ANALYZERS.items():
        fields = {
            name: ContentFieldDefinition(
                type=type_map[ftype],
                method=GenerationMethod.GENERATE,
                description=fdesc,
            )
            for name, (ftype, fdesc) in spec["fields"].items()
        }
        analyzer = ContentAnalyzer(
            base_analyzer_id=spec["baseAnalyzerId"],
            description=spec["description"],
            field_schema=ContentFieldSchema(fields=fields),
            models=spec["models"],
        )
        poller = client.begin_create_analyzer(
            analyzer_id=analyzer_id, resource=analyzer, allow_replace=True
        )
        poller.result()
        log(f"{analyzer_id:<32} ready")

    log("")
    log(f"Deploying classifier: {CLASSIFIER_ID}")
    categories = {
        name: ContentCategoryDefinition(description=desc, analyzer_id=analyzer_id)
        for name, (analyzer_id, desc) in CLASSIFIER_CATEGORIES.items()
    }
    classifier = ContentAnalyzer(
        base_analyzer_id="prebuilt-document",
        description="Classifies field service documents and routes to the correct custom analyzer",
        config=ContentAnalyzerConfig(
            return_details=True,
            enable_segment=False,
            content_categories=categories,
        ),
        models={"completion": "gpt-4.1"},
    )
    poller = client.begin_create_analyzer(
        analyzer_id=CLASSIFIER_ID, resource=classifier, allow_replace=True
    )
    poller.result()
    log(f"Classifier '{CLASSIFIER_ID}' deployed ({len(categories)} categories)")


def _classifier_categories(analyzer):
    """Extract the deployed classifier's category names. Returns ``None`` if we
    cannot introspect the analyzer (in which case the caller should redeploy)."""
    try:
        config = getattr(analyzer, "config", None)
        if config is None and hasattr(analyzer, "get"):
            config = analyzer.get("config")
        if config is None:
            return None
        cats = getattr(config, "content_categories", None)
        if cats is None and hasattr(config, "get"):
            cats = config.get("content_categories")
        if cats is None:
            return None
        if hasattr(cats, "keys"):
            return set(cats.keys())
        return set(cats)
    except Exception:
        return None


def ensure_deployed(client, *, log=print) -> bool:
    """Ensure all analyzers + classifier are deployed AND match current code.

    Redeploys when:
      * Classifier doesn't exist on the endpoint.
      * Classifier exists but its categories drifted from ``CLASSIFIER_CATEGORIES``
        (e.g. after a rename like ``Video_Inspection`` → ``Inspection_Report``).
      * Any expected custom analyzer is missing on the endpoint.

    Returns True if anything was deployed."""
    from azure.core.exceptions import ResourceNotFoundError, HttpResponseError

    def _is_404(exc: BaseException) -> bool:
        return isinstance(exc, ResourceNotFoundError) or (
            isinstance(exc, HttpResponseError)
            and getattr(exc, "status_code", None) == 404
        )

    needs_redeploy = False
    reason = ""

    # 1. Classifier must exist AND its categories must match current code.
    try:
        existing = client.get_analyzer(analyzer_id=CLASSIFIER_ID)
        deployed_cats = _classifier_categories(existing)
        expected_cats = set(CLASSIFIER_CATEGORIES.keys())
        if deployed_cats is None:
            needs_redeploy = True
            reason = "could not verify classifier categories"
        elif deployed_cats != expected_cats:
            needs_redeploy = True
            reason = (
                f"classifier categories drifted "
                f"(deployed={sorted(deployed_cats)} vs expected={sorted(expected_cats)})"
            )
    except Exception as exc:
        if _is_404(exc):
            needs_redeploy = True
            reason = f"classifier '{CLASSIFIER_ID}' missing"
        else:
            raise

    # 2. Every custom analyzer referenced by current code must exist.
    if not needs_redeploy:
        for analyzer_id in CUSTOM_ANALYZERS.keys():
            try:
                client.get_analyzer(analyzer_id=analyzer_id)
            except Exception as exc:
                if _is_404(exc):
                    needs_redeploy = True
                    reason = f"custom analyzer '{analyzer_id}' missing"
                    break
                raise

    if needs_redeploy:
        log(f"Redeploying analyzers — {reason}...")
        deploy_all(client, log=log)
        return True
    return False


def main() -> int:
    if not is_configured():
        print("ERROR: CONTENTUNDERSTANDING_ENDPOINT is not configured in .env")
        return 1

    client = get_cu_client()
    if client is None:
        print("ERROR: could not construct Content Understanding client")
        return 1

    try:
        deploy_all(client)
    except Exception as exc:
        print(f"Deployment FAILED: {exc}")
        return 2

    print()
    print("All 6 custom analyzers + 1 classifier are ready on the configured endpoint.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
