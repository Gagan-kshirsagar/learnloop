"""Catalog courses, modules, and lessons with Postgres RLS

Revision ID: 0002_catalog_courses_modules_lessons
Revises: 0001_initial_tenancy_and_users
Create Date: 2026-08-23 23:50:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0002_catalog_courses"
down_revision: str | None = "0001_initial_tenancy_and_users"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create courses table
    op.create_table(
        "courses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="draft"),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
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
        sa.UniqueConstraint("tenant_id", "slug", name="uq_courses_tenant_slug"),
    )
    op.create_index("ix_courses_tenant_id", "courses", ["tenant_id"])
    op.create_index("ix_courses_status", "courses", ["status"])

    # Enable RLS on courses
    op.execute("ALTER TABLE courses ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE courses FORCE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation ON courses "
        "USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid);"
    )

    # 2. Create modules table
    op.create_table(
        "modules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "course_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("courses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_modules_tenant_id", "modules", ["tenant_id"])
    op.create_index("ix_modules_course_id", "modules", ["course_id"])

    # Enable RLS on modules
    op.execute("ALTER TABLE modules ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE modules FORCE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation ON modules "
        "USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid);"
    )

    # 3. Create lessons table
    op.create_table(
        "lessons",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "module_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("modules.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content_md", sa.Text(), nullable=False, server_default=""),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
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
    op.create_index("ix_lessons_tenant_id", "lessons", ["tenant_id"])
    op.create_index("ix_lessons_module_id", "lessons", ["module_id"])

    # Enable RLS on lessons
    op.execute("ALTER TABLE lessons ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE lessons FORCE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation ON lessons "
        "USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid);"
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON lessons;")
    op.execute("ALTER TABLE lessons DISABLE ROW LEVEL SECURITY;")
    op.drop_index("ix_lessons_module_id", table_name="lessons")
    op.drop_index("ix_lessons_tenant_id", table_name="lessons")
    op.drop_table("lessons")

    op.execute("DROP POLICY IF EXISTS tenant_isolation ON modules;")
    op.execute("ALTER TABLE modules DISABLE ROW LEVEL SECURITY;")
    op.drop_index("ix_modules_course_id", table_name="modules")
    op.drop_index("ix_modules_tenant_id", table_name="modules")
    op.drop_table("modules")

    op.execute("DROP POLICY IF EXISTS tenant_isolation ON courses;")
    op.execute("ALTER TABLE courses DISABLE ROW LEVEL SECURITY;")
    op.drop_index("ix_courses_status", table_name="courses")
    op.drop_index("ix_courses_tenant_id", table_name="courses")
    op.drop_table("courses")
