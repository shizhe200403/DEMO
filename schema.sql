-- PostgreSQL 16+ schema for the nutrition recipe recommendation system
-- Reference only. Django migrations are the source of truth for deployment.

CREATE TABLE IF NOT EXISTS app_user (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username VARCHAR(64) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(32),
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(32) NOT NULL DEFAULT 'user',
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    avatar_url TEXT,
    nickname VARCHAR(64),
    signature VARCHAR(255),
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_app_user_username UNIQUE (username),
    CONSTRAINT uq_app_user_email UNIQUE (email),
    CONSTRAINT uq_app_user_phone UNIQUE (phone)
);

CREATE TABLE IF NOT EXISTS user_profile (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE REFERENCES app_user(id) ON DELETE CASCADE,
    gender VARCHAR(16),
    birthday DATE,
    height_cm NUMERIC(6,2),
    weight_kg NUMERIC(6,2),
    target_weight_kg NUMERIC(6,2),
    activity_level VARCHAR(32),
    occupation VARCHAR(64),
    budget_level VARCHAR(32),
    cooking_skill VARCHAR(32),
    meal_preference VARCHAR(64),
    diet_type VARCHAR(64),
    is_outdoor_eating_frequent BOOLEAN NOT NULL DEFAULT FALSE,
    household_size INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_health_condition (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE REFERENCES app_user(id) ON DELETE CASCADE,
    has_allergy BOOLEAN NOT NULL DEFAULT FALSE,
    allergy_tags TEXT[],
    avoid_food_tags TEXT[],
    religious_restriction VARCHAR(64),
    has_hypertension BOOLEAN NOT NULL DEFAULT FALSE,
    has_diabetes BOOLEAN NOT NULL DEFAULT FALSE,
    has_hyperlipidemia BOOLEAN NOT NULL DEFAULT FALSE,
    is_pregnant BOOLEAN NOT NULL DEFAULT FALSE,
    is_lactating BOOLEAN NOT NULL DEFAULT FALSE,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ingredient (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    canonical_name VARCHAR(128) NOT NULL,
    alias_names TEXT[],
    category VARCHAR(64),
    default_unit VARCHAR(32),
    is_common BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_ingredient_canonical_name UNIQUE (canonical_name)
);

CREATE TABLE IF NOT EXISTS ingredient_nutrition (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ingredient_id BIGINT NOT NULL REFERENCES ingredient(id) ON DELETE CASCADE,
    source VARCHAR(64) NOT NULL,
    source_version VARCHAR(64),
    per_100g_energy NUMERIC(12,4),
    per_100g_protein NUMERIC(12,4),
    per_100g_fat NUMERIC(12,4),
    per_100g_carbohydrate NUMERIC(12,4),
    per_100g_fiber NUMERIC(12,4),
    per_100g_sodium NUMERIC(12,4),
    per_100g_calcium NUMERIC(12,4),
    per_100g_iron NUMERIC(12,4),
    per_100g_vitamin_a NUMERIC(12,4),
    per_100g_vitamin_c NUMERIC(12,4),
    raw_payload JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS recipe (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    cover_image_url TEXT,
    description TEXT,
    portion_size VARCHAR(64),
    servings INTEGER NOT NULL DEFAULT 1,
    difficulty VARCHAR(32),
    cook_time_minutes INTEGER,
    prep_time_minutes INTEGER,
    meal_type VARCHAR(32),
    taste_tags TEXT[],
    cuisine_tags TEXT[],
    status VARCHAR(32) NOT NULL DEFAULT 'draft',
    source_type VARCHAR(32) NOT NULL DEFAULT 'local',
    source_name VARCHAR(128),
    audit_status VARCHAR(32) NOT NULL DEFAULT 'pending',
    created_by BIGINT REFERENCES app_user(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS recipe_step (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    recipe_id BIGINT NOT NULL REFERENCES recipe(id) ON DELETE CASCADE,
    step_no INTEGER NOT NULL,
    content TEXT NOT NULL,
    step_image_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_recipe_step UNIQUE (recipe_id, step_no)
);

CREATE TABLE IF NOT EXISTS recipe_ingredient (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    recipe_id BIGINT NOT NULL REFERENCES recipe(id) ON DELETE CASCADE,
    ingredient_id BIGINT NOT NULL REFERENCES ingredient(id) ON DELETE RESTRICT,
    amount NUMERIC(12,4) NOT NULL,
    unit VARCHAR(32) NOT NULL,
    is_main BOOLEAN NOT NULL DEFAULT FALSE,
    remark VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS recipe_nutrition_summary (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    recipe_id BIGINT NOT NULL UNIQUE REFERENCES recipe(id) ON DELETE CASCADE,
    per_serving_energy NUMERIC(12,4),
    per_serving_protein NUMERIC(12,4),
    per_serving_fat NUMERIC(12,4),
    per_serving_carbohydrate NUMERIC(12,4),
    per_serving_fiber NUMERIC(12,4),
    per_serving_sodium NUMERIC(12,4),
    per_serving_calcium NUMERIC(12,4),
    per_serving_iron NUMERIC(12,4),
    per_serving_vitamin_a NUMERIC(12,4),
    per_serving_vitamin_c NUMERIC(12,4),
    calculation_method VARCHAR(64),
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_behavior (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    recipe_id BIGINT REFERENCES recipe(id) ON DELETE CASCADE,
    behavior_type VARCHAR(32) NOT NULL,
    behavior_value NUMERIC(12,4),
    context_scene VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS recommendation_log (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    recipe_id BIGINT NOT NULL REFERENCES recipe(id) ON DELETE CASCADE,
    score NUMERIC(12,4),
    reason_text TEXT,
    source_model VARCHAR(64),
    recommendation_scene VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_feedback (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    recipe_id BIGINT NOT NULL REFERENCES recipe(id) ON DELETE CASCADE,
    feedback_type VARCHAR(32) NOT NULL,
    rating INTEGER,
    comment TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_favorite_recipe (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    recipe_id BIGINT NOT NULL REFERENCES recipe(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_user_favorite_recipe UNIQUE (user_id, recipe_id)
);

CREATE TABLE IF NOT EXISTS meal_record (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    record_date DATE NOT NULL,
    meal_type VARCHAR(32) NOT NULL,
    source_type VARCHAR(32) NOT NULL DEFAULT 'manual',
    note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_meal_record_unique_context UNIQUE (user_id, record_date, meal_type)
);

CREATE TABLE IF NOT EXISTS meal_record_item (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    meal_record_id BIGINT NOT NULL REFERENCES meal_record(id) ON DELETE CASCADE,
    recipe_id BIGINT REFERENCES recipe(id) ON DELETE SET NULL,
    ingredient_name_snapshot VARCHAR(255),
    amount NUMERIC(12,4) NOT NULL,
    unit VARCHAR(32) NOT NULL,
    energy NUMERIC(12,4),
    protein NUMERIC(12,4),
    fat NUMERIC(12,4),
    carbohydrate NUMERIC(12,4),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS health_goal (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    goal_type VARCHAR(32) NOT NULL,
    target_value NUMERIC(12,4),
    current_value NUMERIC(12,4),
    start_date DATE,
    target_date DATE,
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS health_goal_progress (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    health_goal_id BIGINT NOT NULL REFERENCES health_goal(id) ON DELETE CASCADE,
    progress_date DATE NOT NULL,
    progress_value NUMERIC(12,4),
    note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS post (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    cover_image_url TEXT,
    status VARCHAR(32) NOT NULL DEFAULT 'published',
    audit_status VARCHAR(32) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS post_comment (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    post_id BIGINT NOT NULL REFERENCES post(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'visible',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS content_report (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    reporter_id BIGINT NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    target_type VARCHAR(32) NOT NULL,
    target_id BIGINT NOT NULL,
    reason TEXT NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    processed_by BIGINT REFERENCES app_user(id) ON DELETE SET NULL,
    processed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS external_data_source (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_name VARCHAR(64) NOT NULL,
    source_type VARCHAR(32) NOT NULL,
    api_endpoint TEXT,
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_external_data_source UNIQUE (source_name)
);

CREATE TABLE IF NOT EXISTS external_food_mapping (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_id BIGINT NOT NULL REFERENCES external_data_source(id) ON DELETE CASCADE,
    external_food_id VARCHAR(128) NOT NULL,
    canonical_ingredient_id BIGINT REFERENCES ingredient(id) ON DELETE SET NULL,
    external_name VARCHAR(255) NOT NULL,
    matched_score NUMERIC(12,4),
    raw_payload JSONB,
    synced_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_external_food_mapping UNIQUE (source_id, external_food_id)
);

CREATE TABLE IF NOT EXISTS report_task (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES app_user(id) ON DELETE CASCADE,
    report_type VARCHAR(32) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    file_url TEXT,
    start_date DATE,
    end_date DATE,
    generated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS system_log (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id BIGINT REFERENCES app_user(id) ON DELETE SET NULL,
    log_type VARCHAR(32) NOT NULL,
    module VARCHAR(64) NOT NULL,
    message TEXT NOT NULL,
    trace_id VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS system_config (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    config_key VARCHAR(128) NOT NULL,
    config_value TEXT,
    description TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_system_config_key UNIQUE (config_key)
);

-- Common indexes
CREATE INDEX IF NOT EXISTS idx_meal_record_user_date ON meal_record (user_id, record_date);
CREATE INDEX IF NOT EXISTS idx_user_behavior_user_recipe_type_time ON user_behavior (user_id, recipe_id, behavior_type, created_at);
CREATE INDEX IF NOT EXISTS idx_recommendation_log_user_time ON recommendation_log (user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_content_report_status_time ON content_report (status, created_at);
CREATE INDEX IF NOT EXISTS idx_recipe_status_meal_difficulty ON recipe (status, meal_type, difficulty);
CREATE INDEX IF NOT EXISTS idx_recipe_ingredient_recipe_ingredient ON recipe_ingredient (recipe_id, ingredient_id);
CREATE INDEX IF NOT EXISTS idx_post_status_time ON post (status, created_at);
CREATE INDEX IF NOT EXISTS idx_report_task_user_time ON report_task (user_id, created_at);

-- Helper trigger to keep updated_at current
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_app_user_updated_at ON app_user;
CREATE TRIGGER trg_app_user_updated_at
BEFORE UPDATE ON app_user
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_user_profile_updated_at ON user_profile;
CREATE TRIGGER trg_user_profile_updated_at
BEFORE UPDATE ON user_profile
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_user_health_condition_updated_at ON user_health_condition;
CREATE TRIGGER trg_user_health_condition_updated_at
BEFORE UPDATE ON user_health_condition
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_ingredient_updated_at ON ingredient;
CREATE TRIGGER trg_ingredient_updated_at
BEFORE UPDATE ON ingredient
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_ingredient_nutrition_updated_at ON ingredient_nutrition;
CREATE TRIGGER trg_ingredient_nutrition_updated_at
BEFORE UPDATE ON ingredient_nutrition
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_recipe_updated_at ON recipe;
CREATE TRIGGER trg_recipe_updated_at
BEFORE UPDATE ON recipe
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_meal_record_updated_at ON meal_record;
CREATE TRIGGER trg_meal_record_updated_at
BEFORE UPDATE ON meal_record
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_health_goal_updated_at ON health_goal;
CREATE TRIGGER trg_health_goal_updated_at
BEFORE UPDATE ON health_goal
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_post_updated_at ON post;
CREATE TRIGGER trg_post_updated_at
BEFORE UPDATE ON post
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_external_data_source_updated_at ON external_data_source;
CREATE TRIGGER trg_external_data_source_updated_at
BEFORE UPDATE ON external_data_source
FOR EACH ROW EXECUTE FUNCTION set_updated_at();
