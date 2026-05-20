"""Data models for ArtFlow AI catalogue."""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Optional


class ArtworkStatus(str, Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    NEEDS_REVISION = "needs_revision"
    REJECTED = "rejected"

    @classmethod
    def choices(cls) -> list[str]:
        return [s.value for s in cls]


PLATFORM_OPTIONS = [
    "Instagram",
    "Pinterest",
    "Squarespace",
    "Gelato",
    "Website",
]


@dataclass
class ArtworkMetadata:
    title: str = ""
    theme: str = ""
    collection: str = ""
    format: str = ""
    platforms: list[str] = field(default_factory=list)
    website: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Optional[dict[str, Any]]) -> "ArtworkMetadata":
        if not data:
            return cls()
        theme = data.get("theme", "") or data.get("theme_collection", "")
        collection = data.get("collection", "") or data.get("theme_collection", "")
        return cls(
            title=data.get("title", ""),
            theme=theme,
            collection=collection,
            format=data.get("format", ""),
            platforms=list(data.get("platforms", [])),
            website=data.get("website", ""),
        )


@dataclass
class Artwork:
    id: int
    filename: str
    status: str
    revision_notes: str
    metadata: ArtworkMetadata
    output_path: Optional[str]
    created_at: str
    updated_at: str

    @property
    def upload_path(self) -> str:
        return f"uploads/{self.filename}"
