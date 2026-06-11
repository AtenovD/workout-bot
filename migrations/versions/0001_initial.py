"""Initial migration — create all tables
Revision ID: 0001_initial
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('users',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(64)),
        sa.Column('first_name', sa.String(128)),
        sa.Column('language_code', sa.String(8), server_default='ru'),
        sa.Column('status', sa.String(16), server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_active_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_users_telegram_id', 'users', ['telegram_id'], unique=True)
    op.create_table('muscle_groups',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('code', sa.String(64), nullable=False, unique=True),
        sa.Column('name_ru', sa.String(128), nullable=False),
        sa.Column('name_en', sa.String(128), nullable=False),
        sa.Column('body_part', sa.String(32), nullable=False),
    )
    op.create_table('equipment',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('code', sa.String(64), nullable=False, unique=True),
        sa.Column('name_ru', sa.String(128), nullable=False),
        sa.Column('name_en', sa.String(128), nullable=False),
        sa.Column('category', sa.String(16), nullable=False),
        sa.Column('icon', sa.String(8)),
        sa.Column('photo_url', sa.String(512)),
        sa.Column('description', sa.String(512)),
    )
    op.create_table('exercises',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('code', sa.String(64), nullable=False, unique=True),
        sa.Column('name_ru', sa.String(128), nullable=False),
        sa.Column('name_en', sa.String(128), nullable=False),
        sa.Column('description', sa.String(1024)),
        sa.Column('instructions', postgresql.JSON()),
        sa.Column('tips', postgresql.JSON()),
        sa.Column('common_mistakes', postgresql.JSON()),
        sa.Column('primary_muscle_group_id', sa.BigInteger(), sa.ForeignKey('muscle_groups.id')),
        sa.Column('required_equipment_id', sa.BigInteger(), sa.ForeignKey('equipment.id')),
        sa.Column('equipment_category', sa.String(16), nullable=False),
        sa.Column('exercise_type', sa.String(16), nullable=False),
        sa.Column('difficulty', sa.Integer(), server_default='3'),
        sa.Column('met_value', sa.Numeric(5, 2)),
        sa.Column('photo_url', sa.String(512)),
        sa.Column('video_url', sa.String(512)),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
    )
    op.create_table('exercise_alternatives',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('exercise_id', sa.BigInteger(), sa.ForeignKey('exercises.id'), nullable=False),
        sa.Column('alternative_exercise_id', sa.BigInteger(), sa.ForeignKey('exercises.id'), nullable=False),
        sa.Column('reason', sa.String(16), server_default='no_equipment'),
        sa.UniqueConstraint('exercise_id', 'alternative_exercise_id'),
    )
    op.create_index('ix_ex_alt_exercise_id', 'exercise_alternatives', ['exercise_id'])
    op.create_table('profiles',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.BigInteger(), sa.ForeignKey('users.id'), nullable=False, unique=True),
        sa.Column('gender', sa.String(8)),
        sa.Column('birth_date', sa.Date()),
        sa.Column('height_cm', sa.Integer()),
        sa.Column('current_weight_kg', sa.Numeric(5, 2)),
        sa.Column('target_weight_kg', sa.Numeric(5, 2)),
        sa.Column('goal', sa.String(16)),
        sa.Column('experience_level', sa.String(16)),
        sa.Column('training_experience_months', sa.Integer(), server_default='0'),
        sa.Column('training_structure', sa.String(16)),
        sa.Column('split_type', sa.String(24)),
        sa.Column('intensity_level', sa.Integer(), server_default='3'),
        sa.Column('preferred_duration_min', sa.Integer(), server_default='45'),
        sa.Column('health_flags', postgresql.JSON()),
        sa.Column('calibrated_at', sa.DateTime(timezone=True)),
    )
    op.create_table('user_equipment',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.BigInteger(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('equipment_id', sa.BigInteger(), sa.ForeignKey('equipment.id'), nullable=False),
        sa.Column('has_it', sa.Boolean(), server_default='true'),
        sa.Column('added_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('user_id', 'equipment_id'),
    )
    op.create_index('ix_user_equipment_user_id', 'user_equipment', ['user_id'])
    op.create_table('workout_plans',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.BigInteger(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('structure', sa.String(32), nullable=False),
        sa.Column('split_type', sa.String(32)),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_workout_plans_user_id', 'workout_plans', ['user_id'])
    op.create_table('workout_sessions',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.BigInteger(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('plan_id', sa.BigInteger(), sa.ForeignKey('workout_plans.id')),
        sa.Column('scheduled_date', sa.Date()),
        sa.Column('status', sa.String(16), server_default='planned'),
        sa.Column('difficulty_modifier', sa.String(8), server_default='normal'),
        sa.Column('started_at', sa.DateTime(timezone=True)),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('duration_min', sa.Integer()),
        sa.Column('total_volume_kg', sa.Numeric(10, 2)),
        sa.Column('calories_burned', sa.Integer()),
        sa.Column('xp_earned', sa.Integer()),
        sa.Column('rpe_session', sa.Integer()),
        sa.Column('notes', sa.String(1024)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_workout_sessions_user_id', 'workout_sessions', ['user_id'])
    op.create_table('session_exercises',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('session_id', sa.BigInteger(), sa.ForeignKey('workout_sessions.id'), nullable=False),
        sa.Column('exercise_id', sa.BigInteger(), sa.ForeignKey('exercises.id'), nullable=False),
        sa.Column('order_index', sa.Integer(), server_default='0'),
        sa.Column('target_sets', sa.Integer(), server_default='3'),
        sa.Column('target_reps', sa.Integer(), server_default='10'),
        sa.Column('target_weight_kg', sa.Numeric(6, 2)),
        sa.Column('rest_seconds', sa.Integer(), server_default='90'),
        sa.Column('is_completed', sa.Boolean(), server_default='false'),
    )
    op.create_index('ix_session_exercises_session_id', 'session_exercises', ['session_id'])
    op.create_table('exercise_sets',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('session_exercise_id', sa.BigInteger(), sa.ForeignKey('session_exercises.id'), nullable=False),
        sa.Column('set_number', sa.Integer(), nullable=False),
        sa.Column('reps_done', sa.Integer()),
        sa.Column('weight_kg', sa.Numeric(6, 2)),
        sa.Column('rpe', sa.Integer()),
        sa.Column('is_warmup', sa.Boolean(), server_default='false'),
        sa.Column('completed_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_exercise_sets_session_exercise_id', 'exercise_sets', ['session_exercise_id'])
    op.create_table('user_stats',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.BigInteger(), sa.ForeignKey('users.id'), nullable=False, unique=True),
        sa.Column('level', sa.Integer(), server_default='1'),
        sa.Column('total_xp', sa.Integer(), server_default='0'),
        sa.Column('current_streak', sa.Integer(), server_default='0'),
        sa.Column('longest_streak', sa.Integer(), server_default='0'),
        sa.Column('total_workouts', sa.Integer(), server_default='0'),
        sa.Column('total_volume_kg', sa.Numeric(12, 2), server_default='0'),
        sa.Column('skipped_count', sa.Integer(), server_default='0'),
        sa.Column('last_workout_date', sa.Date()),
    )
    op.create_table('achievements',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('code', sa.String(64), nullable=False, unique=True),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('description', sa.String(512), nullable=False),
        sa.Column('icon', sa.String(8)),
        sa.Column('category', sa.String(16), nullable=False),
        sa.Column('tier', sa.String(16), nullable=False),
        sa.Column('condition', postgresql.JSON(), nullable=False),
        sa.Column('xp_reward', sa.Integer(), server_default='50'),
    )
    op.create_table('user_achievements',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.BigInteger(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('achievement_id', sa.BigInteger(), sa.ForeignKey('achievements.id'), nullable=False),
        sa.Column('unlocked_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('progress', sa.Float(), server_default='0'),
        sa.UniqueConstraint('user_id', 'achievement_id'),
    )
    op.create_index('ix_user_achievements_user_id', 'user_achievements', ['user_id'])
    op.create_table('personal_records',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.BigInteger(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('exercise_id', sa.BigInteger(), sa.ForeignKey('exercises.id'), nullable=False),
        sa.Column('record_type', sa.String(16), nullable=False),
        sa.Column('value', sa.Numeric(10, 2), nullable=False),
        sa.Column('achieved_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('user_id', 'exercise_id', 'record_type'),
    )
    op.create_table('body_measurements',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.BigInteger(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('weight_kg', sa.Numeric(5, 2)),
        sa.Column('body_fat_pct', sa.Numeric(5, 2)),
        sa.Column('measurements', postgresql.JSON()),
        sa.Column('photo_url', sa.String(512)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_body_measurements_user_id', 'body_measurements', ['user_id'])
    op.create_table('schedules',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.BigInteger(), sa.ForeignKey('users.id'), nullable=False, unique=True),
        sa.Column('mode', sa.String(16), server_default='spontaneous'),
        sa.Column('days_of_week', postgresql.ARRAY(sa.Integer())),
        sa.Column('reminder_enabled', sa.Boolean(), server_default='false'),
        sa.Column('reminder_time', sa.Time()),
        sa.Column('timezone', sa.String(64), server_default='Europe/Moscow'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table('reminders',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.BigInteger(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('type', sa.String(32), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('payload', postgresql.JSON()),
        sa.Column('is_sent', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_reminders_user_id', 'reminders', ['user_id'])
    op.create_table('calibration_answers',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.BigInteger(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('question_key', sa.String(64), nullable=False),
        sa.Column('answer', postgresql.JSON(), nullable=False),
        sa.Column('answered_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_calibration_answers_user_id', 'calibration_answers', ['user_id'])


def downgrade():
    for t in ['calibration_answers','reminders','schedules','body_measurements','personal_records',
              'user_achievements','achievements','user_stats','exercise_sets','session_exercises',
              'workout_sessions','workout_plans','user_equipment','profiles','exercise_alternatives',
              'exercises','equipment','muscle_groups','users']:
        try: op.drop_table(t)
        except: pass
