# ArtFlow AI

ArtFlow AI is a multimodal AI-assisted publishing workflow system designed for independent artists and creative businesses.

The platform automates artwork preparation and AI-powered content generation by combining image processing, website context analysis, and multimodal AI workflows.

Users can upload artwork images into a Streamlit dashboard, after which the system:

- Automatically crops and resizes images into platform-ready formats
- Analyses artwork visually
- Understands brand tone from a client website
- Generates AI-powered captions, descriptions, hashtags, and website listings
- Creates publishing-ready content packs

The workflow was intentionally designed as a human-in-the-loop AI system rather than a fully autonomous pipeline, allowing creators to review and approve outputs before publishing.

---

# Features

- Multimodal AI-assisted publishing workflow
- Automated artwork resizing and formatting
- Context-aware AI content generation
- Website scraping and brand tone analysis
- Human-in-the-loop approval workflow
- Streamlit-based interactive dashboard
- Fallback content generation support

---

# Tech Stack

- Python
- Streamlit
- Pillow (PIL)
- BeautifulSoup
- Requests
- Google Gemini Flash API

---

# AI Workflow Architecture

The system is structured around two AI-agent style components:

### 1. Image Processing Agent
Responsible for:
- cropping
- resizing
- formatting
- preparing artwork assets for publishing platforms

### 2. Publishing Agent
Responsible for:
- artwork analysis
- website tone analysis
- multimodal AI content generation
- publishing content creation

The Publishing Agent combines:
- uploaded artwork images
- scraped website context
- multimodal Gemini AI generation

to create context-aware publishing content aligned with the creator’s artistic identity and brand tone.

---

# Human-in-the-Loop Design

The platform intentionally keeps creators involved in the approval process rather than fully automating creative publishing decisions.

This helps preserve:
- artistic identity
- authenticity
- brand consistency
- responsible AI-assisted workflows

---

# Example Outputs

- Instagram captions
- Pinterest descriptions
- Website product listings
- Hashtag generation
- Platform-ready resized artwork images

---

# Future Improvements

- Multi-user support
- AI-based artwork tagging
- Scheduling integrations
- Social media publishing APIs
- Vector database memory for brand consistency
- Advanced recommendation workflows
