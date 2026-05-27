"""Slide iframe component for embedding the HTML deck."""

from dash import html


def create_slide_frame():
    """Create an iframe that loads the static HTML slide deck."""
    return html.Iframe(
        id="deck-iframe",
        src="/static/deck.html",
        style={
            "width": "100%",
            "height": "100%",
            "border": "none",
            "backgroundColor": "#0a0a0f",
        },
    )
