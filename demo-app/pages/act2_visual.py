"""Act 2 — Visual & Audio Evidence Extraction.

Shows inspection photos and audio transcript processing with CU figure
captions and agent reasoning across multi-modal evidence.
Output starts empty — user clicks Run Live or Post-processed.
"""

from pathlib import Path

from dash import html, callback, Input, Output, ctx, no_update
import dash_mantine_components as dmc

from components.doc_viewer import create_doc_viewer
from services.cu_client import is_configured

SAMPLE_AUDIO = Path(__file__).parent.parent.parent / "src" / "sample-data" / "documents" / "cl_v3_site_b_audio_transcript_2026_04_15.pdf"
SAMPLE_PHOTOS = Path(__file__).parent.parent.parent / "src" / "sample-data" / "documents" / "cl_v3_inspection_photos_2026_05_02.pdf"

# Code exactly as in the notebook
PHOTOS_CODE = '''# THE DOCUMENT — 6 embedded field photos with GPS stamps
photos = DOCS_DIR / "cl_v3_inspection_photos_2026_05_02.pdf"

# CU generates figure descriptions — the agent can "see" through text
photos_result = analyze_document(photos)
show_extraction_summary(photos_result)

photos_md = photos_result.contents[0].markdown
print(photos_md[:1800])

reasoning = agent_reason(
    to_llm_input(photos_result),
    "Inspection Photos (May 2) — 6 GPS-tagged field photos with AI captions",
    "Does visual evidence confirm the text-based findings? Is damage progressing?"
)
print("AGENT REASONING:")
print(reasoning)
'''

AUDIO_CODE = '''# Audio transcript — conversational content
audio_transcript = DOCS_DIR / "cl_v3_site_b_audio_transcript_2026_04_15.pdf"

audio_result = analyze_document(audio_transcript)
show_extraction_summary(audio_result)

audio_md = audio_result.contents[0].markdown
print(audio_md[:1200])

reasoning = agent_reason(
    to_llm_input(audio_result),
    "Field Audio Transcript — technician and inspector walking the corridor (Apr 15)",
    "Does this corroborate the maintenance log findings? What's the field assessment?"
)
print("AGENT REASONING:")
print(reasoning)
'''

# Post-processed outputs (from notebook run)
PHOTOS_OUTPUT = """### CU Extraction: 6 Figures with AI Captions

**Figure 1:** Exterior view of underground vault TV-3 showing surface-level
concrete crack running NE-SW, approximately 18 inches long. GPS: 38.9201, -77.0152

**Figure 2:** Close-up of conduit entry point with visible water staining
and mineral deposits indicating chronic moisture intrusion. Cable bundle visible.

**Figure 3:** Interior splice tray showing fiber strand displacement.
Strands 4 and 7 show visible micro-bend at support bracket contact point.

**Figure 4:** OTDR trace screenshot showing elevated loss at 847m mark
(0.82 dB splice loss vs 0.15 dB baseline). Annotated by technician.

**Figure 5:** Thermal image of vault showing heat differential at conduit
penetration — 4.2°C above ambient, indicating active water flow path.

**Figure 6:** Repaired section from January emergency splice (reference photo).
Visible re-entry marks on cable sheath. Original repair by TC-Bravo.

---
**CU extracted:** **6 figure(s)** • **8 paragraphs** • GPS coordinates preserved
"""

REASONING_OUTPUT = """### Agent Reasoning: Multi-Modal Corroboration

• **Visual evidence (photos):** Crack at vault TV-3, water intrusion confirmed,
  strand displacement at bracket contact points (strands 4 & 7)

• **Audio evidence (transcript):** Tech Martinez states "it's worse than January"
  — references prior emergency repair. Inspector Okonkwo notes "shared conduit
  means if primary goes, backup goes with it"

• **Correlation:** Both sources point to vault TV-3, segment 9 at ~847m mark.
  The crack is propagating (18" now vs 6" in January photo).

• **Escalation trigger:** Inspector explicitly says "no redundancy path" —
  matches the incident alert's severity assessment.

• **Timeline:** Deterioration accelerated between April 8 repair and May 2
  inspection (24 days). Rate suggests full failure within 2-3 weeks.

**Conclusion:** Vault TV-3 shared conduit failure is confirmed by photo, audio,
and OTDR evidence. Immediate full replacement required — repair-in-place will not
hold given the structural crack progression.
"""


def _empty_output():
    """Initial empty state."""
    return [
        html.Div("Output", className="demo-panel-header"),
        dmc.Center(
            dmc.Text("Press  ▶ Run Live  or  📦 Post-processed  to execute", c="dimmed", size="sm"),
            style={"height": "100%", "flex": "1"},
        ),
    ]


def _output_tabs(photos_text, reasoning_text):
    """Build output tabs."""
    return [
        html.Div("Output", className="demo-panel-header"),
        dmc.Tabs(
            value="photos",
            children=[
                dmc.TabsList([
                    dmc.TabsTab("Figure Captions", value="photos"),
                    dmc.TabsTab("Agent Reasoning", value="reasoning"),
                ]),
                dmc.TabsPanel(
                    html.Pre(photos_text, style={"fontFamily": "var(--mono)", "fontSize": "0.72rem",
                                                 "lineHeight": "1.5", "whiteSpace": "pre-wrap"}),
                    value="photos", pt="md",
                ),
                dmc.TabsPanel(
                    html.Pre(reasoning_text, style={"fontFamily": "var(--mono)", "fontSize": "0.72rem",
                                                    "lineHeight": "1.5", "whiteSpace": "pre-wrap"}),
                    value="reasoning", pt="md",
                ),
            ],
        ),
    ]


def act2_layout():
    """Build the Act 2 live demo page layout."""
    live_available = is_configured()

    return html.Div([
        html.Div(
            style={"display": "flex", "justifyContent": "space-between", "alignItems": "center",
                   "padding": "16px 24px 0 24px"},
            children=[
                dmc.Group([
                    dmc.Badge("Act 2", color="violet", variant="filled", size="lg"),
                    dmc.Title("Show Me the Evidence — Multi-Modal Extraction", order=4, c="white"),
                ]),
                dmc.Group([
                    dmc.Badge("READY", color="gray", variant="light", size="sm", id="act2-mode-badge"),
                    dmc.Button("▶ Run Live", id="act2-run-btn", variant="light", size="xs",
                               color="green", disabled=not live_available),
                    dmc.Button("📦 Post-processed", id="act2-cached-btn", variant="light", size="xs", color="blue"),
                ]),
            ],
        ),

        html.Div(
            className="demo-page",
            style={"height": "calc(100vh - 60px)", "paddingTop": "12px"},
            children=[
                # Left: Document images
                html.Div(className="demo-panel", children=[
                    html.Div("📷 Documents", className="demo-panel-header"),
                    dmc.Tabs(
                        value="photos",
                        children=[
                            dmc.TabsList([
                                dmc.TabsTab("Inspection Photos", value="photos"),
                                dmc.TabsTab("Audio Transcript", value="audio"),
                            ]),
                            dmc.TabsPanel(
                                html.Img(src="/static/docs/inspection_photos.png",
                                         style={"width": "100%", "borderRadius": "8px"}),
                                value="photos", pt="md",
                            ),
                            dmc.TabsPanel(
                                html.Img(src="/static/docs/audio_transcript.png",
                                         style={"width": "100%", "borderRadius": "8px"}),
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
                                dmc.CodeHighlight(code=PHOTOS_CODE, language="python", withCopyButton=False,
                                                  style={"fontSize": "0.76rem"}),
                                value="photos", pt="md",
                            ),
                            dmc.TabsPanel(
                                dmc.CodeHighlight(code=AUDIO_CODE, language="python", withCopyButton=False,
                                                  style={"fontSize": "0.76rem"}),
                                value="audio", pt="md",
                            ),
                        ],
                    ),
                ]),

                # Right: Output (starts empty)
                html.Div(className="demo-panel", id="act2-output-panel", children=_empty_output()),
            ],
        ),

        html.Div("← → to navigate", className="nav-hint"),
    ])


@callback(
    Output("act2-output-panel", "children"),
    Output("act2-mode-badge", "children"),
    Output("act2-mode-badge", "color"),
    Input("act2-run-btn", "n_clicks"),
    Input("act2-cached-btn", "n_clicks"),
    prevent_initial_call=True,
)
def run_act2(run_clicks, cached_clicks):
    """Execute live or show post-processed results."""
    triggered = ctx.triggered_id

    if triggered == "act2-cached-btn":
        return _output_tabs(PHOTOS_OUTPUT, REASONING_OUTPUT), "POST-PROCESSED", "blue"

    if triggered == "act2-run-btn":
        import os
        from dotenv import load_dotenv
        from azure.ai.contentunderstanding import ContentUnderstandingClient, to_llm_input
        from azure.core.credentials import AzureKeyCredential
        from openai import AzureOpenAI

        load_dotenv(override=True)
        endpoint = os.environ.get("CONTENTUNDERSTANDING_ENDPOINT", "")
        key = os.getenv("CONTENTUNDERSTANDING_KEY")

        if not endpoint:
            return _output_tabs("⚠️ CONTENTUNDERSTANDING_ENDPOINT not set", ""), "ERROR", "red"

        credential = AzureKeyCredential(key) if key else None
        client = ContentUnderstandingClient(endpoint=endpoint, credential=credential,
                                            user_agent="build26-DEM331-demo/1.0.0")
        agent_client = AzureOpenAI(azure_endpoint=endpoint, api_key=key, api_version="2025-04-01-preview")

        # Analyze photos — use prebuilt-documentSearch for AI figure captions
        photos_text = ""
        try:
            with open(SAMPLE_PHOTOS, "rb") as f:
                poller = client.begin_analyze_binary(analyzer_id="prebuilt-documentSearch", binary_input=f.read())
            photos_result = poller.result()
            if photos_result.contents:
                content = photos_result.contents[0]
                # Show extraction summary like the notebook does
                parts = []
                if content.figures:
                    parts.append(f"**{len(content.figures)} figure(s)**")
                if content.paragraphs:
                    parts.append(f"**{len(content.paragraphs)} paragraphs**")
                summary = "CU extracted: " + " • ".join(parts) + "\n\n" if parts else ""
                photos_text = summary + content.markdown
            else:
                # Fallback to prebuilt-layout if documentSearch returns empty
                with open(SAMPLE_PHOTOS, "rb") as f:
                    poller = client.begin_analyze_binary(analyzer_id="prebuilt-layout", binary_input=f.read())
                photos_result = poller.result()
                if photos_result.contents:
                    photos_text = "(fallback: prebuilt-layout)\n\n" + photos_result.contents[0].markdown
                else:
                    photos_text = "⚠️ CU returned empty result for photos"
        except Exception as e:
            photos_text = f"⚠️ Error: {e}"

        # Analyze audio + agent reasoning — use prebuilt-documentSearch
        reasoning_text = ""
        try:
            with open(SAMPLE_AUDIO, "rb") as f:
                poller = client.begin_analyze_binary(analyzer_id="prebuilt-documentSearch", binary_input=f.read())
            audio_result = poller.result()
            if not audio_result.contents:
                # Fallback
                with open(SAMPLE_AUDIO, "rb") as f:
                    poller = client.begin_analyze_binary(analyzer_id="prebuilt-layout", binary_input=f.read())
                audio_result = poller.result()

            if audio_result.contents:
                audio_md = audio_result.contents[0].markdown
                # Agent reasoning
                response = agent_client.chat.completions.create(
                    model="gpt-4.1",
                    messages=[
                        {"role": "system", "content": (
                            "You are the Fiber Cut Response Agent for Zava Telecom. "
                            "You are analyzing documents related to incident INC-2026-0391. "
                            "Given CU extraction output, provide 3-5 bullet points of key reasoning. "
                            "End with a one-line conclusion."
                        )},
                        {"role": "user", "content": (
                            "Document: Field Audio Transcript + Inspection Photos\n"
                            "Question: Does evidence corroborate findings? Is damage progressing?\n\n"
                            f"CU Extraction:\n{audio_md}\n\n{photos_text}"
                        )},
                    ],
                    temperature=0.2,
                    max_tokens=400,
                )
                reasoning_text = f"Audio extraction:\n{audio_md}\n\n{'─'*40}\nAGENT REASONING:\n{response.choices[0].message.content}"
            else:
                reasoning_text = "⚠️ CU returned empty result for audio"
        except Exception as e:
            reasoning_text = f"⚠️ Error: {e}"

        return _output_tabs(photos_text, reasoning_text), "LIVE", "green"

    return no_update, no_update, no_update
