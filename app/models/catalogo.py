from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Catalogo(Base):
    __tablename__ = "catalogos"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pendente")
    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    paginas: Mapped[list["Pagina"]] = relationship(back_populates="catalogo", cascade="all, delete-orphan")
    produtos: Mapped[list["Produto"]] = relationship(back_populates="catalogo", cascade="all, delete-orphan")


class Pagina(Base):
    __tablename__ = "paginas"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    catalogo_id: Mapped[int] = mapped_column(ForeignKey("catalogos.id"), index=True)
    numero: Mapped[int] = mapped_column(nullable=False)
    url_imagem: Mapped[str] = mapped_column(String(500), nullable=False)
    texto_extraido: Mapped[str | None] = mapped_column(Text, nullable=True)
    width: Mapped[int | None] = mapped_column(nullable=True)
    height: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    catalogo: Mapped[Catalogo] = relationship(back_populates="paginas")
    hotspots: Mapped[list["Hotspot"]] = relationship(back_populates="pagina", cascade="all, delete-orphan")


class Produto(Base):
    __tablename__ = "produtos"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    catalogo_id: Mapped[int] = mapped_column(ForeignKey("catalogos.id"), index=True)
    codigo: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    preco: Mapped[str | None] = mapped_column(String(80), nullable=True)
    categoria: Mapped[str | None] = mapped_column(String(120), nullable=True)
    codigo_normalizado: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    nome_normalizado: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    catalogo: Mapped[Catalogo] = relationship(back_populates="produtos")
    hotspots: Mapped[list["Hotspot"]] = relationship(back_populates="produto", cascade="all, delete-orphan")


class Hotspot(Base):
    __tablename__ = "hotspots"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    pagina_id: Mapped[int] = mapped_column(ForeignKey("paginas.id"), index=True)
    produto_id: Mapped[int | None] = mapped_column(ForeignKey("produtos.id"), nullable=True, index=True)
    x_percent: Mapped[float] = mapped_column(nullable=False)
    y_percent: Mapped[float] = mapped_column(nullable=False)
    width_percent: Mapped[float | None] = mapped_column(nullable=True)
    height_percent: Mapped[float | None] = mapped_column(nullable=True)
    confianca: Mapped[float] = mapped_column(default=0.0)
    metodo: Mapped[str] = mapped_column(String(50), default="manual")
    status: Mapped[str] = mapped_column(String(50), default="pendente")
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    pagina: Mapped[Pagina] = relationship(back_populates="hotspots")
    produto: Mapped[Produto | None] = relationship(back_populates="hotspots")
