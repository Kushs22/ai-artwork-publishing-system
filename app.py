import os
import json

import streamlit as st

from approval import (
    approve_artwork,
    reject_artwork,
    revise_artwork,
    status_badge_html,
    submit_for_review,
)
from db import (
    catalogue_summary,
    create_artwork,
    get_artwork,
    init_db,
    list_artworks,
    update_artwork,
)
from image_processor import ImageProcessor
from models import ArtworkMetadata, ArtworkStatus, PLATFORM_OPTIONS
from publishing_agent import PublishingAgent


def get_api_key() -> str | None:
    try:
        if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
    env_key = os.environ.get("GEMINI_API_KEY")
    if env_key:
        return env_key
    manual = st.session_state.get("manual_api_key", "")
    return manual.strip() or None


def save_uploads(uploaded_files) -> list[str]:
    os.makedirs("uploads", exist_ok=True)
    saved = []
    for uploaded_file in uploaded_files:
        path = os.path.join("uploads", uploaded_file.name)
        if not os.path.exists(path):
            with open(path, "wb") as f:
                f.write(uploaded_file.getbuffer())
        create_artwork(uploaded_file.name)
        saved.append(uploaded_file.name)
    return saved


def metadata_form(artwork, key_prefix: str) -> ArtworkMetadata:
    meta = artwork.metadata
    st.markdown("#### Artwork metadata")
    title = st.text_input("Title", value=meta.title, key=f"{key_prefix}_title")
    theme = st.text_input("Theme", value=meta.theme, key=f"{key_prefix}_theme")
    collection = st.text_input("Collection", value=meta.collection, key=f"{key_prefix}_collection")
    fmt = st.text_input("Format (e.g. A3 print, square)", value=meta.format, key=f"{key_prefix}_format")
    website = st.text_input(
        "Client website (brand context)",
        value=meta.website,
        placeholder="https://www.example.com/",
        key=f"{key_prefix}_website",
    )
    st.markdown("**Platforms** (manual posting — no auto-post)")
    platforms = []
    cols = st.columns(len(PLATFORM_OPTIONS))
    for i, platform in enumerate(PLATFORM_OPTIONS):
        with cols[i]:
            if st.checkbox(platform, value=platform in meta.platforms, key=f"{key_prefix}_plat_{platform}"):
                platforms.append(platform)
    return ArtworkMetadata(
        title=title, theme=theme, collection=collection, format=fmt, platforms=platforms, website=website
    )


def render_artwork_review(artwork_id: int):
    artwork = get_artwork(artwork_id)
    if not artwork:
        st.error("Artwork not found.")
        return

    st.markdown(status_badge_html(artwork.status), unsafe_allow_html=True)
    st.caption(f"File: `{artwork.filename}` · ID {artwork.id}")

    upload_path = artwork.upload_path
    if not os.path.exists(upload_path):
        st.warning("Master file missing from uploads/. Re-upload to continue.")
        return

    st.image(upload_path, caption=artwork.filename, width=400)

    meta = metadata_form(artwork, f"review_{artwork_id}")
    if st.button("Save metadata", key=f"save_meta_{artwork_id}"):
        update_artwork(artwork_id, metadata=meta)
        st.success("Metadata saved.")

    processor = ImageProcessor()

    with st.expander("Crop preview (no files written until export or approve)"):
        if st.button("Load crop previews", key=f"preview_{artwork_id}"):
            previews = processor.preview_crops(upload_path)
            preview_cols = st.columns(2)
            preview_bytes = processor.preview_to_bytes(previews)
            for idx, (name, img_bytes) in enumerate(preview_bytes.items()):
                with preview_cols[idx % 2]:
                    st.image(img_bytes, caption=name.replace("_", " "), use_container_width=True)

    col_gen, col_crops = st.columns(2)
    api_key = get_api_key()

    with col_gen:
        generate = st.button("Generate content pack", key=f"gen_{artwork_id}")
    with col_crops:
        export_crops = st.button("Generate & export crops", key=f"crops_{artwork_id}")

    if generate or export_crops:
        update_artwork(artwork_id, metadata=meta)
        agent = PublishingAgent(api_key)
        revision = artwork.revision_notes if artwork.status == ArtworkStatus.NEEDS_REVISION.value else ""
        if revision:
            st.info("Regenerating with revision notes applied.")
        brand_context = {"website": meta.website, "metadata": meta.to_dict()}
        with st.spinner("Generating publishing pack..."):
            result = agent.prepare_output_pack(
                upload_path,
                brand_context=brand_context,
                revision_notes=revision or None,
                include_crops=export_crops,
            )
        update_artwork(artwork_id, output_path=result["output_folder"])
        submit_for_review(artwork_id)
        st.session_state[f"last_result_{artwork_id}"] = result
        st.success(f"Pack created: `{result['output_folder']}`")

    result = st.session_state.get(f"last_result_{artwork_id}")
    if result or artwork.output_path:
        folder = (result or {}).get("output_folder") or artwork.output_path
        st.subheader("Output pack")
        st.code(folder)

        content_json = os.path.join(folder, "content.json")
        if os.path.exists(content_json):
            with open(content_json, encoding="utf-8") as f:
                content = json.load(f)
            st.json(content)
            with st.expander("Gelato section"):
                st.json({
                    "product_title": content.get("gelato_product_title", ""),
                    "product_description": content.get("gelato_product_description", ""),
                    "tags": content.get("gelato_tags", []),
                })
            checklist_json = os.path.join(folder, "platform_checklist.json")
            with st.expander("Platform checklist"):
                if os.path.exists(checklist_json):
                    with open(checklist_json, encoding="utf-8") as f:
                        st.json(json.load(f))
                else:
                    st.caption("Generate a content pack to create the checklist.")

        for img_path in (result or {}).get("generated_images", []):
            if os.path.exists(img_path):
                st.image(img_path, caption=os.path.basename(img_path), width=280)

        if not (result or {}).get("generated_images"):
            crop_files = [
                os.path.join(folder, f)
                for f in os.listdir(folder)
                if f.endswith(".jpg") and f != os.path.basename(upload_path)
            ] if os.path.isdir(folder) else []
            for img_path in crop_files:
                st.image(img_path, caption=os.path.basename(img_path), width=280)

    st.subheader("Human approval")
    if artwork.revision_notes:
        st.info(f"Revision notes: {artwork.revision_notes}")

    rev_notes = st.text_area(
        "Revision notes (required for Revise)",
        key=f"rev_notes_{artwork_id}",
        placeholder="e.g. Soften Instagram caption, emphasise botanical tones",
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Approve", key=f"approve_{artwork_id}", type="primary"):
            if not artwork.output_path and not result:
                st.error("Generate a content pack before approving.")
            else:
                approved = approve_artwork(artwork_id, apply_crops=True)
                if approved:
                    st.success("Approved. Crops exported if not already present.")
                    st.rerun()
                else:
                    st.error("Could not approve artwork.")
    with c2:
        if st.button("Revise", key=f"revise_{artwork_id}"):
            if not rev_notes.strip():
                st.error("Add revision notes before requesting a revision.")
            else:
                revise_artwork(artwork_id, rev_notes)
                st.warning("Marked as needs revision. Regenerate content with notes saved.")
                st.rerun()
    with c3:
        if st.button("Reject", key=f"reject_{artwork_id}"):
            reject_artwork(artwork_id)
            st.error("Rejected.")
            st.rerun()


def page_upload():
    st.subheader("Upload artwork")
    st.caption("Masters are saved to uploads/ and never modified or deleted by the app.")

    uploaded_files = st.file_uploader(
        "Upload artwork images",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
    )
    if uploaded_files:
        names = save_uploads(uploaded_files)
        st.success(f"Saved {len(names)} file(s) to catalogue (draft). No crops generated yet.")
        for name in names:
            path = os.path.join("uploads", name)
            st.image(path, caption=name, width=200)


def page_catalogue():
    st.subheader("Catalogue")
    summary = catalogue_summary()
    if summary:
        cols = st.columns(len(summary))
        for i, (status, count) in enumerate(summary.items()):
            cols[i % len(cols)].metric(status.replace("_", " ").title(), count)
    else:
        st.info("No artworks in catalogue yet. Upload images to begin.")

    filter_status = st.selectbox(
        "Filter by status",
        ["All"] + ArtworkStatus.choices(),
    )
    status_filter = None if filter_status == "All" else filter_status
    artworks = list_artworks(status=status_filter)

    for art in artworks:
        with st.container(border=True):
            cols = st.columns([3, 1, 1])
            with cols[0]:
                st.markdown(f"**{art.metadata.title or art.filename}**")
                st.caption(art.filename)
            with cols[1]:
                st.markdown(status_badge_html(art.status), unsafe_allow_html=True)
            with cols[2]:
                if st.button("Open", key=f"open_{art.id}"):
                    st.session_state["review_id"] = art.id
                    st.session_state["page"] = "Review"
                    st.rerun()


def main():
    st.set_page_config(page_title="ArtFlow AI", layout="wide")
    init_db()

    st.title("ArtFlow AI")
    st.write("AI publishing assistant for independent artists — human approval required before publishing.")

    with st.sidebar:
        st.header("Settings")
        manual_key = st.text_input(
            "Gemini API key (optional override)",
            type="password",
            help="Uses st.secrets GEMINI_API_KEY or env GEMINI_API_KEY first.",
            key="manual_api_key",
        )
        if manual_key:
            st.session_state["manual_api_key"] = manual_key
        if get_api_key():
            st.success("API key configured")
        else:
            st.info("No API key — fallback captions will be used.")

        page = st.radio(
            "Navigation",
            ["Upload", "Catalogue", "Review"],
            index=["Upload", "Catalogue", "Review"].index(st.session_state.get("page", "Upload")),
            key="nav_page",
        )
        st.session_state["page"] = page

    if st.session_state["page"] == "Upload":
        page_upload()
    elif st.session_state["page"] == "Catalogue":
        page_catalogue()
    elif st.session_state["page"] == "Review":
        artworks = list_artworks()
        if not artworks:
            st.info("Upload artwork first.")
        else:
            ids = {f"{a.metadata.title or a.filename} ({a.status})": a.id for a in artworks}
            default_id = st.session_state.get("review_id", artworks[0].id)
            default_label = next((k for k, v in ids.items() if v == default_id), list(ids.keys())[0])
            choice = st.selectbox("Select artwork", list(ids.keys()), index=list(ids.keys()).index(default_label))
            render_artwork_review(ids[choice])


if __name__ == "__main__":
    main()
