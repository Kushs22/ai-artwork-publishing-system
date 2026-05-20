"""Human approval workflow for ArtFlow AI."""

import os
from typing import Optional

from db import get_artwork, update_artwork
from image_processor import ImageProcessor
from models import Artwork, ArtworkStatus


STATUS_LABELS = {
    ArtworkStatus.DRAFT.value: ("Draft", "#6c757d"),
    ArtworkStatus.PENDING_REVIEW.value: ("Pending review", "#ffc107"),
    ArtworkStatus.APPROVED.value: ("Approved", "#28a745"),
    ArtworkStatus.NEEDS_REVISION.value: ("Needs revision", "#fd7e14"),
    ArtworkStatus.REJECTED.value: ("Rejected", "#dc3545"),
}


def status_badge_html(status: str) -> str:
    label, colour = STATUS_LABELS.get(status, (status.replace("_", " ").title(), "#6c757d"))
    return (
        f'<span style="background:{colour};color:#fff;padding:4px 10px;'
        f'border-radius:12px;font-size:0.85em;font-weight:600;">{label}</span>'
    )


def submit_for_review(artwork_id: int) -> Optional[Artwork]:
    return update_artwork(artwork_id, status=ArtworkStatus.PENDING_REVIEW.value)


def approve_artwork(artwork_id: int, *, apply_crops: bool = True) -> Optional[Artwork]:
    artwork = get_artwork(artwork_id)
    if not artwork:
        return None

    if apply_crops and artwork.output_path:
        master = artwork.upload_path
        if os.path.isfile(master):
            ImageProcessor().apply_crops(master, artwork.output_path)

    return update_artwork(
        artwork_id,
        status=ArtworkStatus.APPROVED.value,
        revision_notes="",
    )


def revise_artwork(artwork_id: int, revision_notes: str) -> Optional[Artwork]:
    if not revision_notes.strip():
        return None
    return update_artwork(
        artwork_id,
        status=ArtworkStatus.NEEDS_REVISION.value,
        revision_notes=revision_notes.strip(),
    )


def reject_artwork(artwork_id: int) -> Optional[Artwork]:
    return update_artwork(artwork_id, status=ArtworkStatus.REJECTED.value)
