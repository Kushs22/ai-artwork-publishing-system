"""Download packs and save processed assets to a folder on the user's machine."""

import io
import os
import shutil
import zipfile
from pathlib import Path
from typing import Optional


DEFAULT_EXPORT_DIR = os.path.expanduser("~/Desktop/ArtFlow Exports")

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def normalize_export_path(path: str) -> str:
    p = path.strip()
    if not p:
        return DEFAULT_EXPORT_DIR
    return os.path.expanduser(p)


def list_pack_files(folder: str) -> list[str]:
    if not folder or not os.path.isdir(folder):
        return []
    files = []
    for name in sorted(os.listdir(folder)):
        full = os.path.join(folder, name)
        if os.path.isfile(full):
            files.append(full)
    return files


def list_image_files(folder: str) -> list[str]:
    return [
        f for f in list_pack_files(folder)
        if os.path.splitext(f)[1].lower() in IMAGE_EXTENSIONS
        and not os.path.basename(f).startswith("_")
    ]


def build_zip_bytes(folder: str) -> bytes:
    """Zip entire output pack for browser download."""
    buffer = io.BytesIO()
    base = os.path.basename(folder.rstrip(os.sep)) or "artflow_pack"
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in list_pack_files(folder):
            arcname = os.path.join(base, os.path.basename(file_path))
            zf.write(file_path, arcname=arcname)
    buffer.seek(0)
    return buffer.getvalue()


def install_pack_to_folder(
    source_folder: str,
    export_root: str,
    pack_label: Optional[str] = None,
) -> str:
    """
    Copy output pack into export_root/pack_label/ on this computer.
    Returns destination path.
    """
    if not os.path.isdir(source_folder):
        raise FileNotFoundError(f"Output folder not found: {source_folder}")

    root = normalize_export_path(export_root)
    os.makedirs(root, exist_ok=True)

    label = pack_label or os.path.basename(source_folder.rstrip(os.sep))
    safe_label = "".join(c if c.isalnum() or c in "._- " else "_" for c in label).strip()
    dest = os.path.join(root, safe_label)

    if os.path.exists(dest):
        shutil.rmtree(dest)
    shutil.copytree(source_folder, dest)
    return dest


def open_folder_in_finder(folder_path: str) -> bool:
    """Reveal folder in macOS Finder / Windows Explorer / Linux file manager."""
    import platform
    import subprocess

    path = os.path.abspath(folder_path)
    if not os.path.isdir(path):
        return False

    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.run(["open", path], check=False)
        elif system == "Windows":
            os.startfile(path)  # type: ignore[attr-defined]
        else:
            subprocess.run(["xdg-open", path], check=False)
        return True
    except Exception:
        return False
