"""Document viewer component — shows PDF page images or document previews."""

from dash import html
import dash_mantine_components as dmc


def create_doc_viewer(image_src: str = None, title: str = "Document", description: str = ""):
    """Create a panel showing a document image or placeholder."""
    if image_src:
        content = html.Div(
            children=[
                html.Img(
                    src=image_src,
                    style={
                        "width": "100%",
                        "height": "auto",
                        "borderRadius": "8px",
                        "boxShadow": "0 4px 24px rgba(0,0,0,0.4)",
                    },
                ),
            ],
            style={"padding": "12px", "overflow": "auto", "height": "100%"},
        )
    else:
        content = dmc.Center(
            dmc.Stack([
                dmc.ThemeIcon(
                    size=60,
                    radius="xl",
                    variant="light",
                    children=html.Span("📄", style={"fontSize": "1.5rem"}),
                ),
                dmc.Text(description or "Document preview", c="dimmed", size="sm"),
            ], align="center", gap="sm"),
            style={"height": "100%"},
        )

    return html.Div(
        className="demo-panel",
        children=[
            html.Div(title, className="demo-panel-header"),
            html.Div(content, style={"flex": "1", "overflow": "auto"}),
        ],
    )
