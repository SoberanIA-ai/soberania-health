"""initial — autorizaciones, audit_log, codigos_aseguradora

Revision ID: 0001
Revises:
Create Date: 2026-05-06

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    op.create_table(
        "autorizaciones",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("orden_id", sa.String(100)),
        sa.Column("paciente_id", sa.String(100)),
        sa.Column("paciente_nombre", sa.String(200)),
        sa.Column("medico_id", sa.String(100)),
        sa.Column("medico_nombre", sa.String(200)),
        sa.Column("procedimiento_descripcion", sa.Text),
        sa.Column("procedimiento_cie10", sa.String(20)),
        sa.Column("fecha_solicitud", sa.Date),
        sa.Column("urgencia", sa.String(20), server_default="normal"),
        sa.Column("aseguradora", sa.String(50)),
        sa.Column("poliza_numero", sa.String(100)),
        sa.Column("poliza_tipo", sa.String(50)),
        sa.Column("procedimiento_codigo", sa.String(50)),
        sa.Column("confidence_score", sa.Numeric(5, 4)),
        sa.Column("requiere_autorizacion", sa.Boolean),
        sa.Column("cobertura_verificada", sa.Boolean),
        sa.Column("estado", sa.String(50), server_default="recibido"),
        sa.Column("modo", sa.String(10), server_default="real"),
        sa.Column("solicitud_enviada_at", sa.DateTime(timezone=True)),
        sa.Column("solicitud_referencia", sa.String(100)),
        sa.Column("respuesta_recibida_at", sa.DateTime(timezone=True)),
        sa.Column("numero_autorizacion", sa.String(100)),
        sa.Column("autorizado", sa.Boolean),
        sa.Column("motivo_denegacion", sa.Text),
        sa.Column("hitl_requerido", sa.Boolean, server_default=sa.false()),
        sa.Column("hitl_revisado_at", sa.DateTime(timezone=True)),
        sa.Column("hitl_revisor", sa.String(100)),
        sa.Column("hitl_decision", sa.String(20)),
        sa.Column("hitl_notas", sa.Text),
        sa.Column("raw_orden", sa.Text),
        sa.Column("raw_respuesta", sa.Text),
    )

    op.create_table(
        "audit_log",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "autorizacion_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("autorizaciones.id"),
        ),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("accion", sa.String(100), nullable=False),
        sa.Column("actor", sa.String(100), nullable=False),
        sa.Column("resultado", sa.String(50)),
        sa.Column("datos_entrada", postgresql.JSONB),
        sa.Column("datos_salida", postgresql.JSONB),
        sa.Column("confidence_score", sa.Numeric(5, 4)),
        sa.Column("hash_sha256", sa.String(64), nullable=False),
        sa.Column("hash_previo", sa.String(64)),
        sa.Column("modelo_usado", sa.String(100)),
        sa.Column("version_calculador", sa.String(20)),
        sa.Column("hitl_intervencion", sa.Boolean, server_default=sa.false()),
    )

    op.create_table(
        "codigos_aseguradora",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("aseguradora", sa.String(50), nullable=False),
        sa.Column("procedimiento_descripcion", sa.Text, nullable=False),
        sa.Column("cie10_codigo", sa.String(20)),
        sa.Column("aseguradora_codigo", sa.String(50), nullable=False),
        sa.Column("requiere_autorizacion", sa.Boolean, server_default=sa.true()),
        sa.Column("documentacion_requerida", postgresql.JSONB),
        sa.Column("copago_euros", sa.Numeric(8, 2)),
        sa.Column("notas", sa.Text),
        sa.Column("version", sa.String(20), nullable=False),
        sa.Column("activo", sa.Boolean, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index(
        "idx_codigo_aseguradora",
        "codigos_aseguradora",
        ["aseguradora", "cie10_codigo", "version"],
        unique=True,
        postgresql_where=sa.text("activo = TRUE"),
    )


def downgrade() -> None:
    op.drop_index("idx_codigo_aseguradora", table_name="codigos_aseguradora")
    op.drop_table("codigos_aseguradora")
    op.drop_table("audit_log")
    op.drop_table("autorizaciones")
