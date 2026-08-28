"""align body measurement fields with current model"""

from alembic import op


revision = "0008_body_measurement_fields"
down_revision = "0007_workout_plan_strategy"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE body_measurements ADD COLUMN IF NOT EXISTS chest_cm DOUBLE PRECISION")
    op.execute("ALTER TABLE body_measurements ADD COLUMN IF NOT EXISTS waist_cm DOUBLE PRECISION")
    op.execute("ALTER TABLE body_measurements ADD COLUMN IF NOT EXISTS hips_cm DOUBLE PRECISION")
    op.execute("ALTER TABLE body_measurements ADD COLUMN IF NOT EXISTS biceps_left_cm DOUBLE PRECISION")
    op.execute("ALTER TABLE body_measurements ADD COLUMN IF NOT EXISTS biceps_right_cm DOUBLE PRECISION")
    op.execute("ALTER TABLE body_measurements ADD COLUMN IF NOT EXISTS thigh_left_cm DOUBLE PRECISION")
    op.execute("ALTER TABLE body_measurements ADD COLUMN IF NOT EXISTS thigh_right_cm DOUBLE PRECISION")
    op.execute("ALTER TABLE body_measurements ADD COLUMN IF NOT EXISTS neck_cm DOUBLE PRECISION")
    op.execute("ALTER TABLE body_measurements ADD COLUMN IF NOT EXISTS bodyfat_pct DOUBLE PRECISION")
    op.execute("ALTER TABLE body_measurements ADD COLUMN IF NOT EXISTS notes VARCHAR(512)")
    op.execute("ALTER TABLE body_measurements ADD COLUMN IF NOT EXISTS recorded_at TIMESTAMP DEFAULT now()")
    op.execute(
        """
        UPDATE body_measurements
        SET
            bodyfat_pct = COALESCE(bodyfat_pct, body_fat_pct::DOUBLE PRECISION),
            recorded_at = COALESCE(recorded_at, created_at, date::TIMESTAMP, now())
        """
    )
    op.execute("ALTER TABLE body_measurements ALTER COLUMN date DROP NOT NULL")
    op.execute(
        """
        DO $$
        DECLARE
            constraint_name text;
        BEGIN
            SELECT tc.constraint_name INTO constraint_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
               AND tc.table_schema = kcu.table_schema
            WHERE tc.table_name = 'body_measurements'
              AND tc.constraint_type = 'FOREIGN KEY'
              AND kcu.column_name = 'user_id'
            LIMIT 1;

            IF constraint_name IS NOT NULL THEN
                EXECUTE format('ALTER TABLE body_measurements DROP CONSTRAINT %I', constraint_name);
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE body_measurements ALTER COLUMN date SET NOT NULL")
    op.execute("ALTER TABLE body_measurements DROP COLUMN IF EXISTS recorded_at")
    op.execute("ALTER TABLE body_measurements DROP COLUMN IF EXISTS notes")
    op.execute("ALTER TABLE body_measurements DROP COLUMN IF EXISTS bodyfat_pct")
    op.execute("ALTER TABLE body_measurements DROP COLUMN IF EXISTS neck_cm")
    op.execute("ALTER TABLE body_measurements DROP COLUMN IF EXISTS thigh_right_cm")
    op.execute("ALTER TABLE body_measurements DROP COLUMN IF EXISTS thigh_left_cm")
    op.execute("ALTER TABLE body_measurements DROP COLUMN IF EXISTS biceps_right_cm")
    op.execute("ALTER TABLE body_measurements DROP COLUMN IF EXISTS biceps_left_cm")
    op.execute("ALTER TABLE body_measurements DROP COLUMN IF EXISTS hips_cm")
    op.execute("ALTER TABLE body_measurements DROP COLUMN IF EXISTS waist_cm")
    op.execute("ALTER TABLE body_measurements DROP COLUMN IF EXISTS chest_cm")
