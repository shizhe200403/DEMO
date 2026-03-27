# 数据库设计草案

## 1. 设计原则

- 以用户、菜谱、营养、记录、目标、反馈、内容审核为核心实体。
- 统一食材名称和营养口径，避免同义词和不同来源数据冲突。
- 支持外部开放平台数据接入，保留来源、版本、同步时间和归一化结果。
- 核心业务表保持规范化，统计型字段可通过异步任务冗余存储。

## 2. 核心实体

### 2.1 用户与权限

`user`
- `id`
- `username`
- `email`
- `phone`
- `password_hash`
- `role`
- `status`
- `avatar_url`
- `nickname`
- `signature`
- `last_login_at`
- `created_at`
- `updated_at`

`user_profile`
- `id`
- `user_id`
- `gender`
- `birthday`
- `height_cm`
- `weight_kg`
- `target_weight_kg`
- `activity_level`
- `occupation`
- `budget_level`
- `cooking_skill`
- `meal_preference`
- `diet_type`
- `is_outdoor_eating_frequent`
- `household_size`
- `created_at`
- `updated_at`

`user_health_condition`
- `id`
- `user_id`
- `has_allergy`
- `allergy_tags`
- `avoid_food_tags`
- `religious_restriction`
- `has_hypertension`
- `has_diabetes`
- `has_hyperlipidemia`
- `is_pregnant`
- `is_lactating`
- `notes`
- `created_at`
- `updated_at`

## 3. 菜谱与食材

`recipe`
- `id`
- `title`
- `cover_image_url`
- `description`
- `portion_size`
- `servings`
- `difficulty`
- `cook_time_minutes`
- `prep_time_minutes`
- `meal_type`
- `taste_tags`
- `cuisine_tags`
- `status`
- `source_type`
- `source_name`
- `audit_status`
- `created_by`
- `created_at`
- `updated_at`

`recipe_step`
- `id`
- `recipe_id`
- `step_no`
- `content`
- `step_image_url`
- `created_at`

`ingredient`
- `id`
- `canonical_name`
- `alias_names`
- `category`
- `default_unit`
- `is_common`
- `created_at`
- `updated_at`

`recipe_ingredient`
- `id`
- `recipe_id`
- `ingredient_id`
- `amount`
- `unit`
- `is_main`
- `remark`

`ingredient_nutrition`
- `id`
- `ingredient_id`
- `source`
- `source_version`
- `per_100g_energy`
- `per_100g_protein`
- `per_100g_fat`
- `per_100g_carbohydrate`
- `per_100g_fiber`
- `per_100g_sodium`
- `per_100g_calcium`
- `per_100g_iron`
- `per_100g_vitamin_a`
- `per_100g_vitamin_c`
- `raw_payload`
- `created_at`
- `updated_at`

`recipe_nutrition_summary`
- `id`
- `recipe_id`
- `per_serving_energy`
- `per_serving_protein`
- `per_serving_fat`
- `per_serving_carbohydrate`
- `per_serving_fiber`
- `per_serving_sodium`
- `per_serving_calcium`
- `per_serving_iron`
- `per_serving_vitamin_a`
- `per_serving_vitamin_c`
- `calculation_method`
- `calculated_at`

## 4. 推荐与行为

`user_behavior`
- `id`
- `user_id`
- `recipe_id`
- `behavior_type`
- `behavior_value`
- `context_scene`
- `created_at`

`recommendation_log`
- `id`
- `user_id`
- `recipe_id`
- `score`
- `reason_text`
- `source_model`
- `recommendation_scene`
- `created_at`

`user_feedback`
- `id`
- `user_id`
- `recipe_id`
- `feedback_type`
- `rating`
- `comment`
- `created_at`

## 5. 饮食记录与目标

`meal_record`
- `id`
- `user_id`
- `record_date`
- `meal_type`
- `source_type`
- `note`
- `created_at`
- `updated_at`

`meal_record_item`
- `id`
- `meal_record_id`
- `recipe_id`
- `ingredient_name_snapshot`
- `amount`
- `unit`
- `energy`
- `protein`
- `fat`
- `carbohydrate`
- `created_at`

`health_goal`
- `id`
- `user_id`
- `goal_type`
- `target_value`
- `current_value`
- `start_date`
- `target_date`
- `status`
- `description`
- `created_at`
- `updated_at`

`health_goal_progress`
- `id`
- `health_goal_id`
- `progress_date`
- `progress_value`
- `note`
- `created_at`

## 6. 社区与内容治理

`post`
- `id`
- `user_id`
- `title`
- `content`
- `cover_image_url`
- `status`
- `audit_status`
- `created_at`
- `updated_at`

`post_comment`
- `id`
- `post_id`
- `user_id`
- `content`
- `status`
- `created_at`

`content_report`
- `id`
- `reporter_id`
- `target_type`
- `target_id`
- `reason`
- `status`
- `processed_by`
- `processed_at`
- `created_at`

## 7. 外部数据接入

`external_data_source`
- `id`
- `source_name`
- `source_type`
- `api_endpoint`
- `status`
- `created_at`
- `updated_at`

`external_food_mapping`
- `id`
- `source_id`
- `external_food_id`
- `canonical_ingredient_id`
- `external_name`
- `matched_score`
- `raw_payload`
- `synced_at`

## 8. 报表与系统管理

`report_task`
- `id`
- `user_id`
- `report_type`
- `status`
- `file_url`
- `start_date`
- `end_date`
- `generated_at`

`system_log`
- `id`
- `user_id`
- `log_type`
- `module`
- `message`
- `trace_id`
- `created_at`

`system_config`
- `id`
- `config_key`
- `config_value`
- `description`
- `updated_at`

## 9. 关键索引建议

- `user(email)`, `user(phone)` 唯一索引。
- `recipe(status, meal_type, difficulty)` 联合索引。
- `recipe_ingredient(recipe_id, ingredient_id)` 联合索引。
- `meal_record(user_id, record_date)` 联合索引。
- `user_behavior(user_id, recipe_id, behavior_type, created_at)` 联合索引。
- `recommendation_log(user_id, created_at)` 索引。
- `content_report(status, created_at)` 索引。

## 10. 设计说明

- 菜谱营养不要直接只存原始食材数据，建议同时存计算后的汇总结果，减少查询时重复计算。
- 用户行为和反馈是推荐系统核心训练数据，必须保留完整时间戳。
- 外部 API 同步结果要保留原始 payload，方便后续数据纠错和追溯。
- 后台审核流和社区治理建议独立建模，避免和核心菜谱数据耦合过重。
