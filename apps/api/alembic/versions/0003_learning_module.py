"""Learning enrollments, exercises, submissions, and progress with Postgres RLS

Revision ID: 0003_learning_module
Revises: 0002_catalog_courses
Create Date: 2026-08-24 00:20:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0003_learning_module"
down_revision: str | None = "0002_catalog_courses"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. enrollments
    op.create_table(
        "enrollments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "course_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("courses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="active"),
        sa.Column(
            "enrolled_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "tenant_id", "user_id", "course_id", name="uq_enrollments_tenant_user_course"
        ),
    )
    op.create_index("ix_enrollments_tenant_id", "enrollments", ["tenant_id"])
    op.create_index("ix_enrollments_user_id", "enrollments", ["user_id"])
    op.create_index("ix_enrollments_course_id", "enrollments", ["course_id"])

    op.execute("ALTER TABLE enrollments ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE enrollments FORCE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation ON enrollments "
        "USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid);"
    )

    # 2. exercises
    op.create_table(
        "exercises",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "lesson_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("lessons.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("prompt_md", sa.Text(), nullable=False, server_default=""),
        sa.Column("starter_code", sa.Text(), nullable=False, server_default=""),
        sa.Column("language", sa.String(length=50), nullable=False, server_default="python"),
        sa.Column("tests_code", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("tenant_id", "lesson_id", name="uq_exercises_tenant_lesson"),
    )
    op.create_index("ix_exercises_tenant_id", "exercises", ["tenant_id"])
    op.create_index("ix_exercises_lesson_id", "exercises", ["lesson_id"])

    op.execute("ALTER TABLE exercises ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE exercises FORCE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation ON exercises "
        "USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid);"
    )

    # 3. submissions
    op.create_table(
        "submissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "exercise_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("exercises.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="queued"),
        sa.Column("stdout", sa.Text(), nullable=True),
        sa.Column("stderr", sa.Text(), nullable=True),
        sa.Column("tests_passed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tests_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_submissions_tenant_id", "submissions", ["tenant_id"])
    op.create_index("ix_submissions_user_id", "submissions", ["user_id"])
    op.create_index("ix_submissions_exercise_id", "submissions", ["exercise_id"])
    op.create_index("ix_submissions_status", "submissions", ["status"])

    op.execute("ALTER TABLE submissions ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE submissions FORCE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation ON submissions "
        "USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid);"
    )

    # 4. progress
    op.create_table(
        "progress",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "lesson_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("lessons.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "exercise_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("exercises.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("completed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "user_id",
            "lesson_id",
            "exercise_id",
            name="uq_progress_tenant_user_target",
        ),
    )
    op.create_index("ix_progress_tenant_id", "progress", ["tenant_id"])
    op.create_index("ix_progress_user_id", "progress", ["user_id"])
    op.create_index("ix_progress_lesson_id", "progress", ["lesson_id"])
    op.create_index("ix_progress_exercise_id", "progress", ["exercise_id"])

    op.execute("ALTER TABLE progress ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE progress FORCE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY tenant_isolation ON progress "
        "USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid);"
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON progress;")
    op.execute("ALTER TABLE progress DISABLE ROW LEVEL SECURITY;")
    op.drop_table("progress")

    op.execute("DROP POLICY IF EXISTS tenant_isolation ON submissions;")
    op.execute("ALTER TABLE submissions DISABLE ROW LEVEL SECURITY;")
    op.drop_table("submissions")

    op.execute("DROP POLICY IF EXISTS tenant_isolation ON exercises;")
    op.execute("ALTER TABLE exercises DISABLE ROW LEVEL SECURITY;")
    op.drop_table("exercises")

    op.execute("DROP POLICY IF EXISTS tenant_isolation ON enrollments;")
    op.execute("ALTER TABLE enrollments DISABLE ROW LEVEL SECURITY;")
    op.drop_table("enrollments")
