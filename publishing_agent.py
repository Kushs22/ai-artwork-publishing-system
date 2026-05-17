import os
import json
import requests
from bs4 import BeautifulSoup
from PIL import Image
import google.generativeai as genai
from image_processor import ImageProcessor


class PublishingAgent:

    def __init__(self, api_key=None):
        self.api_key = api_key
        self.image_processor = ImageProcessor()

        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel("gemini-2.0-flash")
        else:
            self.model = None

    def scrape_website_context(self, website_url):
        if not website_url:
            return "No website provided."

        try:
            response = requests.get(
                website_url,
                timeout=10,
                headers={"User-Agent": "Mozilla/5.0"}
            )

            soup = BeautifulSoup(response.text, "html.parser")

            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()

            text = soup.get_text(separator=" ")
            clean_text = " ".join(text.split())

            return clean_text[:4000]

        except Exception as e:
            return f"Could not read website: {str(e)}"

    def fallback_content(self, image_path, website_context):
        artwork_name = os.path.splitext(os.path.basename(image_path))[0]

        return f"""
ARTWORK ANALYSIS:
This artwork has a calm, organic and visually textured appearance. It is suitable for botanical-inspired art, interior styling and reflective social media storytelling.

BRAND TONE INFERENCE:
Based on the website context, the brand should feel calm, artistic, minimal, nature-inspired and premium.

INSTAGRAM CAPTION:
Soft botanical textures, quiet detail, and a calm visual rhythm — created for spaces that invite stillness.

LONG INSTAGRAM CAPTION:
A piece shaped by organic pattern, texture and quiet visual movement. This artwork brings a calm botanical presence into interior spaces, offering a subtle balance between nature-inspired detail and contemporary stillness.

PINTEREST DESCRIPTION:
Nature-inspired botanical artwork with a calm, minimal and elegant visual style. Ideal for gallery walls, peaceful interiors, art print collections and refined home decor.

WEBSITE PRODUCT LISTING:
{artwork_name} is a nature-inspired artwork designed for interiors that value softness, detail and organic form. With its calm visual language and botanical texture, it brings a reflective and elegant presence to any space.

HASHTAGS:
#botanicalart #natureinspiredart #artprint #wallart #interiordecor #gallerywall #minimalart #contemporaryart #botanicalprint #homedecor #independentartist #slowmade #creativebusiness #natureart #artistsoninstagram
"""

    def generate_content_pack(self, image_path, brand_context=None):
        if brand_context is None:
            brand_context = {}

        website = brand_context.get("website", "")
        website_context = self.scrape_website_context(website)

        if self.model is None:
            return self.fallback_content(image_path, website_context)

        image = Image.open(image_path)

        prompt = f"""
You are an expert art brand strategist and social media copywriter.

Analyse BOTH:
1. The uploaded artwork image
2. The website brand identity text below

WEBSITE CONTEXT:
{website_context}

TASK:
Generate unique content for this specific uploaded image.
Do not use generic or repeated captions.

Return EXACTLY in this structure:

ARTWORK ANALYSIS:
Describe the visible subject, colours, texture, mood and composition.

BRAND TONE INFERENCE:
Infer the tone from the website in 3-5 bullet points.

INSTAGRAM CAPTION:
Write a short poetic caption specific to the image.

LONG INSTAGRAM CAPTION:
Write a longer storytelling caption matching the website tone.

PINTEREST DESCRIPTION:
Write an SEO-friendly artistic description.

WEBSITE PRODUCT LISTING:
Write a premium product description suitable for an art print page.

HASHTAGS:
Generate 15 relevant hashtags.

Rules:
- Match the website tone.
- Use visible image details.
- Avoid generic AI language.
- Avoid loud influencer style.
- Do not invent personal backstory.
"""

        try:
            response = self.model.generate_content([prompt, image])
            return response.text

        except Exception as e:
            return self.fallback_content(image_path, website_context) + f"""

NOTE:
AI generation failed, so fallback content was used.
Error: {str(e)}
"""

    def process_artwork(self, image_path, brand_context=None):
        artwork_name = os.path.splitext(os.path.basename(image_path))[0]
        safe_name = artwork_name.lower().replace(" ", "_")

        timestamp = str(int(__import__("time").time()))

        output_folder = os.path.join(
            "outputs",
            f"{safe_name}_{timestamp}"
        )

        os.makedirs(output_folder, exist_ok=True)

        generated_images = self.image_processor.process_images(
            image_path,
            output_folder
        )

        generated_content = self.generate_content_pack(
            image_path,
            brand_context
        )

        content_file = os.path.join(output_folder, "generated_content.txt")

        with open(content_file, "w", encoding="utf-8") as f:
            f.write(generated_content)

        original_copy_path = os.path.join(
            output_folder,
            os.path.basename(image_path)
        )

        with open(image_path, "rb") as src:
            with open(original_copy_path, "wb") as dst:
                dst.write(src.read())

        result = {
            "output_folder": output_folder,
            "original_copy": original_copy_path,
            "generated_images": generated_images,
            "content_file": content_file
        }

        result_file = os.path.join(output_folder, "result.json")

        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=4)

        return result


