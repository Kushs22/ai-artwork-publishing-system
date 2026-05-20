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
from batch_processor import process_artwork, process_batch, list_draft_artwork_ids
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
from brand_voice import crops_for_platforms, load_user_examples, save_user_examples
from publishing_agent import PublishingAgent
from ui_theme import inject_theme, hero

DEFAULT_WEBSITE = "https://www.roxymegyesi.com/"


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


def save_uploads(uploaded_files, shared_meta: ArtworkMetadata | None = None) -> list[str]:
    os.makedirs("uploads", exist_ok=True)
    saved = []
    for uploaded_file in uploaded_files:
        path = os.path.join("uploads", uploaded_file.name)
        if not os.path.exists(path):
            with open(path, "wb") as f:
                f.write(uploaded_file.getbuffer())
        meta = shared_meta or ArtworkMetadata(website=DEFAULT_WEBSITE)
        create_artwork(uploaded_file.name, metadata=meta)
        saved.append(uploaded_file.name)
    return saved


def shared_metadata_form(key_prefix: str = "shared") -> ArtworkMetadata:
    st.markdown('<p class="section-tag">Batch settings (applied to all new uploads)</p>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        collection_options = ["Bark & Grain", "Miniatures", "Urban Signal", "Art Prints", "Other"]
        collection = st.selectbox("Collection", collection_options, key=f"{key_prefix}_coll")
        theme = st.text_input("Theme / mood", key=f"{key_prefix}_theme", placeholder="e.g. winter bark, quiet detail")
    with c2:
        fmt = st.text_input("Format", key=f"{key_prefix}_format", placeholder="e.g. A3 print, miniature")
        website = st.text_input("Brand website", value=DEFAULT_WEBSITE, key=f"{key_prefix}_web")

    st.markdown("**Platforms**")
    pcols = st.columns(len(PLATFORM_OPTIONS))
    platforms = []
    default_plat = list(PLATFORM_OPTIONS)
    for i, platform in enumerate(PLATFORM_OPTIONS):
        with pcols[i]:
            if st.checkbox(
                platform,
                value=platform in default_plat,
                key=f"{key_prefix}_p_{platform}",
            ):
                platforms.append(platform)

    return ArtworkMetadata(
        title="",
        theme=theme,
        collection=collection if collection != "Other" else "",
        format=fmt,
        platforms=platforms,
        website=website or DEFAULT_WEBSITE,
    )


def metadata_form(artwork, key_prefix: str) -> ArtworkMetadata:
    meta = artwork.metadata
    st.markdown("#### Artwork metadata")
    title = st.text_input("Title", value=meta.title or os.path.splitext(artwork.filename)[0], key=f"{key_prefix}_title")
    theme = st.text_input("Theme", value=meta.theme, key=f"{key_prefix}_theme")
    collection_options = ["", "Bark & Grain", "Miniatures", "Urban Signal", "Art Prints", "Other"]
    coll_index = collection_options.index(meta.collection) if meta.collection in collection_options else 0
    collection = st.selectbox("Collection", collection_options, index=coll_index, key=f"{key_prefix}_collection")
    if collection == "Other":
        collection = st.text_input("Collection name", value=meta.collection, key=f"{key_prefix}_collection_other")
    fmt = st.text_input("Format", value=meta.format, key=f"{key_prefix}_format")
    website = st.text_input(
        "Client website",
        value=meta.website or DEFAULT_WEBSITE,
        key=f"{key_prefix}_website",
    )
    st.markdown("**Platforms**")
    platforms = []
    cols = st.columns(len(PLATFORM_OPTIONS))
    for i, platform in enumerate(PLATFORM_OPTIONS):
        with cols[i]:
            if st.checkbox(platform, value=platform in (meta.platforms or ["Instagram", "Pinterest"]), key=f"{key_prefix}_plat_{platform}"):
                platforms.append(platform)
    return ArtworkMetadata(
        title=title, theme=theme, collection=collection, format=fmt, platforms=platforms, website=website
    )


def render_content_cards(content: dict):
    if content.get("suggested_title") or content.get("suggested_theme"):
        st.markdown("**AI detected from image**")
        t1, t2, t3 = st.columns(3)
        with t1:
            st.metric("Title", content.get("suggested_title", "—"))
        with t2:
            st.metric("Theme", content.get("suggested_theme", "—"))
        with t3:
            st.metric("Collection", content.get("suggested_collection", "—"))
    if content.get("instagram_caption"):
        st.markdown("**Instagram (short)**")
        st.info(content["instagram_caption"])
    if content.get("instagram_long_caption"):
        st.markdown("**Instagram (long)**")
        st.write(content["instagram_long_caption"])
    if content.get("pinterest_description"):
        st.markdown("**Pinterest**")
        st.write(content["pinterest_description"])
    tags = content.get("hashtags", [])
    if tags:
        st.markdown("**Hashtags**")
        st.code(" ".join(tags) if isinstance(tags, list) else str(tags))


def render_artwork_review(artwork_id: int):
    artwork = get_artwork(artwork_id)
    if not artwork:
        st.error("Artwork not found.")
        return

    st.markdown(status_badge_html(artwork.status), unsafe_allow_html=True)
    st.caption(f"`{artwork.filename}` · ID {artwork.id}")

    upload_path = artwork.upload_path
    if not os.path.exists(upload_path):
        st.warning("Master file missing. Re-upload to continue.")
        return

    col_img, col_meta = st.columns([1, 1.2])
    with col_img:
        st.image(upload_path, caption=artwork.filename, width=360)

    with col_meta:
        meta = metadata_form(artwork, f"review_{artwork_id}")
        if st.button("Save metadata", key=f"save_meta_{artwork_id}"):
            update_artwork(artwork_id, metadata=meta)
            st.success("Saved.")

    processor = ImageProcessor()
    with st.expander("Crop preview", expanded=False):
        if st.button("Load previews", key=f"preview_{artwork_id}"):
            crop_names = crops_for_platforms(meta.platforms) if meta.platforms else None
            previews = processor.preview_crops(upload_path, crop_names=crop_names)
            preview_bytes = processor.preview_to_bytes(previews)
            pcols = st.columns(3)
            for idx, (name, img_bytes) in enumerate(preview_bytes.items()):
                with pcols[idx % 3]:
                    st.image(img_bytes, caption=name.replace("_", " "))

    st.info(
        "**AI Auto Prep** analyses the image, fills title & theme, writes Instagram/Pinterest/shop copy, "
        "and exports all platform-sized crops. You still approve before posting."
    )
    if st.button("AI Auto Prep — analyse, caption, crop all platforms", key=f"auto_{artwork_id}", type="primary"):
        update_artwork(artwork_id, metadata=meta)
        with st.spinner("AI analysing image, generating copy & crops..."):
            result = process_artwork(
                artwork_id,
                get_api_key(),
                include_crops=True,
                metadata_override=meta,
            )
        if result.get("ok"):
            st.session_state[f"last_result_{artwork_id}"] = result
            st.success("Auto prep complete — review below, then Approve.")
        else:
            st.error(result.get("error", "Failed"))
        st.rerun()

    c1, c2 = st.columns(2)
    with c1:
        generate = st.button("Captions only (no crops)", key=f"gen_{artwork_id}")
    with c2:
        export_crops = st.button("Captions + crops", key=f"crops_{artwork_id}")

    if generate or export_crops:
        update_artwork(artwork_id, metadata=meta)
        include_crops = export_crops
        with st.spinner("Processing..."):
            result = process_artwork(
                artwork_id,
                get_api_key(),
                include_crops=include_crops,
                metadata_override=meta,
            )
        if result.get("ok"):
            st.session_state[f"last_result_{artwork_id}"] = result
            st.success(f"Done → `{result['output_folder']}`")
        else:
            st.error(result.get("error", "Failed"))

    result = st.session_state.get(f"last_result_{artwork_id}")
    folder = (result or {}).get("output_folder") or artwork.output_path
    if folder and os.path.isdir(folder):
        content_json = os.path.join(folder, "content.json")
        if os.path.exists(content_json):
            with open(content_json, encoding="utf-8") as f:
                content = json.load(f)
            render_content_cards(content)

        crops = (result or {}).get("generated_images") or [
            os.path.join(folder, f) for f in os.listdir(folder)
            if f.endswith(".jpg") and not f.startswith("_")
        ]
        if crops:
            st.markdown("**Exported sizes**")
            cc = st.columns(min(4, len(crops)))
            for i, img_path in enumerate(crops[:8]):
                if os.path.exists(img_path):
                    with cc[i % len(cc)]:
                        st.image(img_path, caption=os.path.basename(img_path))

    st.divider()
    st.subheader("Approval")
    rev_notes = st.text_area("Revision notes", key=f"rev_{artwork_id}", height=80)
    a1, a2, a3 = st.columns(3)
    with a1:
        if st.button("Approve", key=f"ap_{artwork_id}", type="primary"):
            if approve_artwork(artwork_id, apply_crops=True):
                st.success("Approved")
                st.rerun()
    with a2:
        if st.button("Revise", key=f"rv_{artwork_id}"):
            if rev_notes.strip() and revise_artwork(artwork_id, rev_notes):
                st.warning("Needs revision — regenerate with notes")
                st.rerun()
    with a3:
        if st.button("Reject", key=f"rj_{artwork_id}"):
            reject_artwork(artwork_id)
            st.rerun()


def page_batch_studio():
    st.markdown('<p class="section-tag">Batch studio</p>', unsafe_allow_html=True)
    st.subheader("Upload & process multiple artworks")
    st.caption("Upload images → one click → AI detects title/theme per picture, writes captions & hashtags, crops for Instagram, Pinterest, website & Gelato.")

    st.success(
        "**Fully AI-driven prep:** You do not need to type title or theme manually. "
        "Select platforms below, upload images, then click **AI Auto Prep all**."
    )

    shared_meta = shared_metadata_form("batch")
    auto_on_upload = st.checkbox("Auto AI prep immediately after each upload", value=False)

    uploaded_files = st.file_uploader(
        "Drop multiple artwork images (JPG / PNG)",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        help="Each file gets its own captions based on the image + settings below.",
    )

    if uploaded_files:
        names = save_uploads(uploaded_files, shared_meta)
        st.success(f"Added {len(names)} artwork(s) to catalogue.")
        if auto_on_upload and get_api_key():
            from db import get_artwork_by_filename
            progress = st.progress(0)
            for i, name in enumerate(names):
                art = get_artwork_by_filename(name)
                if art:
                    progress.progress((i + 1) / len(names), text=f"AI prep {name}...")
                    m = shared_meta
                    if not m.title:
                        m.title = os.path.splitext(name)[0].replace("_", " ").title()
                    process_artwork(art.id, get_api_key(), include_crops=True, metadata_override=m)
            progress.empty()
            st.success("Auto prep finished for new uploads.")
        elif auto_on_upload:
            st.warning("Add Gemini API key to enable auto prep on upload.")

        st.markdown("**Upload preview**")
        cols = st.columns(min(4, len(names)))
        for i, name in enumerate(names):
            with cols[i % len(cols)]:
                st.image(os.path.join("uploads", name), caption=name)

    drafts = list_draft_artwork_ids()
    all_drafts = list_artworks(status=ArtworkStatus.DRAFT.value)

    st.divider()
    st.markdown(f"**{len(all_drafts)}** draft(s) ready to process")

    b1, b2, b3 = st.columns(3)
    with b1:
        process_all = st.button(
            "AI Auto Prep all — title, theme, captions, all platform crops",
            type="primary",
            disabled=len(drafts) == 0,
        )
    with b2:
        captions_only = st.button("Captions only (no crop files)", disabled=len(drafts) == 0)
    with b3:
        apply_meta = st.button("Apply batch settings to all drafts", disabled=len(drafts) == 0)

    if apply_meta and drafts:
        for aid in drafts:
            art = get_artwork(aid)
            if art:
                m = shared_meta
                if not m.title:
                    m.title = os.path.splitext(art.filename)[0].replace("_", " ").title()
                update_artwork(aid, metadata=m)
        st.success("Batch settings applied to all drafts.")
        st.rerun()

    if process_all or captions_only:
        include_crops = process_all
        progress = st.progress(0, text="Starting batch...")
        results = []
        for i, aid in enumerate(drafts):
            art = get_artwork(aid)
            meta = shared_meta
            if art and not meta.title:
                meta = ArtworkMetadata(
                    title=os.path.splitext(art.filename)[0].replace("_", " ").title(),
                    theme=shared_meta.theme,
                    collection=shared_meta.collection,
                    format=shared_meta.format,
                    platforms=shared_meta.platforms,
                    website=shared_meta.website,
                )
            progress.progress((i + 1) / len(drafts), text=f"Processing {i + 1}/{len(drafts)}...")
            results.append(
                process_artwork(aid, get_api_key(), include_crops=include_crops, metadata_override=meta)
            )
        progress.empty()
        ok = sum(1 for r in results if r.get("ok"))
        st.success(f"Finished {ok}/{len(results)} artworks.")
        st.session_state["batch_results"] = results

    if st.session_state.get("batch_results"):
        st.subheader("Batch results")
        for r in st.session_state["batch_results"]:
            if not r.get("ok"):
                st.error(f"{r.get('filename', r.get('artwork_id'))}: {r.get('error')}")
                continue
            with st.expander(f"✓ {r.get('filename', 'artwork')}", expanded=False):
                if r.get("metadata"):
                    st.caption(
                        f"Title: {r['metadata'].get('title')} · Theme: {r['metadata'].get('theme')} · "
                        f"Collection: {r['metadata'].get('collection')}"
                    )
                render_content_cards(r.get("content", {}))
                st.caption(r.get("output_folder", ""))
                if r.get("generated_images"):
                    icols = st.columns(3)
                    for j, p in enumerate(r["generated_images"][:6]):
                        if os.path.exists(p):
                            with icols[j % 3]:
                                st.image(p, caption=os.path.basename(p))


def page_upload():
    page_batch_studio()


def page_catalogue():
    st.markdown('<p class="section-tag">Catalogue</p>', unsafe_allow_html=True)
    summary = catalogue_summary()
    if summary:
        cols = st.columns(min(5, len(summary)))
        for i, (status, count) in enumerate(summary.items()):
            cols[i % len(cols)].metric(status.replace("_", " ").title(), count)
    else:
        st.info("No artworks yet — use Batch Studio to upload.")

    filter_status = st.selectbox("Filter", ["All"] + ArtworkStatus.choices())
    status_filter = None if filter_status == "All" else filter_status
    for art in list_artworks(status=status_filter):
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([1, 2.5, 1, 1])
            thumb = art.upload_path
            with c1:
                if os.path.exists(thumb):
                    st.image(thumb, width=72)
            with c2:
                st.markdown(f"**{art.metadata.title or art.filename}**")
                st.caption(art.filename)
            with c3:
                st.markdown(status_badge_html(art.status), unsafe_allow_html=True)
            with c4:
                if st.button("Review", key=f"rev_open_{art.id}"):
                    st.session_state["review_id"] = art.id
                    st.session_state["page"] = "Review"
                    st.rerun()


def sidebar_settings():
    st.markdown("### Settings")
    manual_key = st.text_input(
        "Gemini API key",
        type="password",
        help="Or use .streamlit/secrets.toml",
        key="manual_api_key",
    )
    if manual_key:
        st.session_state["manual_api_key"] = manual_key
    if get_api_key():
        st.success("API connected")
    else:
        st.warning("Add API key for AI captions")

    with st.expander("Brand voice training"):
        user_ex = load_user_examples()
        ex_caps = st.text_area(
            "Example captions (one per line)",
            value="\n".join(user_ex.get("example_captions", [])),
            height=100,
        )
        ex_tags = st.text_area(
            "Example hashtags",
            value=" ".join(user_ex.get("example_hashtags", [])),
            height=60,
        )
        if st.button("Save examples", use_container_width=True):
            caps = [ln.strip() for ln in ex_caps.splitlines() if ln.strip()]
            tags = [
                t if t.startswith("#") else f"#{t.lstrip('#')}"
                for t in ex_tags.replace("\n", " ").split()
                if t.strip()
            ]
            save_user_examples({"example_captions": caps, "example_hashtags": tags})
            st.success("Saved")


def main():
    st.set_page_config(
        page_title="ArtFlow AI",
        page_icon="🎨",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_theme()
    init_db()

    with st.sidebar:
        st.markdown("## ArtFlow")
        st.caption("Bark & Grain Studio")
        sidebar_settings()
        st.divider()
        pages = ["Batch Studio", "Catalogue", "Review"]
        page = st.radio(
            "Navigate",
            pages,
            index=pages.index(st.session_state.get("page", "Batch Studio")),
            key="nav_page",
        )
        st.session_state["page"] = page

    hero(
        "ArtFlow AI",
        "Upload multiple artworks · crop for Instagram & Pinterest · unique captions & hashtags per image · human approval before publishing.",
    )

    current = st.session_state.get("page", "Batch Studio")
    if current == "Batch Studio":
        page_batch_studio()
    elif current == "Catalogue":
        page_catalogue()
    elif current == "Review":
        artworks = list_artworks()
        if not artworks:
            st.info("Upload in Batch Studio first.")
        else:
            ids = {f"{a.metadata.title or a.filename} ({a.status})": a.id for a in artworks}
            rid = st.session_state.get("review_id", artworks[0].id)
            label = next((k for k, v in ids.items() if v == rid), list(ids.keys())[0])
            choice = st.selectbox("Artwork", list(ids.keys()), index=list(ids.keys()).index(label))
            render_artwork_review(ids[choice])


if __name__ == "__main__":
    main()
