# ArtFlow AI — setup for Roxy

Simple steps to run ArtFlow on your Mac.

## 1. Prerequisites

- Python 3.10 or newer
- A [Google AI Studio](https://aistudio.google.com/) API key (optional — fallback text works without it)

## 2. Install

```bash
cd ai-artwork-publishing-system
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. API key (recommended)

**Option A — environment variable**

```bash
export GEMINI_API_KEY="your-key-here"
```

**Option B — Streamlit secrets**

Create `.streamlit/secrets.toml`:

```toml
GEMINI_API_KEY = "your-key-here"
```

Never share this file or commit it to Git.

## 4. Run the app

```bash
streamlit run app.py
```

Your browser opens the dashboard.

## 5. Typical workflow

1. **Upload** — add JPG/PNG files (saved to `uploads/`, never auto-cropped)
2. **Catalogue** — see status: draft → pending review → approved / needs revision / rejected
3. **Review** — fill metadata (title, theme, format, platforms)
4. **Preview crops** — check framing before exporting
5. **Generate content pack** — AI captions + `content.json` + Gelato section + platform checklist
6. **Generate & export crops** — only when you are ready (or crops run on **Approve**)
7. **Approve / Revise / Reject** — human gate before treating a pack as final
8. **Save to your computer** — download ZIP, save to `~/Desktop/ArtFlow Exports`, or open in Finder
9. **Manual posting** — copy assets and text to Instagram, Pinterest, Squarespace, Gelato, website yourself

## 6. Save edited images on your Mac

After AI prep, use **Save to your computer**:

- **Download ZIP** — browser download (works on iPad too)
- **Save folder to disk** — copies crops + captions into the folder in the sidebar (default: Desktop/ArtFlow Exports)
- **Open folder** — opens that folder in Finder

Enable **Auto-save packs after batch AI prep** in the sidebar to copy every batch automatically.

## 7. Folders

| Folder / file   | Purpose                                      |
|-----------------|----------------------------------------------|
| `uploads/`      | Master artwork (do not delete from app)      |
| `outputs/`      | Generated packs per artwork                  |
| `artflow.db`    | Catalogue and approval state                 |

## 8. Troubleshooting

- **No AI captions:** check `GEMINI_API_KEY` in terminal or secrets
- **Import errors:** re-run `pip install -r requirements.txt` inside your venv
- **Reset catalogue:** stop app, delete `artflow.db` (uploads/ outputs/ stay)

## 9. Privacy

See [PRIVACY.md](PRIVACY.md) for UK GDPR notes.
