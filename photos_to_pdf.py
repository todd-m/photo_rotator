import argparse
import io
import sys
from pathlib import Path

import pillow_heif
from PIL import Image, ImageOps

pillow_heif.register_heif_opener()
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

# Page dimensions in points (72 pt/in); letter = 612 x 792 pt
PAGE_W, PAGE_H = letter
MARGIN_PT = 10 / 150 * 72  # 10 px at 150 DPI → points


def fit_within(img_w, img_h, slot_w, slot_h):
    """Return (w, h) scaled to fit inside slot, preserving aspect ratio."""
    scale = min(slot_w / img_w, slot_h / img_h, 1.0)
    return img_w * scale, img_h * scale


def draw_image_in_slot(c, img_path, slot_x, slot_y, slot_w, slot_h):
    """Open image, scale to fit slot, center it, draw onto canvas."""
    with Image.open(img_path) as img:
        img = ImageOps.exif_transpose(img.convert("RGB"))
        draw_w, draw_h = fit_within(img.width, img.height, slot_w, slot_h)

        # Center within slot
        x = slot_x + (slot_w - draw_w) / 2
        y = slot_y + (slot_h - draw_h) / 2

        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)
        c.drawImage(ImageReader(buf), x, y, width=draw_w, height=draw_h)


def build_pdf(image_paths, output_path):
    slot_h = PAGE_H / 2
    slot_w = PAGE_W

    # Inner slot area after margin
    inner_w = slot_w - 2 * MARGIN_PT
    inner_h = slot_h - 2 * MARGIN_PT

    c = canvas.Canvas(str(output_path), pagesize=letter)

    for i, img_path in enumerate(image_paths):
        slot_index = i % 2  # 0 = top, 1 = bottom

        if slot_index == 0 and i > 0:
            c.showPage()

        # ReportLab y=0 is bottom-left; top slot starts at PAGE_H/2
        slot_y_origin = PAGE_H / 2 if slot_index == 0 else 0

        draw_image_in_slot(
            c,
            img_path,
            slot_x=MARGIN_PT,
            slot_y=slot_y_origin + MARGIN_PT,
            slot_w=inner_w,
            slot_h=inner_h,
        )

    c.save()


def main():
    parser = argparse.ArgumentParser(description="Combine JPG images into a PDF, two per page.")
    parser.add_argument("input_dir", help="Directory containing JPG images")
    parser.add_argument("output_pdf", help="Output PDF file path")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    if not input_dir.is_dir():
        print(f"Error: '{input_dir}' is not a directory.", file=sys.stderr)
        sys.exit(1)

    image_paths = sorted(
        p for p in input_dir.iterdir()
        if p.suffix.lower() in {".jpg", ".jpeg", ".heic"}
    )

    if not image_paths:
        print("No JPG images found.", file=sys.stderr)
        sys.exit(1)

    build_pdf(image_paths, args.output_pdf)
    print(f"Processed {len(image_paths)} image(s) → {args.output_pdf}")


if __name__ == "__main__":
    main()
