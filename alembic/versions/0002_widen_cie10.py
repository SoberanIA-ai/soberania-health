"""widen procedimiento_cie10 a VARCHAR(50)

En modo SIMULADO los identificadores como SIM_CIRUGIA_RODILLA_AMB superan
los 20 chars de la columna original. CIE-10 reales caben en 20, pero los
placeholders del catálogo simulado no. Sec 7.1b del handoff.

Revision ID: 0002
Revises: 0001
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "autorizaciones",
        "procedimiento_cie10",
        type_=sa.String(50),
        existing_type=sa.String(20),
        existing_nullable=True,
    )
    op.alter_column(
        "codigos_aseguradora",
        "cie10_codigo",
        type_=sa.String(50),
        existing_type=sa.String(20),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "autorizaciones",
        "procedimiento_cie10",
        type_=sa.String(20),
        existing_type=sa.String(50),
        existing_nullable=True,
    )
    op.alter_column(
        "codigos_aseguradora",
        "cie10_codigo",
        type_=sa.String(20),
        existing_type=sa.String(50),
        existing_nullable=True,
    )
