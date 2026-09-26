"""sync_spec_models

Revision ID: e71b2a9c1f01
Revises: 489e08191500
Create Date: 2026-09-05 20:15:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e71b2a9c1f01"
down_revision: str | Sequence[str] | None = "489e08191500"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Update session_channel enum with 'email'
    op.execute("ALTER TYPE session_channel ADD VALUE IF NOT EXISTS 'email'")

    # 2. Update users table: add student_id, drop zalo_id
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS student_id VARCHAR(20)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_student_id ON users (student_id)")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS zalo_id")

    # 3. Update alumni_profiles table: nullable user_id, add student_id, full_name, email
    op.execute("ALTER TABLE alumni_profiles ALTER COLUMN user_id DROP NOT NULL")
    op.execute("ALTER TABLE alumni_profiles ADD COLUMN IF NOT EXISTS student_id VARCHAR(50)")
    op.execute(
        "ALTER TABLE alumni_profiles ADD COLUMN IF NOT EXISTS full_name VARCHAR(255) DEFAULT '' NOT NULL"
    )
    op.execute(
        "ALTER TABLE alumni_profiles ADD COLUMN IF NOT EXISTS email VARCHAR(255) DEFAULT '' NOT NULL"
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_alumni_profiles_student_id ON alumni_profiles (student_id)"
    )

    # 4. Update mentorship_sessions: rename alumni_identifier to alumni_student_id
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'mentorship_sessions' AND column_name = 'alumni_identifier'
            ) THEN
                ALTER TABLE mentorship_sessions RENAME COLUMN alumni_identifier TO alumni_student_id;
            END IF;
        END $$;
    """)

    # 5. Update pending_points: rename alumni_identifier to alumni_student_id
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'pending_points' AND column_name = 'alumni_identifier'
            ) THEN
                ALTER TABLE pending_points RENAME COLUMN alumni_identifier TO alumni_student_id;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    # Downgrade logic if needed
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'mentorship_sessions' AND column_name = 'alumni_student_id'
            ) THEN
                ALTER TABLE mentorship_sessions RENAME COLUMN alumni_student_id TO alumni_identifier;
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'pending_points' AND column_name = 'alumni_student_id'
            ) THEN
                ALTER TABLE pending_points RENAME COLUMN alumni_student_id TO alumni_identifier;
            END IF;
        END $$;
    """)
    op.execute("DROP INDEX IF EXISTS ix_alumni_profiles_student_id")
    op.execute("ALTER TABLE alumni_profiles DROP COLUMN IF EXISTS email")
    op.execute("ALTER TABLE alumni_profiles DROP COLUMN IF EXISTS full_name")
    op.execute("ALTER TABLE alumni_profiles DROP COLUMN IF EXISTS student_id")
    op.execute("DROP INDEX IF EXISTS ix_users_student_id")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS student_id")
