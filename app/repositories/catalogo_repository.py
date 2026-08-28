from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.catalogo import Catalogo, Hotspot, Pagina, Produto


class CatalogoRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_catalogo(self, titulo: str, status: str = "pendente", observacao: str | None = None) -> Catalogo:
        catalogo = Catalogo(titulo=titulo, status=status, observacao=observacao)
        self.db.add(catalogo)
        self.db.commit()
        self.db.refresh(catalogo)
        return catalogo

    def add_pagina(self, catalogo_id: int, numero: int, url_imagem: str, texto_extraido: str | None = None, width: int | None = None, height: int | None = None) -> Pagina:
        pagina = Pagina(
            catalogo_id=catalogo_id,
            numero=numero,
            url_imagem=url_imagem,
            texto_extraido=texto_extraido,
            width=width,
            height=height,
        )
        self.db.add(pagina)
        self.db.commit()
        self.db.refresh(pagina)
        return pagina

    def add_produto(self, catalogo_id: int, codigo: str | None, nome: str, preco: str | None = None, categoria: str | None = None) -> Produto:
        produto = Produto(catalogo_id=catalogo_id, codigo=codigo, nome=nome, preco=preco, categoria=categoria)
        self.db.add(produto)
        self.db.commit()
        self.db.refresh(produto)
        return produto

    def add_hotspot(self, pagina_id: int, x_percent: float, y_percent: float, produto_id: int | None = None, confianca: float = 0.0, metodo: str = "manual", status: str = "pendente") -> Hotspot:
        hotspot = Hotspot(
            pagina_id=pagina_id,
            produto_id=produto_id,
            x_percent=x_percent,
            y_percent=y_percent,
            confianca=confianca,
            metodo=metodo,
            status=status,
        )
        self.db.add(hotspot)
        self.db.commit()
        self.db.refresh(hotspot)
        return hotspot

    def get_catalogo(self, catalogo_id: int) -> Catalogo | None:
        return self.db.query(Catalogo).filter(Catalogo.id == catalogo_id).first()

    def list_hotspots_pendentes(self, catalogo_id: int) -> list[Hotspot]:
        return (
            self.db.query(Hotspot)
            .join(Pagina)
            .filter(Pagina.catalogo_id == catalogo_id)
            .filter(Hotspot.status == "pendente")
            .all()
        )

    def update_hotspot(self, hotspot_id: int, **kwargs: Any) -> Hotspot | None:
        hotspot = self.db.query(Hotspot).filter(Hotspot.id == hotspot_id).first()
        if hotspot is None:
            return None
        for key, value in kwargs.items():
            if hasattr(hotspot, key):
                setattr(hotspot, key, value)
        self.db.commit()
        self.db.refresh(hotspot)
        return hotspot
