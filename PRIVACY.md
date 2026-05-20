# Privacy notice (UK GDPR) — ArtFlow AI

**For:** Roxy Megyesi / independent artist use  
**Last updated:** May 2026

## What this app stores locally

- Uploaded artwork files in `uploads/` (master copies)
- Generated output packs in `outputs/`
- A local SQLite database (`artflow.db`) with filenames, approval status, revision notes, and metadata you enter (title, platforms, etc.)

## What leaves your computer

- If you configure a **Google Gemini API key**, image and website text may be sent to Google for AI caption generation. Review [Google’s privacy terms](https://policies.google.com/privacy) before use.
- Optional **website URL** scraping reads public page text only; no account login is required.

## What we do not do

- No automatic posting to Instagram, Pinterest, Squarespace, Gelato, or other platforms
- No Dropbox OAuth or cloud sync in Phase 1
- No sale or sharing of your data by this codebase

## Your rights (UK GDPR)

You are the data controller for artwork and metadata on your machine. You may:

- **Access / export:** copy files from `uploads/`, `outputs/`, and `artflow.db`
- **Erase:** delete those folders and the database file
- **Restrict processing:** run without an API key (fallback text only)

## Security tips for Roxy

- Keep your API key in Streamlit secrets or environment variables, not in shared screenshots
- Back up `uploads/` and approved `outputs/` to your usual storage (e.g. Dropbox) manually
- Do not commit `.env` or API keys to Git

## Contact

For questions about this tool’s data handling, contact your developer or support contact listed in `SETUP.md`.
