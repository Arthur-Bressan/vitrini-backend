import pytest

from app.services.matching_service import match_product, normalize_code, normalize_name


@pytest.mark.parametrize(
    "products, target, expected_key",
    [
        ([{"codigo": "A-001", "nome": "Produto A"}], {"codigo": "A-001", "nome": "Produto A"}, "A-001"),
        ([{"codigo": "A-001", "nome": "Produto A"}], {"codigo": "a001", "nome": "Produto A"}, "A-001"),
        ([{"codigo": "B-999", "nome": "Café Premium"}], {"codigo": "X", "nome": "Café Premium"}, "B-999"),
        ([{"codigo": "C-100", "nome": "Bateria 12V"}], {"codigo": "X", "nome": "Bateria 12 V"}, "C-100"),
    ],
)
def test_match_product_hierarchy(products, target, expected_key):
    result = match_product(products, target)
    assert result["product_id"] == expected_key


def test_match_product_not_found():
    products = [{"codigo": "A-001", "nome": "Produto A"}]
    target = {"codigo": "Z-999", "nome": "Qualquer coisa"}
    result = match_product(products, target)
    assert result["product_id"] is None
    assert result["match_type"] == "not_found"


def test_normalize_code_and_name():
    assert normalize_code("A-001") == "a001"
    assert normalize_name(" Café   Premium ") == "cafe premium"
