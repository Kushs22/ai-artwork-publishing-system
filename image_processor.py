from io import BytesIO
from typing import Optional

from PIL import Image
import os


class ImageProcessor:
    SIZES = {
        "instagram_square": (1080, 1080),
        "instagram_portrait": (1080, 1350),
        "pinterest_vertical": (1000, 1500),
        "website_thumbnail": (1200, 800),
        "website_product": (1600, 1200),
        "gelato_print": (2400, 3000),
    }

    def crop_to_fill(self, img: Image.Image, target_size: tuple[int, int]) -> Image.Image:
        target_w, target_h = target_size
        img_w, img_h = img.size

        target_ratio = target_w / target_h
        img_ratio = img_w / img_h

        if img_ratio > target_ratio:
            new_w = int(img_h * target_ratio)
            left = (img_w - new_w) // 2
            img = img.crop((left, 0, left + new_w, img_h))
        else:
            new_h = int(img_w / target_ratio)
            top = (img_h - new_h) // 2
            img = img.crop((0, top, img_w, top + new_h))

        return img.resize(target_size, Image.LANCZOS)

    def preview_crops(
        self,
        image_path: str,
        sizes: Optional[dict[str, tuple[int, int]]] = None,
        crop_names: Optional[list[str]] = None,
    ) -> dict[str, Image.Image]:
        """Return in-memory crop previews — does not write files."""
        img = Image.open(image_path).convert("RGB")
        size_map = sizes or self.SIZES
        if crop_names:
            size_map = {k: v for k, v in size_map.items() if k in crop_names}
        return {name: self.crop_to_fill(img.copy(), size) for name, size in size_map.items()}

    def preview_to_bytes(self, previews: dict[str, Image.Image]) -> dict[str, bytes]:
        result = {}
        for name, img in previews.items():
            buf = BytesIO()
            img.save(buf, format="JPEG", quality=90)
            result[name] = buf.getvalue()
        return result

    def apply_crops(
        self,
        image_path: str,
        output_folder: str,
        sizes: Optional[dict[str, tuple[int, int]]] = None,
        crop_names: Optional[list[str]] = None,
    ) -> list[str]:
        """Write cropped files to output_folder. Optional crop_names limits exports."""
        os.makedirs(output_folder, exist_ok=True)
        previews = self.preview_crops(image_path, sizes)
        if crop_names:
            previews = {k: v for k, v in previews.items() if k in crop_names}
        generated_files = []

        for name, cropped in previews.items():
            output_path = os.path.join(output_folder, f"{name}.jpg")
            cropped.save(output_path, quality=95)
            generated_files.append(output_path)

        return generated_files
