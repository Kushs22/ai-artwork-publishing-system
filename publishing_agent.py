import json
import os
import time
from typing import Any, Optional

import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
from PIL import Image

from brand_voice import (
    build_brand_context_block,
    crops_for_platforms,
    load_brand_profile,
    load_user_examples,
)
from image_processor import ImageProcessor


class PublishingAgent:

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.image_processor = ImageProcessor()

        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel("gemini-2.0-flash")
        else:
            self.model = None

    def scrape_website_context(self, website_url: str) -> str:
        if not website_url:
            return "No website provided."

        try:
            response = requests.get(
                website_url,
                timeout=10,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            soup = BeautifulSoup(response.text, "html.parser")

            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()

            text = soup.get_text(separator=" ")
            clean_text = " ".join(text.split())
            return clean_text[:4000]

        except Exception as e:
            return f"Could not read website: {str(e)}"

    def _fallback_content(self, image_path: str, brand_context: dict) -> dict[str, Any]:
        artwork_name = os.path.splitext(os.path.basename(image_path))[0]
        meta = brand_context.get("metadata", {})
        title = meta.get("title") or artwork_name

        return {
            "artwork_analysis": (
                "Calm, organic visual texture suitable for botanical-inspired art "
                "and reflective social storytelling."
            ),
            "brand_tone": [
                "Calm and artistic",
                "Nature-inspired",
                "Minimal and premium",
            ],
            "instagram_caption": (
                "Soft botanical textures and quiet detail — created for spaces "
                "that invite stillness."
            ),
            "instagram_long_caption": (
                "A piece shaped by organic pattern and quiet visual movement. "
                "Designed for interiors that value softness and botanical form."
            ),
            "pinterest_description": (
                "Nature-inspired botanical artwork with a calm, minimal style. "
                "Ideal for gallery walls and refined home decor."
            ),
            "website_product_listing": (
                f"{title} is a nature-inspired artwork for interiors that value "
                "softness, detail and organic form."
            ),
            "gelato_product_title": title,
            "gelato_product_description": (
                f"Premium art print: {title}. Museum-quality reproduction "
                "suitable for framed wall art and gift collections."
            ),
            "gelato_tags": ["botanical", "nature", "wall art", "print", "minimal"],
            "hashtags": [
                "#botanicalart",
                "#natureinspiredart",
                "#artprint",
                "#wallart",
                "#interiordecor",
                "#gallerywall",
                "#minimalart",
                "#contemporaryart",
                "#homedecor",
                "#independentartist",
            ],
            "platform_notes": {},
        }

    def _build_prompt(
        self,
        website_context: str,
        brand_context: dict,
        revision_notes: Optional[str] = None,
    ) -> str:
        meta = brand_context.get("metadata", {})
        platforms = meta.get("platforms", []) or ["Instagram", "Pinterest", "Website"]
        platforms_str = ", ".join(platforms)

        profile = load_brand_profile()
        user_examples = load_user_examples()
        brand_block = build_brand_context_block(profile, user_examples, meta)

        revision_block = ""
        if revision_notes:
            revision_block = f"""
REVISION REQUEST (address these changes):
{revision_notes}
"""

        platform_rules = """
PLATFORM RULES (content must differ per platform — same artwork, different copy):
- Instagram: Short poetic caption (1-3 lines) + separate longer caption for carousel/story depth.
  Hashtags: 8-15, mix artist + nature + Bristol/bark + decor; match example style.
- Pinterest: Longer descriptive pin text (SEO: botanical art print, wall art, bark art, gift).
  Use keyword phrases; calmer than Instagram, more searchable.
- Squarespace/Website: Premium product listing; title, materials, one-of-a-kind or print options.
- Gelato: Practical POD title, description (sizes, paper, framing, gifts), 5-8 product tags.
"""
        if "Instagram" not in platforms:
            platform_rules += "\n- Omit or minimise Instagram fields if not in target platforms."
        if "Pinterest" not in platforms:
            platform_rules += "\n- Omit or minimise Pinterest fields if not in target platforms."

        return f"""
You are an expert art brand strategist for Roxy Megyesi / Bark & Grain Studio (Bristol).

Analyse BOTH:
1. The uploaded artwork image (colours, texture, subject, mood — this post is UNIQUE)
2. Brand voice + website context below

BRAND VOICE (match example captions — vary wording for THIS image):
{brand_block}

WEBSITE TEXT (roxymegyesi.com):
{website_context[:3500]}

ARTWORK METADATA:
- Title: {meta.get('title', '')}
- Theme: {meta.get('theme', '')}
- Collection: {meta.get('collection', '')}
- Format: {meta.get('format', '')}
- Target platforms: {platforms_str}
{revision_block}
{platform_rules}

TASK:
Generate fresh captions and hashtags for THIS specific upload — not generic templates.
Return valid JSON only (no markdown fences):

{{
  "artwork_analysis": "what you see in the image",
  "brand_tone": ["3-5 tone words"],
  "instagram_caption": "short caption for feed post",
  "instagram_long_caption": "longer caption if needed",
  "pinterest_description": "pin description with SEO keywords",
  "website_product_listing": "Squarespace-style product copy",
  "gelato_product_title": "POD product title",
  "gelato_product_description": "Gelato listing body",
  "gelato_tags": ["tag1", "tag2"],
  "hashtags": ["#tag1", "... tailored to this piece and collection"],
  "pinterest_keywords": ["keyword1", "keyword2"],
  "platform_notes": {{
    "instagram": "which crop: square vs portrait",
    "pinterest": "vertical pin tip",
    "squarespace": "listing tip",
    "gelato": "POD tip"
  }}
}}

Rules:
- Captions and hashtags MUST reflect visible details in the image and collection metadata.
- Sound like Bark & Grain: tactile, quiet, nature, intention — never influencer hype.
- Do not invent medical or personal trauma narratives unless clearly supported by metadata.
- Human reviews all copy before posting; do not mention auto-posting.
"""

    def _parse_json_response(self, text: str, fallback: dict) -> dict[str, Any]:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        try:
            data = json.loads(cleaned)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass
        return fallback

    def generate_content_pack(
        self,
        image_path: str,
        brand_context: Optional[dict] = None,
        revision_notes: Optional[str] = None,
    ) -> dict[str, Any]:
        if brand_context is None:
            brand_context = {}

        website = brand_context.get("website") or brand_context.get("metadata", {}).get("website", "")
        website_context = self.scrape_website_context(website)
        fallback = self._fallback_content(image_path, brand_context)

        if self.model is None:
            fallback["_note"] = "No API key — fallback content used."
            return fallback

        image = Image.open(image_path)
        prompt = self._build_prompt(website_context, brand_context, revision_notes)

        try:
            response = self.model.generate_content([prompt, image])
            return self._parse_json_response(response.text, fallback)
        except Exception as e:
            fallback["_note"] = f"AI generation failed: {e}"
            return fallback

    def write_content_json(self, output_folder: str, content: dict[str, Any]) -> str:
        os.makedirs(output_folder, exist_ok=True)
        path = os.path.join(output_folder, "content.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(content, f, indent=2, ensure_ascii=False)

        txt_path = os.path.join(output_folder, "generated_content.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(self._content_to_text(content))
        return path

    def write_platform_checklist(
        self,
        output_folder: str,
        platforms: list[str],
    ) -> str:
        checklist = {
            "platforms": platforms,
            "items": [],
        }
        platform_tasks = {
            "Instagram": [
                "Upload instagram_square or instagram_portrait crop",
                "Paste instagram_caption from content.json",
                "Add hashtags (max 30)",
                "Schedule or post manually",
            ],
            "Pinterest": [
                "Upload pinterest_vertical crop",
                "Paste pinterest_description",
                "Add link to shop/website",
            ],
            "Squarespace": [
                "Create/update product page",
                "Paste website_product_listing",
                "Upload website_product image",
            ],
            "Gelato": [
                "Create product with gelato_product_title",
                "Paste gelato_product_description",
                "Apply gelato_tags",
                "Upload gelato_print crop",
            ],
            "Website": [
                "Update portfolio or shop listing",
                "Paste website_product_listing",
                "Upload website_thumbnail / website_product",
            ],
        }
        for platform in platforms:
            tasks = platform_tasks.get(platform, ["Review content.json for this platform"])
            checklist["items"].append({"platform": platform, "tasks": tasks})

        if not platforms:
            checklist["items"].append({
                "platform": "(none selected)",
                "tasks": ["Select platforms in metadata to generate a tailored checklist"],
            })

        path = os.path.join(output_folder, "platform_checklist.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(checklist, f, indent=2)
        return path

    def _content_to_text(self, content: dict[str, Any]) -> str:
        lines = []
        for key, value in content.items():
            if key.startswith("_"):
                continue
            label = key.replace("_", " ").upper()
            if isinstance(value, list):
                lines.append(f"{label}:\n" + "\n".join(f"- {v}" for v in value))
            elif isinstance(value, dict):
                lines.append(f"{label}:\n" + json.dumps(value, indent=2))
            else:
                lines.append(f"{label}:\n{value}")
            lines.append("")
        return "\n".join(lines)

    def prepare_output_pack(
        self,
        image_path: str,
        brand_context: Optional[dict] = None,
        revision_notes: Optional[str] = None,
        include_crops: bool = False,
    ) -> dict[str, Any]:
        """Create output folder with content.json; crops only if include_crops=True."""
        artwork_name = os.path.splitext(os.path.basename(image_path))[0]
        safe_name = artwork_name.lower().replace(" ", "_")
        timestamp = str(int(time.time()))

        output_folder = os.path.join("outputs", f"{safe_name}_{timestamp}")
        os.makedirs(output_folder, exist_ok=True)

        generated_images = []
        if include_crops:
            meta = (brand_context or {}).get("metadata", {})
            platform_list = meta.get("platforms", [])
            crop_names = crops_for_platforms(platform_list) if platform_list else None
            generated_images = self.image_processor.apply_crops(
                image_path, output_folder, crop_names=crop_names
            )

        content = self.generate_content_pack(image_path, brand_context, revision_notes)
        content_file = self.write_content_json(output_folder, content)

        meta = (brand_context or {}).get("metadata", {})
        self.write_platform_checklist(output_folder, meta.get("platforms", []))

        preview_path = os.path.join(output_folder, "_preview_reference.jpg")
        with open(image_path, "rb") as src:
            with open(preview_path, "wb") as dst:
                dst.write(src.read())

        result = {
            "output_folder": output_folder,
            "preview_reference": preview_path,
            "generated_images": generated_images,
            "content_file": content_file,
            "content": content,
        }

        result_file = os.path.join(output_folder, "result.json")
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(
                {k: v for k, v in result.items() if k != "content"},
                f,
                indent=2,
            )

        return result

    def process_artwork(
        self,
        image_path: str,
        metadata=None,
        revision_notes: str = "",
        apply_crops: bool = False,
    ) -> dict:
        """Compatibility wrapper used by app.py."""
        brand_context = {"website": "", "metadata": {}}
        if metadata is not None:
            meta_dict = metadata.to_dict() if hasattr(metadata, "to_dict") else metadata
            brand_context["metadata"] = meta_dict
            brand_context["website"] = meta_dict.get("website", "")

        result = self.prepare_output_pack(
            image_path,
            brand_context=brand_context,
            revision_notes=revision_notes or None,
            include_crops=apply_crops,
        )

        content = result.get("content", {})
        result["gelato"] = {
            "product_title": content.get("gelato_product_title", ""),
            "product_description": content.get("gelato_product_description", ""),
            "tags": content.get("gelato_tags", []),
        }
        checklist_path = os.path.join(result["output_folder"], "platform_checklist.json")
        if os.path.isfile(checklist_path):
            with open(checklist_path, encoding="utf-8") as f:
                result["platform_checklist"] = json.load(f)
        else:
            result["platform_checklist"] = {"items": []}

        return result
