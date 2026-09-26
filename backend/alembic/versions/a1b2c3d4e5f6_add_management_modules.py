"""add_management_modules

Revision ID: a1b2c3d4e5f6
Revises: e71b2a9c1f01
Create Date: 2026-09-26 22:05:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "e71b2a9c1f01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create Enums
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE job_post_status AS ENUM ('PENDING', 'APPROVED', 'REJECTED', 'CLOSED');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE job_type AS ENUM ('full_time', 'part_time', 'internship');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE event_type AS ENUM ('anniversary', 'talkshow', 'workshop', 'seminar', 'other');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE registration_type AS ENUM ('attendee', 'speaker');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE registration_status AS ENUM ('REGISTERED', 'ATTENDED', 'CANCELLED');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE survey_status AS ENUM ('DRAFT', 'ACTIVE', 'CLOSED');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE question_type AS ENUM ('text', 'single_choice', 'multiple_choice', 'scale');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE aid_application_status AS ENUM ('PENDING', 'APPROVED', 'REJECTED', 'DISBURSED');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE contribution_status AS ENUM ('PLEDGED', 'CONFIRMED');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE document_status AS ENUM ('PROCESSING', 'READY', 'FAILED');
        EXCEPTION WHEN duplicate_object THEN null; END $$;
    """)

    # 2. Update users table with new columns
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS graduation_year INTEGER")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS major VARCHAR(255)")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(20)")

    # 3. Create companies table
    op.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(255) UNIQUE NOT NULL,
            industry VARCHAR(255),
            website VARCHAR(500),
            address TEXT,
            description TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(name);
    """)

    # 4. Update alumni_profiles table
    op.execute("""
        ALTER TABLE alumni_profiles ADD COLUMN IF NOT EXISTS company_id UUID REFERENCES companies(id) ON DELETE SET NULL;
        ALTER TABLE alumni_profiles ADD COLUMN IF NOT EXISTS phone VARCHAR(20);
        ALTER TABLE alumni_profiles ADD COLUMN IF NOT EXISTS gpa NUMERIC(3, 2);
        ALTER TABLE alumni_profiles ADD COLUMN IF NOT EXISTS current_job_title VARCHAR(255);
        ALTER TABLE alumni_profiles ADD COLUMN IF NOT EXISTS company_name VARCHAR(255);
        ALTER TABLE alumni_profiles ADD COLUMN IF NOT EXISTS work_location VARCHAR(255);
        ALTER TABLE alumni_profiles ADD COLUMN IF NOT EXISTS job_field VARCHAR(255);
        ALTER TABLE alumni_profiles ADD COLUMN IF NOT EXISTS bio TEXT;
        ALTER TABLE alumni_profiles ADD COLUMN IF NOT EXISTS achievements TEXT;
        ALTER TABLE alumni_profiles ADD COLUMN IF NOT EXISTS raw_text TEXT;
        CREATE INDEX IF NOT EXISTS idx_alumni_profiles_graduation_year ON alumni_profiles(graduation_year);
        CREATE INDEX IF NOT EXISTS idx_alumni_profiles_major ON alumni_profiles(major);
    """)

    # 5. Create import_sessions table
    op.execute("""
        CREATE TABLE IF NOT EXISTS import_sessions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            uploaded_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
            filename VARCHAR(255) NOT NULL,
            status document_status NOT NULL DEFAULT 'PROCESSING',
            total_records INTEGER NOT NULL DEFAULT 0,
            new_records INTEGER NOT NULL DEFAULT 0,
            updated_records INTEGER NOT NULL DEFAULT 0,
            error TEXT,
            preview_data JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
    """)

    # 6. Create job_posts & job_applications tables
    op.execute("""
        CREATE TABLE IF NOT EXISTS job_posts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            created_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
            company_id UUID REFERENCES companies(id) ON DELETE SET NULL,
            approved_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
            title VARCHAR(255) NOT NULL,
            job_type job_type NOT NULL,
            description TEXT NOT NULL,
            requirements TEXT,
            benefits TEXT,
            location VARCHAR(255),
            salary_min INTEGER,
            salary_max INTEGER,
            deadline TIMESTAMPTZ,
            status job_post_status NOT NULL DEFAULT 'PENDING',
            rejection_note TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_job_posts_status ON job_posts(status);
        CREATE INDEX IF NOT EXISTS idx_job_posts_job_type ON job_posts(job_type);
        CREATE INDEX IF NOT EXISTS idx_job_posts_created_at ON job_posts(created_at);

        CREATE TABLE IF NOT EXISTS job_applications (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            job_post_id UUID NOT NULL REFERENCES job_posts(id) ON DELETE CASCADE,
            applicant_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            cover_letter TEXT,
            cv_url VARCHAR(500),
            status VARCHAR(50) NOT NULL DEFAULT 'submitted',
            note TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_job_applications_job_post_id ON job_applications(job_post_id);
        CREATE INDEX IF NOT EXISTS idx_job_applications_applicant_id ON job_applications(applicant_id);
    """)

    # 7. Create events & event_registrations tables
    op.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            created_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
            title VARCHAR(255) NOT NULL,
            event_type event_type NOT NULL,
            description TEXT,
            location VARCHAR(500),
            is_online BOOLEAN NOT NULL DEFAULT false,
            online_link VARCHAR(500),
            start_time TIMESTAMPTZ NOT NULL,
            end_time TIMESTAMPTZ,
            max_attendees INTEGER,
            max_speakers INTEGER,
            is_published BOOLEAN NOT NULL DEFAULT false,
            banner_url VARCHAR(500),
            agenda TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_events_start_time ON events(start_time);
        CREATE INDEX IF NOT EXISTS idx_events_event_type ON events(event_type);
        CREATE INDEX IF NOT EXISTS idx_events_is_published ON events(is_published);

        CREATE TABLE IF NOT EXISTS event_registrations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            registration_type registration_type NOT NULL DEFAULT 'attendee',
            status registration_status NOT NULL DEFAULT 'REGISTERED',
            speaker_topic VARCHAR(500),
            speaker_bio TEXT,
            registered_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_event_reg_event_id ON event_registrations(event_id);
        CREATE INDEX IF NOT EXISTS idx_event_reg_user_id ON event_registrations(user_id);
    """)

    # 8. Create surveys, survey_questions, survey_responses, survey_answers
    op.execute("""
        CREATE TABLE IF NOT EXISTS surveys (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            created_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            status survey_status NOT NULL DEFAULT 'DRAFT',
            target_graduation_year INTEGER,
            start_date TIMESTAMPTZ,
            end_date TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE IF NOT EXISTS survey_questions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            survey_id UUID NOT NULL REFERENCES surveys(id) ON DELETE CASCADE,
            question_text TEXT NOT NULL,
            question_type question_type NOT NULL,
            options JSONB,
            is_required BOOLEAN NOT NULL DEFAULT true,
            order_index INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS survey_responses (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            survey_id UUID NOT NULL REFERENCES surveys(id) ON DELETE CASCADE,
            respondent_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            submitted_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_survey_responses_survey_id ON survey_responses(survey_id);
        CREATE INDEX IF NOT EXISTS idx_survey_responses_respondent_id ON survey_responses(respondent_id);

        CREATE TABLE IF NOT EXISTS survey_answers (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            response_id UUID NOT NULL REFERENCES survey_responses(id) ON DELETE CASCADE,
            question_id UUID NOT NULL REFERENCES survey_questions(id) ON DELETE CASCADE,
            answer_text TEXT,
            answer_choices JSONB,
            answer_scale INTEGER
        );
    """)

    # 9. Create financial_contributions & aid_applications
    op.execute("""
        CREATE TABLE IF NOT EXISTS financial_contributions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            contributor_id UUID REFERENCES users(id) ON DELETE SET NULL,
            amount INTEGER NOT NULL,
            message TEXT,
            is_anonymous BOOLEAN NOT NULL DEFAULT false,
            status contribution_status NOT NULL DEFAULT 'PLEDGED',
            confirmed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE IF NOT EXISTS aid_applications (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            applicant_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            reviewed_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
            title VARCHAR(255) NOT NULL,
            reason TEXT NOT NULL,
            amount_requested INTEGER,
            amount_approved INTEGER,
            supporting_documents JSONB,
            status aid_application_status NOT NULL DEFAULT 'PENDING',
            review_note TEXT,
            disbursed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS idx_aid_applications_status ON aid_applications(status);
        CREATE INDEX IF NOT EXISTS idx_aid_applications_applicant_id ON aid_applications(applicant_id);
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS aid_applications CASCADE;")
    op.execute("DROP TABLE IF EXISTS financial_contributions CASCADE;")
    op.execute("DROP TABLE IF EXISTS survey_answers CASCADE;")
    op.execute("DROP TABLE IF EXISTS survey_responses CASCADE;")
    op.execute("DROP TABLE IF EXISTS survey_questions CASCADE;")
    op.execute("DROP TABLE IF EXISTS surveys CASCADE;")
    op.execute("DROP TABLE IF EXISTS event_registrations CASCADE;")
    op.execute("DROP TABLE IF EXISTS events CASCADE;")
    op.execute("DROP TABLE IF EXISTS job_applications CASCADE;")
    op.execute("DROP TABLE IF EXISTS job_posts CASCADE;")
    op.execute("DROP TABLE IF EXISTS import_sessions CASCADE;")
    op.execute("DROP TABLE IF EXISTS companies CASCADE;")
