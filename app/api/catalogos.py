from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.catalogo import Catalogo, Hotspot, Pagina, Produto
from app.repositories.catalogo_repository import CatalogoRepository
from app.services.hotspot_service import build_hotspot
from app.services.matching_service import match_product
from app.services.pdf_service import (
    extract_pdf_text_and_blocks,
    iter_pdf_pages_to_images,
    upload_page_image_to_r2,
)

router = APIRouter(prefix="/catalogos", tags=["catalogos"])


@router.get("/{catalogo_id}")
def get_catalogo_public(catalogo_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    repo = CatalogoRepository(db)
    catalogo = repo.get_catalogo(catalogo_id)
    if not catalogo:
        raise HTTPException(status_code=404, detail="Catalogo nao encontrado")

    paginas = []
    for pagina in catalogo.paginas:
        hotspots = [
            {
                "id": hotspot.id,
                "x_percent": hotspot.x_percent,
                "y_percent": hotspot.y_percent,
                "status": hotspot.status,
                "produto": {
                    "id": hotspot.produto.id,
                    "nome": hotspot.produto.nome,
                    "codigo": hotspot.produto.codigo,
                    "preco": hotspot.produto.preco,
                } if hotspot.produto else None,
            }
            for hotspot in pagina.hotspots
            if hotspot.status == "confirmado"
        ]
        paginas.append({"id": pagina.id, "numero": pagina.numero, "url_imagem": pagina.url_imagem, "hotspots": hotspots})

    return {
        "id": catalogo.id,
        "titulo": catalogo.titulo,
        "status": catalogo.status,
        "paginas": paginas,
    }


@router.get("/revisao")
def list_pending_hotspots(catalogo_id: int | None = None, db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    repo = CatalogoRepository(db)
    catalogos = db.query(Catalogo).all() if catalogo_id is None else [repo.get_catalogo(catalogo_id)]
    result = []
    for catalogo in catalogos:
        if not catalogo:
            continue
        for hotspot in repo.list_hotspots_pendentes(catalogo.id):
            result.append({
                "id": hotspot.id,
                "catalogo_id": catalogo.id,
                "pagina_id": hotspot.pagina_id,
                "produto_id": hotspot.produto_id,
                "x_percent": hotspot.x_percent,
                "y_percent": hotspot.y_percent,
                "status": hotspot.status,
            })
    return result


@router.patch("/hotspots/{hotspot_id}")
def update_hotspot(hotspot_id: int, payload: dict[str, Any], db: Session = Depends(get_db)) -> dict[str, Any]:
    repo = CatalogoRepository(db)
    hotspot = repo.update_hotspot(hotspot_id, **payload)
    if hotspot is None:
        raise HTTPException(status_code=404, detail="Hotspot nao encontrado")
    return {"id": hotspot.id, "status": hotspot.status, "x_percent": hotspot.x_percent, "y_percent": hotspot.y_percent}


@router.post("/importar")
async def importar_catalogo(
    pdf: UploadFile,
    planilha: UploadFile | None = None,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    repo = CatalogoRepository(db)
    catalogo = repo.create_catalogo(titulo=pdf.filename or "Catalogo importado", status="importando")

    pdf_bytes = await pdf.read()
    pdf_data = extract_pdf_text_and_blocks(pdf_bytes)
    if not pdf_data["has_extractable_text"]:
        catalogo.status = "configuracao_manual"
        catalogo.observacao = "PDF sem texto extraivel; configuracao manual necessaria"
        db.commit()
        return {
            "catalogo_id": catalogo.id,
            "status": catalogo.status,
            "resumo": {"total": 0, "identificados": 0, "precisa_revisao": 0, "nao_encontrados": 0},
            "message": "PDF sem texto extraivel; configuracao manual necessaria",
        }

    for page_data, page_image in zip(pdf_data["pages"], iter_pdf_pages_to_images(pdf_bytes)):
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
                page_data["width"],
                page_data["height"],
                block["x0"],
                block["y0"],
                width=block["x1"] - block["x0"],
                height=block["y1"] - block["y0"],
            )
            repo.add_hotspot(
                pagina_id=pagina.id,
                x_percent=hotspot_data["x_percent"],
                y_percent=hotspot_data["y_percent"],
                confianca=0.8,
                metodo="pdf_text_block",
                status="pendente",
            )

    if planilha is not None:
        planilha_bytes = await planilha.read()
        import pandas as pd
        from io import BytesIO

        dataframe = pd.read_excel(BytesIO(planilha_bytes), engine="openpyxl")
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
    precisa_revisao = 0
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
            hotspot.status = "pendente"
            continue
        hotspot.produto_id = result["product_id"]
        hotspot.status = "confirmado"
        hotspot.confianca = 0.9
        identificados += 1

    catalogo.status = "importado"
    db.commit()
    return {
        "catalogo_id": catalogo.id,
        "status": catalogo.status,
        "resumo": {
            "total": len(hotspots),
            "identificados": identificados,
            "precisa_revisao": precisa_revisao,
            "nao_encontrados": nao_encontrados,
        },
    }
