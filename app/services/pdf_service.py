from __future__ import annotations

import uuid
from typing import Any

import fitz

from app.config import settings
from app.services.r2_service import R2Storage


def _build_object_key(prefix: str, file_name: str) -> str:
    return f"{prefix.rstrip('/')}/{file_name}".lstrip("/")


def upload_page_image_to_r2(page_image: dict[str, Any], catalogo_id: int, prefix: str = "catalogos") -> dict[str, Any]:
    if not settings.r2_bucket or not settings.r2_access_key_id or not settings.r2_secret_access_key:
        return {
            "public_url": f"/images/{catalogo_id}/{page_image['image_name']}",
            "presigned_url": None,
        }

    try:
        storage = R2Storage()
        key = _build_object_key(prefix, f"catalogo_{catalogo_id}/{page_image['image_name']}")
        public_url = storage.upload_bytes(key=key, data=page_image["image_bytes"], content_type="image/png")
        presigned_url = storage.generate_presigned_url(key, expires_seconds=3600)
        return {"public_url": public_url, "presigned_url": presigned_url}
    except ValueError:
        return {
            "public_url": f"/images/{catalogo_id}/{page_image['image_name']}",
            "presigned_url": None,
        }


def extract_pdf_text_and_blocks(pdf_bytes: bytes) -> dict[str, Any]:
    try:
        document = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:  # pragma: no cover - defensive path in real imports
        return {"pages": [], "has_extractable_text": False, "error": str(exc)}

    try:
        pages: list[dict[str, Any]] = []
        has_text = False

        for page_number in range(document.page_count):
            page = document[page_number]
            blocks = page.get_text("blocks")
            page_text = "\n".join(block[4].strip() for block in blocks if block[4].strip())
            if page_text.strip():
                has_text = True
            pages.append(
                {
                    "page_number": page_number + 1,
                    "width": float(page.rect.width),
                    "height": float(page.rect.height),
                    "text": page_text,
                    "blocks": [
                        {
                            "text": block[4].strip(),
                            "x0": float(block[0]),
                            "y0": float(block[1]),
                            "x1": float(block[2]),
                            "y1": float(block[3]),
                        }
                        for block in blocks
                        if block[4].strip()
                    ],
                }
            )

        return {"pages": pages, "has_extractable_text": has_text}
    except Exception as exc:  # pragma: no cover - defensive path in real imports
        return {"pages": [], "has_extractable_text": False, "error": str(exc)}
    finally:
        document.close()


def iter_pdf_pages_to_images(pdf_bytes: bytes):
    try:
        document = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception:
        return

    try:
        for page_number in range(document.page_count):
            page = document[page_number]
            matrix = fitz.Matrix(2, 2)
            pix = page.get_pixmap(matrix=matrix)
            image_bytes = pix.tobytes("png")
            yield {
                "page_number": page_number + 1,
                "width": float(page.rect.width),
                "height": float(page.rect.height),
                "image_bytes": image_bytes,
                "image_name": f"page_{page_number + 1}.png",
            }
    except Exception:
        return
    finally:
        document.close()


def render_pdf_pages_to_images(pdf_bytes: bytes) -> list[dict[str, Any]]:
    return list(iter_pdf_pages_to_images(pdf_bytes))
