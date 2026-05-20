"""SQLite catalogue for ArtFlow AI artworks."""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from models import Artwork, ArtworkMetadata, ArtworkStatus

DB_PATH = Path("artflow.db")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS artworks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL DEFAULT 'draft',
                revision_notes TEXT DEFAULT '',
                metadata TEXT DEFAULT '{}',
                output_path TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )


def _row_to_artwork(row: sqlite3.Row) -> Artwork:
    meta = ArtworkMetadata.from_dict(json.loads(row["metadata"] or "{}"))
    return Artwork(
        id=row["id"],
        filename=row["filename"],
        status=row["status"],
        revision_notes=row["revision_notes"] or "",
        metadata=meta,
        output_path=row["output_path"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def create_artwork(filename: str, metadata: Optional[ArtworkMetadata] = None) -> Artwork:
    now = _now_iso()
    meta_json = json.dumps((metadata or ArtworkMetadata()).to_dict())
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO artworks (filename, status, revision_notes, metadata, output_path, created_at, updated_at)
            VALUES (?, ?, '', ?, NULL, ?, ?)
            ON CONFLICT(filename) DO UPDATE SET updated_at = excluded.updated_at
            RETURNING *
            """,
            (filename, ArtworkStatus.DRAFT.value, meta_json, now, now),
        )
        row = cursor.fetchone()
    return _row_to_artwork(row)


def get_artwork(artwork_id: int) -> Optional[Artwork]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM artworks WHERE id = ?", (artwork_id,)).fetchone()
    return _row_to_artwork(row) if row else None


def get_artwork_by_filename(filename: str) -> Optional[Artwork]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM artworks WHERE filename = ?", (filename,)).fetchone()
    return _row_to_artwork(row) if row else None


def list_artworks(status: Optional[str] = None) -> list[Artwork]:
    with get_connection() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM artworks WHERE status = ? ORDER BY updated_at DESC",
                (status,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM artworks ORDER BY updated_at DESC"
            ).fetchall()
    return [_row_to_artwork(r) for r in rows]


def update_artwork(
    artwork_id: int,
    *,
    status: Optional[str] = None,
    revision_notes: Optional[str] = None,
    metadata: Optional[ArtworkMetadata] = None,
    output_path: Optional[str] = None,
) -> Optional[Artwork]:
    artwork = get_artwork(artwork_id)
    if not artwork:
        return None

    new_status = status if status is not None else artwork.status
    new_notes = revision_notes if revision_notes is not None else artwork.revision_notes
    new_meta = metadata if metadata is not None else artwork.metadata
    new_output = output_path if output_path is not None else artwork.output_path

    with get_connection() as conn:
        conn.execute(
            """
            UPDATE artworks
            SET status = ?, revision_notes = ?, metadata = ?, output_path = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                new_status,
                new_notes,
                json.dumps(new_meta.to_dict()),
                new_output,
                _now_iso(),
                artwork_id,
            ),
        )
    return get_artwork(artwork_id)


def catalogue_summary() -> dict[str, int]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT status, COUNT(*) as cnt FROM artworks GROUP BY status"
        ).fetchall()
    return {r["status"]: r["cnt"] for r in rows}
