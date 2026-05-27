"""Output panel component — displays extraction/reasoning results."""

from dash import html
import dash_mantine_components as dmc


def create_output_panel(content: str, title: str = "Output", is_cached: bool = True, format: str = "text"):
    """Create a panel showing command output or extraction results."""
    badge = html.Span(
        "CACHED" if is_cached else "LIVE",
        className="badge-cached" if is_cached else "badge-live",
    )

    header = html.Div(
        style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "12px"},
        children=[
            html.Div(title, className="demo-panel-header", style={"marginBottom": "0"}),
            badge,
        ],
    )

    if format == "markdown":
        body = dmc.TypographyStylesProvider(
            children=html.Div(
                dangerouslySetInnerHTML={"__html": _md_to_html(content)},
                style={"fontSize": "0.82rem", "lineHeight": "1.6"},
            ),
        )
    else:
        body = html.Pre(
            content,
            style={
                "fontFamily": "var(--mono)",
                "fontSize": "0.78rem",
                "lineHeight": "1.6",
                "whiteSpace": "pre-wrap",
                "wordBreak": "break-word",
            },
        )

    return html.Div(
        className="demo-panel",
        children=[header, html.Div(body, className="output-block")],
    )


def _md_to_html(md_text: str) -> str:
    """Simple markdown to HTML (basic formatting only)."""
    import re
    text = md_text
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'^### (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.+)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
    text = re.sub(r'^- (.+)$', r'<li>\1</li>', text, flags=re.MULTILINE)
    text = text.replace('\n\n', '</p><p>').replace('\n', '<br>')
    return f'<p>{text}</p>'
