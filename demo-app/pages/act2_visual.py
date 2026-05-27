"""Act 2 — Multi-modal evidence: audio transcript + inspection photos.

Mirrors notebook cells 15-16 (audio extraction + agent reasoning) and
cells 18-19 (inspection photos with AI figure captions + agent reasoning).
Output starts empty — user clicks Run Live or Pre-processed.
"""

from pathlib import Path

from dash import Input, Output, callback, ctx, html, no_update
import dash_mantine_components as dmc

from services.cu_client import (
    agent_reason,
    analyze_document,
    extraction_summary,
    is_configured,
)

DOCS_DIR = Path(__file__).parent.parent.parent / "src" / "sample-data" / "documents"
AUDIO_PDF = DOCS_DIR / "cl_v3_site_b_audio_transcript_2026_04_15.pdf"
PHOTOS_PDF = DOCS_DIR / "cl_v3_inspection_photos_2026_05_02.pdf"


# ---------------------------------------------------------------------------
# Displayed code — literally from notebook cells 16 (audio) and 19 (photos)
# ---------------------------------------------------------------------------

AUDIO_CODE = '''# Notebook cell 16 — audio transcript with CU
display(Markdown("### CU Extraction: Conversational Content"))
audio_result = analyze_document(audio_transcript)
show_extraction_summary(audio_result)

audio_md = audio_result.contents[0].markdown
print(audio_md[:1200])

print("\\n" + "─" * 60)
reasoning = agent_reason(
    to_llm_input(audio_result),
    "Field Audio Transcript — technician and inspector walking the corridor (Apr 15)",
    "Does this corroborate the maintenance log findings? What's the field assessment?"
)
print("AGENT REASONING:")
print(reasoning)
'''

PHOTOS_CODE = '''# Notebook cell 19 — inspection photos with AI figure captions
display(Markdown("### CU Extraction: Figures with AI-Generated Captions"))
photos_result = analyze_document(photos)
show_extraction_summary(photos_result)

photos_md = photos_result.contents[0].markdown
print(photos_md[:1800])

print("\\n" + "─" * 60)
reasoning = agent_reason(
    to_llm_input(photos_result),
    "Inspection Photos (May 2) — 6 GPS-tagged field photos with AI captions",
    "Does visual evidence confirm the text-based findings? Is damage progressing?"
)
print("AGENT REASONING:")
print(reasoning)
'''


# ---------------------------------------------------------------------------
# Cached outputs — captured directly from notebook .ipynb cell 16 + 19 stdout
# ---------------------------------------------------------------------------

AUDIO_CACHED = """**CU extracted:** **36 paragraphs**

# FIELD AUDIO TRANSCRIPT Zava Telecom -- Field Operations

Site B | Segment 9 | Date: 2026-04-15 | Duration: 47:22

Personnel: P. Sharma (Field Tech), J. Alvarez (Inspector)


## TRANSCRIPT EXCERPT (12:30 - 18:45)

[12:30] SHARMA: Approaching vault TV-3. Visual on the conduit entry.

[12:42] SHARMA: Yeah, I can see the crack. It's worse than January (INC-2025-1187) .

[12:55] ALVAREZ: Photographing now. The displacement is about 3 centimeters.

[13:10] SHARMA: The protective sleeve is completely off. That's your micro-bend.

[13:25] ALVAREZ: Confirmed. This matches the OTDR anomaly at 847 meters.

[14:02] SHARMA: Moving to splice enclosure. SE-24F housing looks intact.

[14:15] SHARMA: No moisture inside. Seals are good.

[14:30] ALVAREZ: I'm checking the barrier. It's shifted about 15 centimeters.

[15:00] SHARMA: The ground heave is getting worse. This whole section needs--

[15:05] SHARMA: --needs a full conduit replacement. Patching won't hold. Route 2 shares this conduit.

[15:20] ALVAREZ: Agreed. I'll flag it in my report for engineering review.

[16:00] SHARMA: Strand check on 5 and 7. Still showing elevated loss.

[16:15] SHARMA: Not a splice issue. It's the conduit applyin

────────────────────────────────────────────────────────────
AGENT REASONING:
- The transcript confirms the maintenance log findings: the conduit crack at vault TV-3 has worsened since January, with a 3 cm displacement and the protective sleeve fully off, matching prior documented degradation.
- Field assessment identifies the root cause of signal loss on strands 5 and 7 as conduit pressure, not splice faults, directly corroborating maintenance log diagnostics.
- OTDR anomaly at 847 meters is physically verified in the field, strengthening the log's technical evidence.
- Both personnel recommend full conduit replacement, stating patching is insufficient—this aligns with maintenance log recommendations for major remediation.
- The transcript notes 42 customers are exposed with no backup, consistent with log risk assessments, and confirms engineering routing analysis completion.

**Conclusion:** The field audio transcript fully corroborates maintenance log findings and supports urgent conduit replacement at Site B, Segment 9.
"""

PHOTOS_CACHED = """**CU extracted:** **6 figure(s)** • **32 paragraphs**

# SITE INSPECTION -- PHOTO DOCUMENTATION Zava Telecom -- Field Operations

DOC-PHOTO-2026-05-02-TR9

Inspector: J. Alvarez | Date: 2026-05-02 | Site B, Segment 9


PHOTO 1: Vault TV-3 Interior

Conduit crack visible at 12 o'clock.
Water intrusion. Ref: FSE-2026-0041 SM-11.

![2026-05-02 11:00 GPS:34.0538](figures/1.1 "Circular vault interior with a gray circular ring near the center.
Multiple scattered circular spots of varying sizes in shades of brown and gray around and inside the ring.
A vertical crack or line at the top center (12 o'clock position) extending slightly inward from the ring.
A vertical wavy blue line inside the ring, slightly right of center.
Bottom left corner contains a black rectangular label with yellow text: "2026-05-02 11:00 GPS:34.0538".")


PHOTO 2: Cable Stress Point

![SLEEVE 2026-05-02 11:15 GPS:34.0538](figures/1.2 "Image of a cable with multiple colored strands extending from a dark circular conduit on the left.
Yellow rectangular box labeled 'SLEEVE' around a section of the cable near the conduit entry.
Red arrow pointing rightward along the cable strands within the yellow box.
Text in bottom left corner: '2026-05-02 11:15 GPS:34.0538'.
Background is dark gray.
No numeric scales or units visible on the image.")

Micro-bend at conduit entry.

Sleeve displaced 8cm. Micro-bend source.


PHOTO 3: Splice Enclosure
SE-24F housing intact.
No moisture detected.

![SE-24F SPLICE ENCL OK OK OK OK 2026-05-02 12:30 GPS:34.0542](figures/1.3 "Gray rectangular splice enclosure with label \"SE-24F SPLICE ENCL\" on upper section.
Four green hexagonal indicators below label, each labeled \"OK\".
Black screws at corners of enclosure.
Three black circular connectors at bottom of enclosure.
Timestamp and GPS coordinates in black box with yellow text: \"2026-05-02 

────────────────────────────────────────────────────────────
AGENT REASONING:
- Visual evidence in Photo 1 confirms a conduit crack with water intrusion at Vault TV-3, matching text-based findings and referencing FSE-2026-0041 SM-11.
- Photo 2 shows cable stress with an 8cm sleeve displacement and a visible micro-bend at the conduit entry, directly supporting the reported cable stress point.
- Photo 4 documents a 3cm pavement heave above the shared conduit (Rt1+Rt2), indicating surface damage and potential progression, as the offset is specifically measured.
- Photo 5 reveals a Jersey barrier displaced by 15cm since the last survey, suggesting worsening ground movement near the conduit.
- Photo 6 confirms ground erosion at Pole TR-38 base but notes guy wire tension remains OK, aligning with text descriptions.

Conclusion: The inspection photos provide clear visual confirmation of the text-based findings, with evidence of progressing damage (e.g., sleeve displacement, pavement heave, barrier shift) affecting the shared conduit and 42 customers at risk.
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


def _output_tabs(photos_text, audio_text):
    return [
        html.Div("Output", className="demo-panel-header"),
        dmc.Tabs(
            value="photos",
            children=[
                dmc.TabsList([
                    dmc.TabsTab("Photos + Reasoning", value="photos"),
                    dmc.TabsTab("Audio + Reasoning", value="audio"),
                ]),
                dmc.TabsPanel(html.Pre(photos_text, style=PRE_STYLE), value="photos", pt="md"),
                dmc.TabsPanel(html.Pre(audio_text, style=PRE_STYLE), value="audio", pt="md"),
            ],
        ),
    ]


def act2_layout():
    live_available = is_configured()

    return html.Div([
        html.Div(
            style={
                "display": "flex", "justifyContent": "space-between", "alignItems": "center",
                "padding": "16px 24px 0 24px",
            },
            children=[
                dmc.Group([
                    dmc.Badge("Act 2", color="violet", variant="filled", size="lg"),
                    dmc.Title("Show Me the Evidence — Multi-Modal Extraction", order=4, c="white"),
                ]),
                dmc.Group([
                    dmc.Badge("READY", color="gray", variant="light", size="sm", id="act2-mode-badge"),
                    dmc.Button("\u25B6 Run Live", id="act2-run-btn", variant="light", size="xs",
                               color="green", disabled=not live_available),
                    dmc.Button("\U0001F4E6 Pre-processed", id="act2-cached-btn", variant="light",
                               size="xs", color="blue"),
                ]),
            ],
        ),

        html.Div(
            className="demo-page",
            style={"height": "calc(100vh - 60px)", "paddingTop": "12px"},
            children=[
                # Left: Document tabs (photos + audio)
                html.Div(className="demo-panel", children=[
                    html.Div("\U0001F4F7 Documents", className="demo-panel-header"),
                    dmc.Tabs(
                        value="photos",
                        children=[
                            dmc.TabsList([
                                dmc.TabsTab("Inspection Photos", value="photos"),
                                dmc.TabsTab("Audio Transcript", value="audio"),
                            ]),
                            dmc.TabsPanel(
                                html.Img(
                                    src="/static/docs/inspection_photos.png",
                                    style={"width": "100%", "borderRadius": "8px"},
                                ),
                                value="photos", pt="md",
                            ),
                            dmc.TabsPanel(
                                html.Img(
                                    src="/static/docs/audio_transcript.png",
                                    style={"width": "100%", "borderRadius": "8px"},
                                ),
                                value="audio", pt="md",
                            ),
                        ],
                    ),
                ]),

                # Center: Code
                html.Div(className="demo-panel", children=[
                    html.Div("Code", className="demo-panel-header"),
                    dmc.Tabs(
                        value="photos",
                        children=[
                            dmc.TabsList([
                                dmc.TabsTab("Photos", value="photos"),
                                dmc.TabsTab("Audio Transcript", value="audio"),
                            ]),
                            dmc.TabsPanel(
                                dmc.CodeHighlight(code=PHOTOS_CODE, language="python",
                                                  withCopyButton=False,
                                                  style={"fontSize": "0.74rem"}),
                                value="photos", pt="md",
                            ),
                            dmc.TabsPanel(
                                dmc.CodeHighlight(code=AUDIO_CODE, language="python",
                                                  withCopyButton=False,
                                                  style={"fontSize": "0.74rem"}),
                                value="audio", pt="md",
                            ),
                        ],
                    ),
                ]),

                # Right: Output
                html.Div(className="demo-panel", id="act2-output-panel", children=_empty_output()),
            ],
        ),

        html.Div("\u2190 \u2192 to navigate", className="nav-hint"),
    ])


# ---------------------------------------------------------------------------
# Live runner — mirrors notebook cells 16 (audio) and 19 (photos)
# ---------------------------------------------------------------------------


def _extract_and_reason(pdf_path: Path, preview_chars: int, doc_description: str, question: str) -> str:
    """Run CU + agent_reason for one document, formatted like the notebook output."""
    from azure.ai.contentunderstanding import to_llm_input

    result = analyze_document(pdf_path, analyzer_id="prebuilt-documentSearch")
    if not result or not result.contents:
        return "\u26A0\uFE0F CU returned empty result"
    md = result.contents[0].markdown or ""

    lines = [extraction_summary(result), "", md[:preview_chars]]
    lines.append("")
    lines.append("─" * 60)
    try:
        reasoning = agent_reason(to_llm_input(result), doc_description, question)
    except Exception as e:  # pragma: no cover
        reasoning = f"(agent reasoning failed: {e})"
    lines.append("AGENT REASONING:")
    lines.append(reasoning)
    return "\n".join(lines)


@callback(
    Output("act2-output-panel", "children"),
    Output("act2-mode-badge", "children"),
    Output("act2-mode-badge", "color"),
    Input("act2-run-btn", "n_clicks"),
    Input("act2-cached-btn", "n_clicks"),
    prevent_initial_call=True,
)
def run_act2(run_clicks, cached_clicks):
    triggered = ctx.triggered_id

    if triggered == "act2-cached-btn":
        return _output_tabs(PHOTOS_CACHED, AUDIO_CACHED), "PRE-PROCESSED", "blue"

    if triggered == "act2-run-btn":
        try:
            photos_text = _extract_and_reason(
                PHOTOS_PDF,
                preview_chars=1800,
                doc_description="Inspection Photos (May 2) — 6 GPS-tagged field photos with AI captions",
                question="Does visual evidence confirm the text-based findings? Is damage progressing?",
            )
        except Exception as e:
            photos_text = f"⚠️ Photos error: {type(e).__name__}: {e}"

        try:
            audio_text = _extract_and_reason(
                AUDIO_PDF,
                preview_chars=1200,
                doc_description="Field Audio Transcript — technician and inspector walking the corridor (Apr 15)",
                question="Does this corroborate the maintenance log findings? What's the field assessment?",
            )
        except Exception as e:
            audio_text = f"⚠️ Audio error: {type(e).__name__}: {e}"

        return _output_tabs(photos_text, audio_text), "LIVE", "green"

    return no_update, no_update, no_update
