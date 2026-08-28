"""create catalog models

Revision ID: 20240828_000001
Revises: 
Create Date: 2024-08-28 00:00:01.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20240828_000001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "catalogos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("titulo", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("observacao", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_catalogos_id"), "catalogos", ["id"], unique=False)

    op.create_table(
        "paginas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("catalogo_id", sa.Integer(), nullable=False),
        sa.Column("numero", sa.Integer(), nullable=False),
        sa.Column("url_imagem", sa.String(length=500), nullable=False),
        sa.Column("texto_extraido", sa.Text(), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["catalogo_id"], ["catalogos.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_paginas_catalogo_id"), "paginas", ["catalogo_id"], unique=False)
    op.create_index(op.f("ix_paginas_id"), "paginas", ["id"], unique=False)

    op.create_table(
        "produtos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("catalogo_id", sa.Integer(), nullable=False),
        sa.Column("codigo", sa.String(length=120), nullable=True),
        sa.Column("nome", sa.String(length=255), nullable=False),
        sa.Column("preco", sa.String(length=80), nullable=True),
        sa.Column("categoria", sa.String(length=120), nullable=True),
        sa.Column("codigo_normalizado", sa.String(length=120), nullable=True),
        sa.Column("nome_normalizado", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["catalogo_id"], ["catalogos.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_produtos_catalogo_id"), "produtos", ["catalogo_id"], unique=False)
    op.create_index(op.f("ix_produtos_codigo"), "produtos", ["codigo"], unique=False)
    op.create_index(op.f("ix_produtos_codigo_normalizado"), "produtos", ["codigo_normalizado"], unique=False)
    op.create_index(op.f("ix_produtos_id"), "produtos", ["id"], unique=False)

    op.create_table(
        "hotspots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("pagina_id", sa.Integer(), nullable=False),
        sa.Column("produto_id", sa.Integer(), nullable=True),
        sa.Column("x_percent", sa.Float(), nullable=False),
        sa.Column("y_percent", sa.Float(), nullable=False),
        sa.Column("width_percent", sa.Float(), nullable=True),
        sa.Column("height_percent", sa.Float(), nullable=True),
        sa.Column("confianca", sa.Float(), nullable=False),
        sa.Column("metodo", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["pagina_id"], ["paginas.id"]),
        sa.ForeignKeyConstraint(["produto_id"], ["produtos.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_hotspots_id"), "hotspots", ["id"], unique=False)
    op.create_index(op.f("ix_hotspots_pagina_id"), "hotspots", ["pagina_id"], unique=False)
    op.create_index(op.f("ix_hotspots_produto_id"), "hotspots", ["produto_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_hotspots_produto_id"), table_name="hotspots")
    op.drop_index(op.f("ix_hotspots_pagina_id"), table_name="hotspots")
    op.drop_index(op.f("ix_hotspots_id"), table_name="hotspots")
    op.drop_table("hotspots")

    op.drop_index(op.f("ix_produtos_codigo_normalizado"), table_name="produtos")
    op.drop_index(op.f("ix_produtos_codigo"), table_name="produtos")
    op.drop_index(op.f("ix_produtos_catalogo_id"), table_name="produtos")
    op.drop_index(op.f("ix_produtos_id"), table_name="produtos")
    op.drop_table("produtos")

    op.drop_index(op.f("ix_paginas_catalogo_id"), table_name="paginas")
    op.drop_index(op.f("ix_paginas_id"), table_name="paginas")
    op.drop_table("paginas")

    op.drop_index(op.f("ix_catalogos_id"), table_name="catalogos")
    op.drop_table("catalogos")
