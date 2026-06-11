"""Tests for photos_to_pdf.

Style: real artifacts where practical — real JPEG/HEIC files built with PIL,
real PDFs inspected with pypdf. The canvas is mocked only for geometry
assertions on draw_image_in_slot.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PIL import Image
from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from photos_to_pdf import build_pdf, draw_image_in_slot, fit_within, main


def make_jpeg(path, size=(40, 20), color=(200, 30, 30), exif_orientation=None):
    img = Image.new("RGB", size, color)
    kwargs = {}
    if exif_orientation is not None:
        exif = img.getexif()
        exif[274] = exif_orientation  # 274 = Orientation tag
        kwargs["exif"] = exif
    img.save(path, "JPEG", **kwargs)
    return path


# ---------------------------------------------------------------------------
# fit_within
# ---------------------------------------------------------------------------


class TestFitWithin:
    def test_downscales_to_fit(self):
        assert fit_within(1000, 500, 100, 100) == (100, 50)

    def test_never_upscales(self):
        assert fit_within(40, 20, 200, 200) == (40, 20)

    def test_exact_fit_unchanged(self):
        assert fit_within(100, 50, 100, 50) == (100, 50)

    def test_preserves_aspect_ratio(self):
        w, h = fit_within(300, 100, 150, 150)
        assert w / h == pytest.approx(3.0)

    def test_tall_image_constrained_by_height(self):
        w, h = fit_within(100, 400, 200, 200)
        assert (w, h) == (50, 200)


# ---------------------------------------------------------------------------
# draw_image_in_slot
# ---------------------------------------------------------------------------


class TestDrawImageInSlot:
    def test_centers_small_image_in_slot(self, tmp_path):
        img_path = make_jpeg(tmp_path / "a.jpg", size=(40, 20))
        c = MagicMock()

        draw_image_in_slot(c, img_path, slot_x=10, slot_y=10, slot_w=200, slot_h=200)

        args = c.drawImage.call_args
        assert args.args[1] == 90  # 10 + (200 - 40) / 2
        assert args.args[2] == 100  # 10 + (200 - 20) / 2
        assert args.kwargs["width"] == 40
        assert args.kwargs["height"] == 20

    def test_downscales_large_image(self, tmp_path):
        img_path = make_jpeg(tmp_path / "a.jpg", size=(400, 200))
        c = MagicMock()

        draw_image_in_slot(c, img_path, slot_x=0, slot_y=0, slot_w=100, slot_h=100)

        args = c.drawImage.call_args
        assert args.kwargs["width"] == 100
        assert args.kwargs["height"] == 50

    def test_exif_rotation_is_applied(self, tmp_path):
        """Orientation 6 (90° rotation) swaps the drawn dimensions."""
        img_path = make_jpeg(tmp_path / "a.jpg", size=(40, 20), exif_orientation=6)
        c = MagicMock()

        draw_image_in_slot(c, img_path, slot_x=0, slot_y=0, slot_w=200, slot_h=200)

        args = c.drawImage.call_args
        assert args.kwargs["width"] == 20
        assert args.kwargs["height"] == 40


# ---------------------------------------------------------------------------
# build_pdf
# ---------------------------------------------------------------------------


class TestBuildPdf:
    def _build(self, tmp_path, n_images):
        # Distinct colors per image — reportlab dedupes identical images into
        # one shared XObject, which would skew the per-page image counts.
        paths = [
            make_jpeg(tmp_path / f"img{i}.jpg", color=(40 * i + 10, 30, 30))
            for i in range(n_images)
        ]
        out = tmp_path / "out.pdf"
        build_pdf(paths, out)
        return PdfReader(out)

    def test_single_image_single_page(self, tmp_path):
        reader = self._build(tmp_path, 1)
        assert len(reader.pages) == 1
        assert len(reader.pages[0].images) == 1

    def test_two_images_share_one_page(self, tmp_path):
        reader = self._build(tmp_path, 2)
        assert len(reader.pages) == 1
        assert len(reader.pages[0].images) == 2

    def test_three_images_overflow_to_second_page(self, tmp_path):
        reader = self._build(tmp_path, 3)
        assert len(reader.pages) == 2
        assert len(reader.pages[0].images) == 2
        assert len(reader.pages[1].images) == 1

    def test_four_images_fill_two_pages(self, tmp_path):
        reader = self._build(tmp_path, 4)
        assert len(reader.pages) == 2
        assert len(reader.pages[1].images) == 2

    def test_pages_are_letter_sized(self, tmp_path):
        reader = self._build(tmp_path, 1)
        box = reader.pages[0].mediabox
        assert float(box.width) == 612
        assert float(box.height) == 792

    def test_heic_input(self, tmp_path):
        """HEIC files decode via pillow-heif and land in the PDF."""
        heic = tmp_path / "photo.heic"
        Image.new("RGB", (40, 20), (10, 120, 40)).save(heic, "HEIF")
        out = tmp_path / "out.pdf"

        build_pdf([heic], out)

        reader = PdfReader(out)
        assert len(reader.pages) == 1
        assert len(reader.pages[0].images) == 1


# ---------------------------------------------------------------------------
# main (CLI)
# ---------------------------------------------------------------------------


class TestMain:
    def _run(self, monkeypatch, *argv):
        monkeypatch.setattr(sys, "argv", ["photos_to_pdf.py", *argv])
        main()

    def test_missing_directory_exits_1(self, monkeypatch, tmp_path, capsys):
        with pytest.raises(SystemExit) as exc:
            self._run(monkeypatch, str(tmp_path / "nope"), str(tmp_path / "out.pdf"))
        assert exc.value.code == 1
        assert "is not a directory" in capsys.readouterr().err

    def test_empty_directory_exits_1(self, monkeypatch, tmp_path, capsys):
        with pytest.raises(SystemExit) as exc:
            self._run(monkeypatch, str(tmp_path), str(tmp_path / "out.pdf"))
        assert exc.value.code == 1
        assert "No JPG images found" in capsys.readouterr().err

    def test_processes_images_and_reports_count(self, monkeypatch, tmp_path, capsys):
        make_jpeg(tmp_path / "a.jpg")
        make_jpeg(tmp_path / "b.jpg")
        out = tmp_path / "out.pdf"

        self._run(monkeypatch, str(tmp_path), str(out))

        assert out.exists()
        assert "Processed 2 image(s)" in capsys.readouterr().out

    def test_ignores_other_extensions(self, monkeypatch, tmp_path, capsys):
        make_jpeg(tmp_path / "a.jpg")
        Image.new("RGB", (10, 10)).save(tmp_path / "b.png", "PNG")
        (tmp_path / "notes.txt").write_text("not an image")

        self._run(monkeypatch, str(tmp_path), str(tmp_path / "out.pdf"))

        assert "Processed 1 image(s)" in capsys.readouterr().out

    def test_accepts_jpeg_and_heic_extensions(self, monkeypatch, tmp_path):
        captured = {}
        monkeypatch.setattr(
            "photos_to_pdf.build_pdf",
            lambda paths, out: captured.setdefault("paths", list(paths)),
        )
        make_jpeg(tmp_path / "a.jpeg")
        make_jpeg(tmp_path / "b.JPG")  # uppercase suffix
        Image.new("RGB", (10, 10)).save(tmp_path / "c.heic", "HEIF")

        self._run(monkeypatch, str(tmp_path), str(tmp_path / "out.pdf"))

        assert len(captured["paths"]) == 3

    def test_images_processed_in_alphabetical_order(self, monkeypatch, tmp_path):
        captured = {}
        monkeypatch.setattr(
            "photos_to_pdf.build_pdf",
            lambda paths, out: captured.setdefault("paths", list(paths)),
        )
        make_jpeg(tmp_path / "b.jpg")
        make_jpeg(tmp_path / "a.jpg")
        make_jpeg(tmp_path / "c.jpg")

        self._run(monkeypatch, str(tmp_path), str(tmp_path / "out.pdf"))

        assert [p.name for p in captured["paths"]] == ["a.jpg", "b.jpg", "c.jpg"]
