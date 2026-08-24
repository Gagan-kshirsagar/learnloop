"""Tutor chat sessions and messages with multi-turn memory and Postgres RLS

Revision ID: 0005_tutor_chat_sessions
Revises: 0004_tutor_rag
Create Date: 2026-08-24 15:05:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0005_tutor_chat_sessions"
down_revision: str | None = "0004_tutor_rag"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. chat_sessions table
    op.create_table(
        "chat_sessions",
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
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "lesson_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("lessons.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # 2. chat_messages table
    op.create_table(
        "chat_messages",
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
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("chat_sessions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("citations", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # 3. Create indices for fast timeline retrieval
    op.create_index(
        "idx_chat_sessions_tenant_user_updated",
        "chat_sessions",
        ["tenant_id", "user_id", "updated_at"],
    )
    op.create_index(
        "idx_chat_messages_tenant_session_created",
        "chat_messages",
        ["tenant_id", "session_id", "created_at"],
    )

    # 4. Enable and Force Postgres RLS
    for table in ["chat_sessions", "chat_messages"]:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")
        op.execute(
            f"CREATE POLICY tenant_isolation ON {table} "
            "USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid);"
        )

    # 5. Grant permissions to application role
    op.execute(
        "DO $$ BEGIN "
        "IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'learnloop_app') THEN "
        "GRANT ALL ON chat_sessions TO learnloop_app; "
        "GRANT ALL ON chat_messages TO learnloop_app; "
        "END IF; "
        "END $$;"
    )


def downgrade() -> None:
    for table in ["chat_messages", "chat_sessions"]:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table};")
    op.drop_index("idx_chat_messages_tenant_session_created", table_name="chat_messages")
    op.drop_table("chat_messages")
    op.drop_index("idx_chat_sessions_tenant_user_updated", table_name="chat_sessions")
    op.drop_table("chat_sessions")
