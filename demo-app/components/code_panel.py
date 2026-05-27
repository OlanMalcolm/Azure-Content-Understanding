"""Code panel component — displays syntax-highlighted Python code."""

from dash import html
import dash_mantine_components as dmc


def create_code_panel(code: str, title: str = "Code", language: str = "python"):
    """Create a panel showing syntax-highlighted code."""
    return html.Div(
        className="demo-panel",
        children=[
            html.Div(title, className="demo-panel-header"),
            dmc.CodeHighlight(
                code=code,
                language=language,
                withCopyButton=False,
                style={
                    "flex": "1",
                    "overflow": "auto",
                    "borderRadius": "12px",
                    "fontSize": "0.78rem",
                },
            ),
        ],
    )
