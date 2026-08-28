import re
import unicodedata
from typing import Any

from rapidfuzz import fuzz


def normalize_code(value: str | None) -> str:
    if value is None:
        return ""
    value = str(value).strip().upper()
    value = re.sub(r"[^A-Z0-9]", "", value)
    return value.lower()


def normalize_name(value: str | None) -> str:
    if value is None:
        return ""
    value = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def match_product(products: list[dict[str, Any]], target: dict[str, Any]) -> dict[str, Any]:
    if not products:
        return {"product_id": None, "match_type": "not_found"}

    target_code = normalize_code(target.get("codigo"))
    target_name = normalize_name(target.get("nome"))

    raw_target_code = str(target.get("codigo") or "").strip()
    raw_target_name = str(target.get("nome") or "").strip()

    for product in products:
        product_code = str(product.get("codigo") or "").strip()
        if raw_target_code and product_code and product_code.lower() == raw_target_code.lower():
            return {"product_id": product.get("id") or product.get("codigo"), "match_type": "codigo_exato"}

    for product in products:
        product_code = normalize_code(product.get("codigo"))
        if target_code and product_code and product_code == target_code:
            return {"product_id": product.get("id") or product.get("codigo"), "match_type": "codigo_normalizado"}

    if target_name:
        for product in products:
            product_name = normalize_name(product.get("nome"))
            if product_name and product_name == target_name:
                return {"product_id": product.get("id") or product.get("codigo"), "match_type": "nome_exato_normalizado"}

    best_match = None
    best_score = 0
    for product in products:
        product_name = normalize_name(product.get("nome"))
        if not target_name or not product_name:
            continue
        score = fuzz.ratio(target_name, product_name)
        if score > best_score:
            best_score = score
            best_match = product

    if best_match and best_score >= 75:
        return {"product_id": best_match.get("id") or best_match.get("codigo"), "match_type": "nome_similaridade", "score": best_score}

    return {"product_id": None, "match_type": "not_found"}
