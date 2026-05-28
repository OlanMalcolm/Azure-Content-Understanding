# DEM331 Demo App — Hybrid Presentation

A Dash application that combines the HTML slide deck with interactive "live code" pages for the DEM331 Build 2026 session: **Fiber Cut Incident Response with Azure Content Understanding + Agents**.

## Quick Start

```bash
cd demo-app
uv run python app.py
```

Then open **http://localhost:8050** in your browser. Press **F11** for fullscreen presentation mode.

## Navigation

| Key | Action |
|-----|--------|
| `→` / `Space` / `PageDown` | Next frame |
| `←` / `PageUp` | Previous frame |
| `Home` | First frame |
| `End` | Last frame |

The presentation is a **linear sequence of 27 frames**: 22 HTML slides interleaved with 5 interactive Dash pages (one per act).

## Architecture

```
Slides 0–6 → [Act 1 Live Code] → Slides 7–8 → [Act 2 Live Code]
→ Slides 9–14 → [Act 3 Live Code] → Slides 15–17 → [Act 4 Live Code]
→ Slides 18–20 → [Act 5 Live Code] → Slide 21
```

Each live code page shows:
- **Left panel**: Document being analyzed (description + metadata)
- **Center panel**: Python code with syntax highlighting (tabbed)
- **Right panel**: Output / extraction results (pre-cached)

## Live Execution

By default, all results are pre-cached for offline use. To run live:

1. Create a `.env` file:
   ```
   CONTENTUNDERSTANDING_ENDPOINT=https://your-endpoint.services.ai.azure.com/
   CONTENTUNDERSTANDING_KEY=your-api-key
   ```
2. Click the **"▶ Run Live"** button on any page

> **Act 3 only:** the classifier and 6 custom analyzers must exist on the configured endpoint. Run the one-shot deploy script once after pointing `.env` at a new endpoint:
>
> ```powershell
> .\.venv\Scripts\python.exe scripts\deploy_analyzers.py
> ```
>
> Re-running is safe (every analyzer is created with `allow_replace=True`).

## File Structure

```
demo-app/
├── app.py                  # Main entry point + navigation sequence
├── pyproject.toml          # uv project config
├── assets/
│   ├── style.css           # Dark presentation theme
│   └── keyboard.js         # Arrow key navigation
├── components/             # Reusable UI components
│   ├── slide_frame.py      # Iframe wrapper for HTML slides
│   ├── code_panel.py       # Syntax-highlighted code display
│   ├── doc_viewer.py       # Document preview panel
│   └── output_panel.py     # Result display with cached/live badge
├── pages/                  # Interactive demo pages
│   ├── act1_extraction.py  # CU vs PyMuPDF comparison
│   ├── act2_visual.py      # Multi-modal evidence extraction
│   ├── act3_custom.py      # Custom analyzers + classification
│   ├── act4_synthesis.py   # 9-doc synthesis → dispatch email
│   └── act5_framework.py   # Agent Framework integration
├── services/
│   ├── cu_client.py        # Azure CU wrapper (live execution)
│   └── cache.py            # Cache loader/saver
├── cached_results/         # Pre-computed outputs (add JSON files here)
└── static/
    └── deck.html           # Modified HTML slide deck (iframe-ready)
```

## Tech Stack

- **Python 3.12+** (managed with `uv`)
- **Dash 4.x** + **dash-mantine-components**
- **Azure Content Understanding SDK** (optional, for live execution)
- The HTML slide deck runs in an iframe with postMessage communication
