"""Batch processing for multiple artworks."""

from typing import Any, Optional

from db import get_artwork, list_artworks, update_artwork
from metadata_utils import ensure_auto_platforms, metadata_from_ai
from models import ArtworkMetadata, ArtworkStatus
from publishing_agent import PublishingAgent
from approval import submit_for_review


def process_artwork(
    artwork_id: int,
    api_key: Optional[str],
    *,
    include_crops: bool = True,
    metadata_override: Optional[ArtworkMetadata] = None,
) -> dict[str, Any]:
    artwork = get_artwork(artwork_id)
    if not artwork:
        return {"ok": False, "error": "Artwork not found", "artwork_id": artwork_id}

    meta = ensure_auto_platforms(metadata_override or artwork.metadata)

    update_artwork(artwork_id, metadata=meta)
    upload_path = artwork.upload_path

    agent = PublishingAgent(api_key)
    revision = (
        artwork.revision_notes
        if artwork.status == ArtworkStatus.NEEDS_REVISION.value
        else None
    )
    brand_context = {"website": meta.website, "metadata": meta.to_dict()}

    result = agent.prepare_output_pack(
        upload_path,
        brand_context=brand_context,
        revision_notes=revision or None,
        include_crops=include_crops,
    )
    content = result.get("content", {})
    meta = metadata_from_ai(content, meta)
    update_artwork(artwork_id, output_path=result["output_folder"], metadata=meta)
    submit_for_review(artwork_id)
    return {
        "ok": True,
        "artwork_id": artwork_id,
        "filename": artwork.filename,
        "output_folder": result["output_folder"],
        "content": content,
        "metadata": meta.to_dict(),
        "generated_images": result.get("generated_images", []),
    }


def process_batch(
    artwork_ids: list[int],
    api_key: Optional[str],
    *,
    include_crops: bool = True,
    metadata_override: Optional[ArtworkMetadata] = None,
) -> list[dict[str, Any]]:
    results = []
    for aid in artwork_ids:
        try:
            results.append(
                process_artwork(
                    aid,
                    api_key,
                    include_crops=include_crops,
                    metadata_override=metadata_override,
                )
            )
        except Exception as e:
            results.append({
                "ok": False,
                "artwork_id": aid,
                "error": str(e),
            })
    return results


def list_draft_artwork_ids() -> list[int]:
    return [a.id for a in list_artworks(status=ArtworkStatus.DRAFT.value)]
