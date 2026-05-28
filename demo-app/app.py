"""DEM331 Hybrid Presentation — Dash App Entry Point"""

import json
from pathlib import Path

import dash
from dash import html, dcc, callback, Input, Output, State, clientside_callback, no_update
import dash_mantine_components as dmc
from flask import send_from_directory

from components.slide_frame import create_slide_frame
from pages.act1_extraction import act1_layout
from pages.act2_visual import act2_layout
from pages.act3_custom import act3_layout
from pages.act4_synthesis import act4_layout
from pages.act5_framework import act5_layout

# Presentation sequence: list of frames
# Each frame is either ("slide", slide_index) or ("page", page_id)
# Slide indices map to the HTML deck's internal slide numbers (0-based)
SEQUENCE = []

# Slides 1–5 (deck indices 0–4)
for i in range(5):
    SEQUENCE.append(("slide", i))

# Act 1 live code page (before slide 6)
SEQUENCE.append(("page", "act1"))

# Slides 6–8 (deck indices 5–7)
for i in range(5, 8):
    SEQUENCE.append(("slide", i))

# Act 2 live code page (after slide 8)
SEQUENCE.append(("page", "act2"))

# Slides 9–11 (deck indices 8–10)
for i in range(8, 11):
    SEQUENCE.append(("slide", i))

# Act 3 live code page (after slide 11)
SEQUENCE.append(("page", "act3"))

# Slides 12–13 (deck indices 11–12)
for i in range(11, 13):
    SEQUENCE.append(("slide", i))

# Act 4 live code page (before slide 14, so the live run precedes the synthesis recap)
SEQUENCE.append(("page", "act4"))

# Slides 14, 16, 17 (deck indices 13–15) — synthesis+dispatch recap, then Act 5 intro & code
for i in range(13, 16):
    SEQUENCE.append(("slide", i))

# Act 5 live code page (after slide-label 17, the Act 5 code preview)
SEQUENCE.append(("page", "act5"))

# Slides 18–20 (deck indices 16–18)
for i in range(16, 19):
    SEQUENCE.append(("slide", i))

# JSON-serialize the sequence for the client
SEQUENCE_JSON = json.dumps([[s[0], s[1]] for s in SEQUENCE])

app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    title="DEM331 — Fiber Cut Response Demo",
    external_stylesheets=dmc.styles.ALL,
)
app._favicon = None

# Serve the static HTML deck
STATIC_DIR = Path(__file__).parent / "static"


@app.server.route("/static/<path:filename>")
def serve_static(filename):
    return send_from_directory(str(STATIC_DIR), filename)

# Page layouts
PAGE_LAYOUTS = {
    "act1": act1_layout,
    "act2": act2_layout,
    "act3": act3_layout,
    "act4": act4_layout,
    "act5": act5_layout,
}

app.layout = dmc.MantineProvider(
    id="mantine-provider",
    forceColorScheme="dark",
    children=[
        # Navigation state
        dcc.Store(id="frame-index", data=0, storage_type="session"),

        # Hidden element to capture keyboard events via n_events
        # This uses an EventListener approach: a div that captures key presses
        html.Div(
            id="nav-key-capture",
            children="",
            style={"position": "fixed", "top": 0, "left": 0, "width": "1px", "height": "1px", "opacity": 0, "pointerEvents": "none"},
        ),

        # Main content area
        html.Div(
            id="presentation-container",
            children=[
                # Slide iframe (shown/hidden)
                html.Div(
                    id="slide-container",
                    children=[create_slide_frame()],
                    style={"width": "100vw", "height": "100vh", "display": "block"},
                ),
                # Dash page container (shown/hidden)
                html.Div(
                    id="page-container",
                    style={"width": "100vw", "height": "100vh", "display": "none", "overflow": "auto"},
                ),
            ],
            style={"width": "100vw", "height": "100vh", "overflow": "hidden", "position": "relative"},
        ),

        # Progress indicator
        html.Div(
            id="progress-bar",
            style={
                "position": "fixed",
                "bottom": "0",
                "left": "0",
                "height": "3px",
                "backgroundColor": "#3b82f6",
                "transition": "width 0.3s ease",
                "zIndex": "9999",
            },
        ),

        # Navigation overlay buttons (invisible but clickable)
        html.Button(id="nav-prev", n_clicks=0, style={"display": "none"}),
        html.Button(id="nav-next", n_clicks=0, style={"display": "none"}),
    ],
)


@callback(
    Output("slide-container", "style"),
    Output("page-container", "style"),
    Output("page-container", "children"),
    Output("progress-bar", "style"),
    Input("frame-index", "data"),
)
def update_frame(frame_idx):
    """Switch between slide iframe and Dash page based on current frame."""
    if frame_idx is None or frame_idx < 0:
        frame_idx = 0
    if frame_idx >= len(SEQUENCE):
        frame_idx = len(SEQUENCE) - 1

    frame_type, frame_value = SEQUENCE[frame_idx]
    progress_pct = (frame_idx / max(len(SEQUENCE) - 1, 1)) * 100

    progress_style = {
        "position": "fixed",
        "bottom": "0",
        "left": "0",
        "height": "3px",
        "backgroundColor": "#3b82f6",
        "transition": "width 0.3s ease",
        "zIndex": "9999",
        "width": f"{progress_pct:.1f}%",
    }

    slide_style = {"width": "100vw", "height": "100vh", "display": "none"}
    page_style = {"width": "100vw", "height": "100vh", "display": "none", "overflow": "auto"}

    if frame_type == "slide":
        slide_style["display"] = "block"
        return slide_style, page_style, None, progress_style
    else:
        page_style["display"] = "block"
        layout_fn = PAGE_LAYOUTS.get(frame_value)
        children = layout_fn() if layout_fn else html.Div("Page not found")
        return slide_style, page_style, children, progress_style


# Navigate forward
clientside_callback(
    """
    function(n_clicks, frameIdx) {
        if (!n_clicks) return dash_clientside.no_update;
        const seq = window.__DEM331_SEQUENCE__;
        const newIdx = Math.min((frameIdx || 0) + 1, seq.length - 1);
        return newIdx;
    }
    """,
    Output("frame-index", "data", allow_duplicate=True),
    Input("nav-next", "n_clicks"),
    State("frame-index", "data"),
    prevent_initial_call=True,
)

# Navigate backward
clientside_callback(
    """
    function(n_clicks, frameIdx) {
        if (!n_clicks) return dash_clientside.no_update;
        const newIdx = Math.max((frameIdx || 0) - 1, 0);
        return newIdx;
    }
    """,
    Output("frame-index", "data", allow_duplicate=True),
    Input("nav-prev", "n_clicks"),
    State("frame-index", "data"),
    prevent_initial_call=True,
)

# Sync iframe when frame changes
clientside_callback(
    f"""
    function(frameIdx) {{
        const seq = window.__DEM331_SEQUENCE__;
        if (!seq) return dash_clientside.no_update;
        const frame = seq[frameIdx];
        if (frame && frame[0] === "slide") {{
            const iframe = document.getElementById("deck-iframe");
            if (iframe && iframe.contentWindow) {{
                iframe.contentWindow.postMessage({{type: "goToSlide", index: frame[1]}}, "*");
                iframe.contentWindow.postMessage({{type: "framePosition", index: frameIdx, total: seq.length}}, "*");
            }}
        }}
        return dash_clientside.no_update;
    }}
    """,
    Output("nav-key-capture", "children"),
    Input("frame-index", "data"),
)


# Inject sequence data into the page on load
app.index_string = '''<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
        <script>
            window.__DEM331_SEQUENCE__ = ''' + SEQUENCE_JSON + ''';
            window.__DEM331_SEQ_LENGTH__ = ''' + str(len(SEQUENCE)) + ''';

            // Global keyboard handler — clicks hidden nav buttons
            document.addEventListener("keydown", function(e) {
                // Don't capture if typing in an input
                if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA" || e.target.tagName === "SELECT") return;

                if (e.key === "ArrowRight" || e.key === " " || e.key === "PageDown") {
                    e.preventDefault();
                    e.stopPropagation();
                    var btn = document.getElementById("nav-next");
                    if (btn) btn.click();
                } else if (e.key === "ArrowLeft" || e.key === "PageUp") {
                    e.preventDefault();
                    e.stopPropagation();
                    var btn = document.getElementById("nav-prev");
                    if (btn) btn.click();
                }
            }, true);

            // Also capture keyboard from iframe via postMessage
            window.addEventListener("message", function(e) {
                if (e.data && e.data.type === "keyNav") {
                    if (e.data.direction === "next") {
                        var btn = document.getElementById("nav-next");
                        if (btn) btn.click();
                    } else if (e.data.direction === "prev") {
                        var btn = document.getElementById("nav-prev");
                        if (btn) btn.click();
                    }
                }
            });
        </script>
    </body>
</html>'''


server = app.server


def main():
    app.run(debug=True, host="0.0.0.0", port=8050)


if __name__ == "__main__":
    main()
