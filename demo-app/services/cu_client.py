"""Azure Content Understanding + Azure OpenAI client wrappers.

Mirror the helper functions from the notebook (`src/demo_fiber_cut_MAF.ipynb` cell 5)
so the demo-app callbacks can invoke the same logic the notebook does.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Always honor .env values over any inherited shell env vars (the notebook does this).
load_dotenv(override=True)

CU_API_VERSION = "2025-11-01"
CU_COMPLETION_ALIAS = "prebuilt-analyzer-completion"
CU_COMPLETION_MINI_ALIAS = "prebuilt-analyzer-completion-mini"
CU_EMBEDDING_ALIAS = "prebuilt-analyzer-embedding"
AGENT_MODEL = os.getenv("AGENT_MODEL", "gpt-5.2")
DEFAULT_ANALYZER = "prebuilt-documentSearch"
CLASSIFIER_ID = "fiberFieldDocClassifier"


def _endpoint() -> Optional[str]:
    return os.environ.get("CONTENTUNDERSTANDING_ENDPOINT") or None


def _key() -> Optional[str]:
    return os.getenv("CONTENTUNDERSTANDING_KEY") or None


def is_configured() -> bool:
    """True if a CU endpoint is configured."""
    return bool(_endpoint())


def model_deployments() -> dict[str, str]:
    """Return CU model aliases mapped to the deployment names on the endpoint."""
    completion_model = os.getenv("CONTENTUNDERSTANDING_COMPLETION_MODEL", "gpt-5.2")
    completion_deployment = os.getenv(
        "CONTENTUNDERSTANDING_COMPLETION_DEPLOYMENT", completion_model
    )
    embedding_deployment = os.getenv(
        "CONTENTUNDERSTANDING_EMBEDDING_DEPLOYMENT", "text-embedding-3-large"
    )
    return {
        completion_model: completion_deployment,
        CU_COMPLETION_ALIAS: completion_deployment,
        CU_COMPLETION_MINI_ALIAS: completion_deployment,
        "text-embedding-3-large": embedding_deployment,
        CU_EMBEDDING_ALIAS: embedding_deployment,
    }


def configure_model_defaults() -> dict:
    """Configure the resource-level CU model defaults and return the response."""
    endpoint = _endpoint()
    if not endpoint:
        raise RuntimeError("CONTENTUNDERSTANDING_ENDPOINT is not configured")

    import requests

    headers = {"Content-Type": "application/json"}
    key = _key()
    if key:
        headers["Ocp-Apim-Subscription-Key"] = key
    else:
        from azure.identity import DefaultAzureCredential

        token = DefaultAzureCredential().get_token(
            "https://cognitiveservices.azure.com/.default"
        )
        headers["Authorization"] = f"Bearer {token.token}"

    response = requests.patch(
        f"{endpoint.rstrip('/')}/contentunderstanding/defaults",
        params={"api-version": CU_API_VERSION},
        headers=headers,
        json={"modelDeployments": model_deployments()},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def get_cu_client():
    """Create a Content Understanding client (matches notebook cell 4)."""
    endpoint = _endpoint()
    if not endpoint:
        return None
    from azure.ai.contentunderstanding import ContentUnderstandingClient
    from azure.core.credentials import AzureKeyCredential

    key = _key()
    if key:
        credential = AzureKeyCredential(key)
    else:
        from azure.identity import DefaultAzureCredential
        credential = DefaultAzureCredential()
    return ContentUnderstandingClient(
        endpoint=endpoint,
        credential=credential,
        user_agent="build26-DEM331-demo/1.0.0",
    )


def get_agent_client():
    """Create the Azure OpenAI agent client (matches notebook cell 5)."""
    endpoint = _endpoint()
    if not endpoint:
        return None
    from openai import AzureOpenAI

    return AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=_key(),
        api_version="2025-04-01-preview",
    )


def analyze_document(pdf_path: Path, analyzer_id: str = DEFAULT_ANALYZER):
    """Analyze a document with CU. Mirrors notebook `analyze_document`."""
    client = get_cu_client()
    if not client:
        return None
    with open(pdf_path, "rb") as f:
        poller = client.begin_analyze_binary(
            analyzer_id=analyzer_id,
            binary_input=f.read(),
        )
    return poller.result()


def extraction_summary(result) -> str:
    """Build the same summary string the notebook prints (cell 5 `show_extraction_summary`)."""
    if not result or not result.contents:
        return "**CU extracted:** (no contents)"
    content = result.contents[0]
    parts: list[str] = []
    if content.tables:
        parts.append(f"**{len(content.tables)} table(s)**")
    if content.figures:
        parts.append(f"**{len(content.figures)} figure(s)**")
    if content.paragraphs:
        parts.append(f"**{len(content.paragraphs)} paragraphs**")
    if content.pages:
        barcode_total = sum(len(p.barcodes) for p in content.pages if p.barcodes)
        if barcode_total:
            parts.append(f"**{barcode_total} barcode/QR**")
    md = content.markdown or ""
    checked = md.count("\u2612")
    unchecked = md.count("\u2610")
    if checked + unchecked > 0:
        parts.append(f"**{checked}\u2612 {unchecked}\u2610 selection marks**")
    return "**CU extracted:** " + " \u2022 ".join(parts) if parts else "**CU extracted:** (empty)"


def agent_reason(extraction_text: str, doc_description: str, question: str) -> str:
    """Send a CU extraction to the agent and return reasoning text.

    Mirrors notebook cell 5 `agent_reason` exactly (same prompt, temperature, max_completion_tokens).
    """
    client = get_agent_client()
    if not client:
        return "(agent client not configured)"
    response = client.chat.completions.create(
        model=AGENT_MODEL,
        messages=[
            {"role": "system", "content": (
                "You are the Fiber Cut Response Agent for Zava Telecom. "
                "You are analyzing documents related to incident INC-2026-0391 (signal degradation, "
                "Tower Ridge Corridor, Site B, Segment 9, 42 customers at risk). "
                "Given CU extraction output from a document, provide 3-5 bullet points of key reasoning. "
                "End with a one-line conclusion. Be concise and specific — cite values from the data."
            )},
            {"role": "user", "content": (
                f"Document: {doc_description}\n"
                f"Question: {question}\n\n"
                f"CU Extraction:\n{extraction_text}"
            )},
        ],
        temperature=0.2,
        max_completion_tokens=400,
    )
    return response.choices[0].message.content
