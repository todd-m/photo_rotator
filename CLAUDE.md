# CLAUDE.md

## Recent changes

- *(uncommitted)* — Test suite + standards alignment (`~/Projects/standards/STANDARDS.md`): 20 tests in `tests/test_photos_to_pdf.py` (98% coverage; real JPEG/HEIC + pypdf-inspected PDFs, mock canvas only for geometry), `pyproject.toml` (pytest + 80% gate + ruff), `requirements.txt` repinned `~=` (Pillow 10→12 — 11.3 had 7 pip-audit findings, all fixed in 12.2; pillow-heif 0.x→1.x; both verified by the suite) + test/lint deps, standard Makefile, GitHub Actions CI, `.gitignore` expanded. `register_heif_opener()` moved below the import block (was mid-imports, E402). Venv is `.venv` per standards (stale `env/` may linger). Gotcha: reportlab dedupes identical images into one XObject — tests use distinct colors so per-page image counts are meaningful.
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
