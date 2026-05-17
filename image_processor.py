from PIL import Image
import os


class ImageProcessor:
    def __init__(self):
        self.sizes = {
            "instagram_square": (1080, 1080),
            "instagram_portrait": (1080, 1350),
            "pinterest_vertical": (1000, 1500),
            "website_thumbnail": (1200, 800),
            "website_product": (1600, 1200)
        }

    def crop_to_fill(self, img, target_size):
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

    def process_images(self, image_path, output_folder):
        os.makedirs(output_folder, exist_ok=True)

        img = Image.open(image_path).convert("RGB")
        generated_files = []

        for name, size in self.sizes.items():
            cropped = self.crop_to_fill(img, size)

            output_path = os.path.join(output_folder, f"{name}.jpg")
            cropped.save(output_path, quality=95)

            generated_files.append(output_path)

        return generated_files