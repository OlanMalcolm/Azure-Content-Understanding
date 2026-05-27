"""Cache loader — reads pre-computed results from cached_results/."""

import json
from pathlib import Path

CACHE_DIR = Path(__file__).parent.parent / "cached_results"


def load_cached(filename: str) -> dict | str | None:
    """Load a cached result file. Returns dict for .json, str for .txt/.md."""
    path = CACHE_DIR / filename
    if not path.exists():
        return None
    if path.suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    return path.read_text(encoding="utf-8")


def save_cached(filename: str, data):
    """Save result to cache."""
    CACHE_DIR.mkdir(exist_ok=True)
    path = CACHE_DIR / filename
    if isinstance(data, (dict, list)):
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    else:
        path.write_text(str(data), encoding="utf-8")


def has_cached(filename: str) -> bool:
    """Check if a cached result exists."""
    return (CACHE_DIR / filename).exists()
