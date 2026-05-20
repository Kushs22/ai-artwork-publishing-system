"""Apply AI-detected metadata from content.json to catalogue records."""

import os
from typing import Any

from models import ArtworkMetadata, PLATFORM_OPTIONS

AUTO_PLATFORMS = list(PLATFORM_OPTIONS)


def metadata_from_ai(content: dict[str, Any], base: ArtworkMetadata) -> ArtworkMetadata:
    """Merge Gemini suggestions into artwork metadata."""
    title = (content.get("suggested_title") or content.get("gelato_product_title") or base.title or "").strip()
    theme = (content.get("suggested_theme") or base.theme or "").strip()
    collection = (content.get("suggested_collection") or base.collection or "").strip()
    fmt = (content.get("suggested_format") or base.format or "").strip()

    if not title and content.get("artwork_analysis"):
        title = content["artwork_analysis"][:60].strip()

    platforms = base.platforms if base.platforms else AUTO_PLATFORMS

    return ArtworkMetadata(
        title=title,
        theme=theme,
        collection=collection,
        format=fmt,
        platforms=platforms,
        website=base.website or "https://www.roxymegyesi.com/",
    )


def ensure_auto_platforms(meta: ArtworkMetadata) -> ArtworkMetadata:
    if not meta.platforms:
        meta.platforms = list(AUTO_PLATFORMS)
    if not meta.website:
        meta.website = "https://www.roxymegyesi.com/"
    return meta
