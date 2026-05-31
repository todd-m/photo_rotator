# photos_to_pdf

Combines a directory of images into a single PDF with two images per page.

## What it does

- Accepts `.jpg`, `.jpeg`, and `.heic` files
- Processes images in alphabetical filename order
- Lays out two images per page, stacked vertically on letter-size pages (8.5×11 in)
- Scales each image to fit its slot while preserving aspect ratio (no cropping, no upscaling)
- Centers each image within its slot with a 10px margin on all sides
- Corrects EXIF rotation automatically (phone photos appear upright)
- Odd number of images: last page has one image in the top slot

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python photos_to_pdf.py /path/to/photos output.pdf
```

Prints a summary on completion: number of images processed and output path.

## Architecture

| Component | Role |
|---|---|
| `main()` | Parses CLI args, globs and sorts image files, validates input |
| `build_pdf()` | Iterates images in pairs, manages ReportLab canvas pages |
| `draw_image_in_slot()` | Opens image, applies EXIF transpose, scales, centers, draws |
| `fit_within()` | Pure function: returns scaled dimensions preserving aspect ratio |

Page geometry is in ReportLab points (72 pt/in). The 10px margin is converted from 150 DPI to points at startup.

## Dependencies

- [Pillow](https://python-pillow.org/) — image open/resize/EXIF correction
- [pillow-heif](https://github.com/bigcat88/pillow_heif) — HEIC format support via Pillow
- [ReportLab](https://www.reportlab.com/) — PDF generation
