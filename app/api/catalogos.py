from __future__ import annotations

import shutil
import tempfile
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.catalogo import Catalogo, Hotspot, Pagina, Produto
from app.repositories.catalogo_repository import CatalogoRepository
from app.services.catalog_import_service import process_catalog_import

router = APIRouter(prefix="/catalogos", tags=["catalogos"])


@router.get("/{catalogo_id}/status")
def get_catalogo_status(catalogo_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    catalogo = db.query(Catalogo).filter(Catalogo.id == catalogo_id).first()
    if not catalogo:
        raise HTTPException(status_code=404, detail="Catalogo nao encontrado")
    return {"catalogo_id": catalogo.id, "status": catalogo.status, "observacao": catalogo.observacao}


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


@router.post("/importar", status_code=status.HTTP_202_ACCEPTED)
async def importar_catalogo(
    pdf: UploadFile,
    background_tasks: BackgroundTasks,
    planilha: UploadFile | None = None,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    repo = CatalogoRepository(db)
    catalogo = repo.create_catalogo(titulo=pdf.filename or "Catalogo importado", status="processando")
    pdf_file = tempfile.NamedTemporaryFile(prefix="catalogo_", suffix=".pdf", delete=False)
    try:
        shutil.copyfileobj(pdf.file, pdf_file)
        pdf_file.close()
        spreadsheet_path = None
        if planilha is not None:
            sheet_file = tempfile.NamedTemporaryFile(prefix="catalogo_", suffix=".xlsx", delete=False)
            shutil.copyfileobj(planilha.file, sheet_file)
            sheet_file.close()
            spreadsheet_path = sheet_file.name
        background_tasks.add_task(process_catalog_import, catalogo.id, pdf_file.name, spreadsheet_path)
    except Exception:
        pdf_file.close()
        raise

    return {"catalogo_id": catalogo.id, "status": catalogo.status, "message": "Importacao iniciada"}
