"""Tutor RAG lesson chunks with pgvector and Postgres RLS

Revision ID: 0004_tutor_rag
Revises: 0003_learning_module
Create Date: 2026-08-24 13:45:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0004_tutor_rag"
down_revision: str | None = "0003_learning_module"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 2. lesson_chunks table
    op.create_table(
        "lesson_chunks",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "lesson_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("lessons.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("embedding", Vector(768), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "lesson_id",
            "ordinal",
            name="uq_lesson_chunks_tenant_lesson_ordinal",
        ),
    )

    # 3. Create HNSW Cosine Index
    op.execute(
        "CREATE INDEX idx_lesson_chunks_embedding ON lesson_chunks "
        "USING hnsw (embedding vector_cosine_ops);"
    )

    # 4. Enable and Force Postgres RLS
    op.execute("ALTER TABLE lesson_chunks ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE lesson_chunks FORCE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation ON lesson_chunks "
        "USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid);"
    )

    # 5. Grant permissions to application role
    op.execute(
        "DO $$ BEGIN "
        "IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'learnloop_app') THEN "
        "GRANT ALL ON lesson_chunks TO learnloop_app; "
        "END IF; "
        "END $$;"
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON lesson_chunks;")
    op.execute("DROP INDEX IF EXISTS idx_lesson_chunks_embedding;")
    op.drop_table("lesson_chunks")
