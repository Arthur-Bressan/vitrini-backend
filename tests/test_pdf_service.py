import io

import fitz

from app.services.pdf_service import extract_pdf_text_and_blocks, render_pdf_pages_to_images


def _make_pdf_bytes(text: str | None = None) -> bytes:
    document = fitz.open()
    page = document.new_page()
    if text:
        page.insert_text((72, 72), text)
    stream = io.BytesIO()
    document.save(stream)
    document.close()
    return stream.getvalue()


def test_extract_pdf_text_and_blocks_for_clean_pdf():
    pdf_bytes = _make_pdf_bytes("Café Premium")

    result = extract_pdf_text_and_blocks(pdf_bytes)

    assert result["has_extractable_text"] is True
    assert any("Café Premium" in block["text"] for page_data in result["pages"] for block in page_data["blocks"])


def test_extract_pdf_text_and_blocks_handles_blank_pdf_gracefully():
    pdf_bytes = _make_pdf_bytes()

    result = extract_pdf_text_and_blocks(pdf_bytes)

    assert result["has_extractable_text"] is False
    assert result["pages"]
    assert result["pages"][0]["blocks"] == []


def test_extract_pdf_text_and_blocks_handles_invalid_pdf_bytes():
    result = extract_pdf_text_and_blocks(b"not-a-valid-pdf")

    assert result["has_extractable_text"] is False
    assert result["pages"] == []
    assert "error" in result


def test_render_pdf_pages_to_images_handles_invalid_pdf_bytes():
    result = render_pdf_pages_to_images(b"not-a-valid-pdf")

    assert result == []
