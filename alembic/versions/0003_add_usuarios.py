"""add_usuarios — tabla de autenticación del dashboard

Revision ID: 0003
Revises: 0002
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from passlib.context import CryptContext
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def upgrade() -> None:
    op.create_table(
        "usuarios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(200), unique=True, nullable=False),
        sa.Column("nombre", sa.String(200), nullable=False),
        sa.Column("password_hash", sa.String(200), nullable=False),
        sa.Column("rol", sa.String(50), nullable=False, server_default="recepcionista"),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("ultimo_acceso", sa.DateTime(timezone=True), nullable=True),
    )

    # Seed: usuarios de demo — CAMBIAR passwords en producción con HM
    # Hashes generados offline con bcrypt (cost factor 12)
    h_admin = pwd_context.hash("soberania2026")
    h_supervisor = pwd_context.hash("supervisor2026")
    h_auditor = pwd_context.hash("auditor2026")

    op.execute(
        f"""
        INSERT INTO usuarios (id, email, nombre, password_hash, rol) VALUES
        (gen_random_uuid(), 'isabella@hmhospitales.es',
         'Isabella Cristancho', '{h_admin}', 'admin'),
        (gen_random_uuid(), 'supervisor@hmhospitales.es',
         'Supervisor HM Demo', '{h_supervisor}', 'supervisor'),
        (gen_random_uuid(), 'auditor@hmhospitales.es',
         'Auditor AI Act Demo', '{h_auditor}', 'auditor')
        """
    )


def downgrade() -> None:
    op.drop_table("usuarios")