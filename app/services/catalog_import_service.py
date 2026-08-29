from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from app.models.catalogo import Catalogo, Hotspot, Pagina, Produto
from app.repositories.catalogo_repository import CatalogoRepository
from app.services.hotspot_service import build_hotspot
from app.services.matching_service import match_product
from app.services.pdf_service import extract_pdf_text_and_blocks, iter_pdf_pages_to_images, upload_page_image_to_r2


def process_catalog_import(catalogo_id: int, pdf_path: str, spreadsheet_path: str | None) -> None:
    from app.database import SessionLocal

    db = SessionLocal()
    catalogo = db.query(Catalogo).filter(Catalogo.id == catalogo_id).first()
    if catalogo is None:
        db.close()
        return

    try:
        pdf_data = extract_pdf_text_and_blocks(Path(pdf_path))
        if not pdf_data["has_extractable_text"]:
            catalogo.status = "configuracao_manual"
            catalogo.observacao = "PDF sem texto extraivel; configuracao manual necessaria"
            db.commit()
            return

        repo = CatalogoRepository(db)
        for page_data, page_image in zip(pdf_data["pages"], iter_pdf_pages_to_images(Path(pdf_path))):
            image_url = upload_page_image_to_r2(page_image, catalogo.id)["public_url"]
            pagina = repo.add_pagina(
                catalogo_id=catalogo.id,
                numero=page_data["page_number"],
                url_imagem=image_url,
                texto_extraido=page_data["text"],
                width=int(page_data["width"]),
                height=int(page_data["height"]),
            )
            for block in page_data["blocks"]:
                hotspot_data = build_hotspot(
                    page_data["width"], page_data["height"], block["x0"], block["y0"],
                    width=block["x1"] - block["x0"], height=block["y1"] - block["y0"],
                )
                repo.add_hotspot(
                    pagina_id=pagina.id,
                    x_percent=hotspot_data["x_percent"],
                    y_percent=hotspot_data["y_percent"],
                    confianca=0.8,
                    metodo="pdf_text_block",
                    status="pendente",
                )

        if spreadsheet_path:
            dataframe = pd.read_excel(spreadsheet_path, engine="openpyxl")
            required = {"codigo", "nome"}
            for _, row in dataframe.iterrows():
                if not required.issubset(row.index):
                    continue
                codigo = row.get("codigo")
                nome = row.get("nome")
                if pd.isna(codigo) or pd.isna(nome):
                    continue
                repo.add_produto(catalogo_id=catalogo.id, codigo=str(codigo), nome=str(nome))

        produtos = [
            {"id": produto.id, "codigo": produto.codigo, "nome": produto.nome}
            for produto in db.query(Produto).filter(Produto.catalogo_id == catalogo.id).all()
        ]
        hotspots = db.query(Hotspot).join(Pagina).filter(Pagina.catalogo_id == catalogo.id).all()
        identificados = 0
        nao_encontrados = 0
        for hotspot in hotspots:
            target = {"codigo": "", "nome": ""}
            if hotspot.pagina.texto_extraido:
                lines = [line.strip() for line in hotspot.pagina.texto_extraido.splitlines() if line.strip()]
                if lines:
                    target["nome"] = lines[0][:120]
            result = match_product(produtos, target)
            if result["product_id"] is None:
                nao_encontrados += 1
                continue
            hotspot.produto_id = result["product_id"]
            hotspot.status = "confirmado"
            hotspot.confianca = 0.9
            identificados += 1

        catalogo.status = "importado"
        catalogo.observacao = f"identificados={identificados}; nao_encontrados={nao_encontrados}"
        db.commit()
    except Exception as exc:
        db.rollback()
        catalogo.status = "erro"
        catalogo.observacao = str(exc)[:1000]
        db.commit()
    finally:
        db.close()
        for path in (pdf_path, spreadsheet_path):
            if path:
                try:
                    os.unlink(path)
                except FileNotFoundError:
                    pass
