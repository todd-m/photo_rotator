# CLAUDE.md

## Recent changes

No git history yet. Script was written fresh this session:

- Created `photos_to_pdf.py` — two images per page, letter size, alphabetical order
- Added EXIF transpose (`ImageOps.exif_transpose`) for correct phone photo orientation
- Added HEIC support via `pillow-heif` with `register_heif_opener()`
- Added `.jpeg` extension alongside `.jpg` and `.heic` in file filter

## Planned / in-progress

Nothing currently planned.

## Conventions / gotchas

- ReportLab y=0 is **bottom-left**; top slot origin is `PAGE_H / 2`, bottom slot is `0`
- Margin is defined as 10px at 150 DPI, converted to points at module level (`MARGIN_PT`)
- `pillow_heif.register_heif_opener()` must be called before any `Image.open()` on HEIC files
- File error message still says "No JPG images found" even though HEIC/JPEG are also supported — minor wording issue
