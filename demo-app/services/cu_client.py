"""Azure Content Understanding client wrapper."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=True)


def get_cu_client():
    """Create a CU client if credentials are available."""
    endpoint = os.getenv("CONTENTUNDERSTANDING_ENDPOINT")
    key = os.getenv("CONTENTUNDERSTANDING_KEY")

    if not endpoint:
        return None

    from azure.ai.contentunderstanding import ContentUnderstandingClient
    from azure.core.credentials import AzureKeyCredential
    from azure.identity import DefaultAzureCredential

    credential = AzureKeyCredential(key) if key else DefaultAzureCredential()
    return ContentUnderstandingClient(
        endpoint=endpoint,
        credential=credential,
        user_agent="build26-DEM331-demo/1.0.0",
    )


def analyze_document(pdf_path: Path, analyzer_id: str = "prebuilt-layout"):
    """Analyze a document with CU. Returns the result or None."""
    client = get_cu_client()
    if not client:
        return None

    with open(pdf_path, "rb") as f:
        poller = client.begin_analyze_binary(
            analyzer_id=analyzer_id,
            binary_input=f.read(),
        )
    return poller.result()


def is_configured() -> bool:
    """Check if CU credentials are available."""
    return bool(os.getenv("CONTENTUNDERSTANDING_ENDPOINT"))
