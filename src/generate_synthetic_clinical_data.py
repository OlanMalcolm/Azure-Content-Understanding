"""Generate local, fictional clinical PDFs for the notebook demo.

The generated documents contain no patient information and exist only to exercise
the Content Understanding notebook when the optional public datasets are absent.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


CATEGORIES = (
    "progress_note",
    "lab_report",
    "prescription",
    "vitals_flowsheet",
    "imaging_report",
    "claim_form",
    "referral_intake",
)
CASE_COUNT = 5

STYLES = getSampleStyleSheet()
NOTICE_STYLE = ParagraphStyle(
    "SyntheticNotice",
    parent=STYLES["BodyText"],
    textColor=colors.HexColor("#8A1C1C"),
    fontSize=8,
    leading=10,
)
SMALL_STYLE = ParagraphStyle(
    "SyntheticSmall",
    parent=STYLES["BodyText"],
    fontSize=9,
    leading=12,
)


def _paragraph(text: str, style: ParagraphStyle | None = None) -> Paragraph:
    return Paragraph(text, style or STYLES["BodyText"])


def _table(rows: list[list[str]], widths: list[float] | None = None) -> Table:
    table = Table(rows, colWidths=widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DCE6F1")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#102A43")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#9FB3C8")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def _header(title: str, case_number: int) -> list:
    return [
        _paragraph(title, STYLES["Title"]),
        Spacer(1, 0.08 * inch),
        _paragraph(
            "SYNTHETIC TRAINING DATA - NO REAL PATIENT INFORMATION - NOT FOR CLINICAL USE",
            NOTICE_STYLE,
        ),
        _paragraph(f"Fictional case identifier: DEMO-CNH-{case_number:03d}", SMALL_STYLE),
        Spacer(1, 0.14 * inch),
    ]


def _progress_note(case_number: int) -> list:
    return _header("Preoperative Progress Note", case_number) + [
        _paragraph("<b>Visit type:</b> Preoperative review for fictional lumbar procedure"),
        _paragraph(
            "<b>History:</b> Demo patient reports intermittent lower back discomfort. "
            "No acute neurologic symptoms are documented in this fictional record."
        ),
        _paragraph(
            "<b>Assessment:</b> Preoperative documentation review is incomplete pending "
            "verification of laboratory results and consent signatures."
        ),
        _paragraph(
            "<b>Plan:</b> Confirm the most recent lab panel, medication list, and consent "
            "before final clearance. Escalate discrepancies to the reviewing clinician."
        ),
        Spacer(1, 0.12 * inch),
        _paragraph("Provider attestation: /s/ Demo Review Provider", SMALL_STYLE),
    ]


def _lab_report(case_number: int) -> list:
    potassium = "5.8" if case_number == 1 else f"{4.0 + case_number / 10:.1f}"
    potassium_flag = "HIGH - REVIEW" if case_number == 1 else "Normal"
    return _header("Laboratory Results Report", case_number) + [
        _paragraph("<b>Collection timestamp:</b> 2026-07-10 09:15"),
        Spacer(1, 0.08 * inch),
        _table(
            [
                ["Test", "Result", "Reference range", "Flag"],
                ["Hemoglobin", "13.8 g/dL", "12.0 - 16.0 g/dL", "Normal"],
                ["White blood cell count", "7.2 K/uL", "4.5 - 11.0 K/uL", "Normal"],
                ["Potassium", f"{potassium} mmol/L", "3.5 - 5.1 mmol/L", potassium_flag],
                ["Creatinine", "0.9 mg/dL", "0.6 - 1.2 mg/dL", "Normal"],
                ["INR", "1.0", "0.8 - 1.2", "Normal"],
            ],
            [1.7 * inch, 1.1 * inch, 1.55 * inch, 1.55 * inch],
        ),
        Spacer(1, 0.12 * inch),
        _paragraph(
            "Laboratory comment: This is fictional training data. Any flagged value requires "
            "review by a qualified clinician in a real workflow."
        ),
    ]


def _prescription(case_number: int) -> list:
    medications = (
        ("Acetaminophen", "500 mg", "Take one tablet every 6 hours as needed"),
        ("Ibuprofen", "200 mg", "Take one tablet with food as directed"),
        ("Ondansetron", "4 mg", "Take one tablet as needed for nausea"),
        ("Cyclobenzaprine", "5 mg", "Take one tablet at bedtime as directed"),
        ("Topical lidocaine", "4 percent patch", "Apply one patch to intact skin as directed"),
    )
    medication, dose, directions = medications[case_number - 1]
    return _header("Medication Order", case_number) + [
        _paragraph("<b>Medication:</b> " + medication),
        _paragraph("<b>Dose:</b> " + dose),
        _paragraph("<b>Directions:</b> " + directions),
        _paragraph("<b>Quantity:</b> 10"),
        _paragraph("<b>Refills:</b> 0"),
        Spacer(1, 0.18 * inch),
        _paragraph("Prescriber signature: /s/ Fictional Prescriber", SMALL_STYLE),
        _paragraph(
            "This printed sample does not demonstrate handwriting recognition. Use a permitted "
            "handwritten source image when demonstrating that capability."
        ),
    ]


def _vitals_flowsheet(case_number: int) -> list:
    return _header("Perioperative Vitals Flowsheet", case_number) + [
        _table(
            [
                ["Time", "Heart rate", "Blood pressure", "Respiratory rate", "Temperature", "SpO2"],
                ["08:00", "78 bpm", "122/78", "16", "36.8 C", "98%"],
                ["08:30", "80 bpm", "124/80", "16", "36.8 C", "98%"],
                ["09:00", f"{82 + case_number} bpm", "126/82", "17", "36.9 C", "97%"],
                ["09:30", f"{80 + case_number} bpm", "124/80", "16", "36.9 C", "98%"],
            ],
            [0.7 * inch, 1.0 * inch, 1.15 * inch, 1.2 * inch, 1.0 * inch, 0.7 * inch],
        ),
        Spacer(1, 0.12 * inch),
        _paragraph(
            "Nursing note: Fictitious trend shown for document-processing validation only. "
            "No patient-specific interpretation should be made from this sample."
        ),
    ]


def _imaging_report(case_number: int) -> list:
    return _header("Radiology Report", case_number) + [
        _paragraph("<b>Study:</b> Fictional lumbar spine MRI summary"),
        _paragraph("<b>Clinical history:</b> Preoperative planning in a demo scenario."),
        _paragraph(
            "<b>Technique:</b> Multiplanar image series reviewed for this synthetic report."
        ),
        _paragraph(
            "<b>Findings:</b> Demonstration text describes a mild lower-lumbar disc bulge "
            "without acute finding. This statement is fictional and has no diagnostic value."
        ),
        _paragraph(
            "<b>Impression:</b> Synthetic report used to test document classification, layout "
            "extraction, and LLM reasoning boundaries."
        ),
    ]


def _claim_form(case_number: int) -> list:
    consent_mark = "X"
    witness_mark = "X" if case_number != 1 else " "
    return _header("Procedure Consent and Encounter Form", case_number) + [
        _table(
            [
                ["Field", "Recorded value"],
                ["Procedure", "Fictional lumbar procedure"],
                ["Risks discussed", "Yes"],
                ["Alternatives discussed", "Yes"],
                ["Patient signature present", f"[{consent_mark}] Yes   [ ] No"],
                ["Witness signature present", f"[{witness_mark}] Yes   [ ] No"],
                ["Provider signature present", "[X] Yes   [ ] No"],
            ],
            [2.2 * inch, 3.3 * inch],
        ),
        Spacer(1, 0.12 * inch),
        _paragraph(
            "Consent validation note: This is a fictional form. It intentionally varies a "
            "signature field across samples to exercise exception handling."
        ),
    ]


def _referral_intake(case_number: int) -> list:
    urgency = "Urgent" if case_number == 1 else "Routine"
    return _header("Referral and Intake Form", case_number) + [
        _paragraph("<b>Referring department:</b> Fictional primary care clinic"),
        _paragraph("<b>Referral reason:</b> Preoperative assessment and documentation review."),
        _paragraph(f"<b>Urgency level:</b> {urgency}"),
        _paragraph(
            "<b>Intake summary:</b> This fictional referral requests review of a medication "
            "list, recent laboratory results, and procedure-consent completeness."
        ),
        _paragraph("<b>Completion status:</b> Pending specialist review"),
    ]


BUILDERS = {
    "progress_note": _progress_note,
    "lab_report": _lab_report,
    "prescription": _prescription,
    "vitals_flowsheet": _vitals_flowsheet,
    "imaging_report": _imaging_report,
    "claim_form": _claim_form,
    "referral_intake": _referral_intake,
}


def _write_pdf(path: Path, story: list) -> None:
    document = SimpleDocTemplate(
        str(path),
        pagesize=letter,
        leftMargin=0.55 * inch,
        rightMargin=0.55 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
        title=path.stem,
        author="Azure Content Understanding demo",
    )
    document.build(story)


def parse_args() -> argparse.Namespace:
    default_output = Path(__file__).parent / "sample-data" / "cnh-clinical"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=default_output,
        help=f"Directory that contains the category folders (default: {default_output})",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing synthetic PDFs instead of leaving them unchanged.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    created = 0
    skipped = 0

    for category in CATEGORIES:
        destination = args.output_dir / category
        destination.mkdir(parents=True, exist_ok=True)
        for case_number in range(1, CASE_COUNT + 1):
            output_path = destination / f"synthetic_{category}_{case_number:02d}.pdf"
            if output_path.exists() and not args.overwrite:
                skipped += 1
                continue
            _write_pdf(output_path, BUILDERS[category](case_number))
            created += 1

    print(f"Created {created} synthetic PDFs; left {skipped} existing PDFs unchanged.")
    print(f"Output directory: {args.output_dir}")
    print("All documents are fictional, contain no PHI, and are not for clinical use.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
