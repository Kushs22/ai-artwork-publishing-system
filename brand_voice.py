"""Load and merge Roxy / Bark & Grain brand voice for caption generation."""

import json
import os
from typing import Any, Optional

DEFAULT_PROFILE_PATH = os.path.join(
    os.path.dirname(__file__), "brand_profile", "roxy_bark_grain.json"
)
USER_OVERRIDES_PATH = os.path.join(
    os.path.dirname(__file__), "brand_profile", "user_examples.json"
)


def load_json(path: str) -> dict[str, Any]:
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_brand_profile(profile_path: Optional[str] = None) -> dict[str, Any]:
    path = profile_path or DEFAULT_PROFILE_PATH
    return load_json(path)


def load_user_examples() -> dict[str, Any]:
    return load_json(USER_OVERRIDES_PATH)


def save_user_examples(examples: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(USER_OVERRIDES_PATH), exist_ok=True)
    with open(USER_OVERRIDES_PATH, "w", encoding="utf-8") as f:
        json.dump(examples, f, indent=2, ensure_ascii=False)


def build_brand_context_block(
    profile: dict[str, Any],
    user_examples: Optional[dict[str, Any]] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> str:
    """Text block injected into the Gemini prompt."""
    user_examples = user_examples or {}
    meta = metadata or {}

    captions = list(profile.get("example_captions", []))
    captions.extend(user_examples.get("example_captions", []))
    hashtags = list(profile.get("example_hashtags", []))
    hashtags.extend(user_examples.get("example_hashtags", []))

    collection = meta.get("collection", "") or meta.get("theme", "")
    collection_note = ""
    collections = profile.get("collections", {})
    if collection and collection in collections:
        collection_note = collections[collection]
    elif collection:
        collection_note = f"Collection/theme: {collection}"

    lines = [
        f"Artist: {profile.get('artist_name', '')} — {profile.get('studio', '')}",
        f"Voice: {profile.get('voice_summary', '')}",
        f"Tone keywords: {', '.join(profile.get('tone_keywords', []))}",
        f"Avoid: {', '.join(profile.get('avoid_phrases', []))}",
    ]
    if collection_note:
        lines.append(f"Collection context: {collection_note}")

    if captions:
        lines.append("\nEXAMPLE CAPTIONS (match this style — do not copy verbatim):")
        for i, cap in enumerate(captions[:8], 1):
            lines.append(f"{i}. {cap}")

    if hashtags:
        lines.append("\nEXAMPLE HASHTAGS (similar mix and tone):")
        lines.append(" ".join(hashtags[:20]))

    platform_style = profile.get("platform_style", {})
    if platform_style:
        lines.append("\nPLATFORM-SPECIFIC STYLE:")
        for platform, rules in platform_style.items():
            lines.append(f"- {platform}: {json.dumps(rules)}")

    return "\n".join(lines)


def crops_for_platforms(platforms: list[str]) -> list[str]:
    """Map selected platforms to crop output names."""
    mapping = {
        "Instagram": ["instagram_square", "instagram_portrait"],
        "Pinterest": ["pinterest_vertical"],
        "Squarespace": ["website_thumbnail", "website_product"],
        "Gelato": ["gelato_print"],
        "Website": ["website_thumbnail", "website_product"],
    }
    names: list[str] = []
    for platform in platforms:
        for name in mapping.get(platform, []):
            if name not in names:
                names.append(name)
    return names
