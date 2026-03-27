# 后端接口清单草案

## 1. 通用约定

- 基础路径建议为 `/api/v1/`
- 请求和响应统一使用 JSON
- 所有鉴权接口使用 JWT Access Token
- 列表接口统一支持分页、筛选、排序
- 关键写操作需要参数校验和权限控制

### 1.1 统一响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

### 1.2 列表分页格式

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [],
    "page": 1,
    "page_size": 10,
    "total": 100
  }
}
```

## 2. 认证与用户

`POST /accounts/register`
- 注册用户

请求示例：

```json
{
  "username": "zhangsan",
  "email": "a@example.com",
  "phone": "13800000000",
  "password": "12345678"
}
```

`POST /accounts/login`
- 密码登录
支持 `account` 字段，账号可以是用户名、邮箱或手机号。

请求示例：

```json
{
  "account": "zhangsan",
  "password": "12345678"
}
```

`POST /accounts/login-code`
- 验证码登录，当前为规划项，尚未接入短信或邮箱验证码服务

请求示例：

```json
{
  "account": "13800000000",
  "verify_code": "123456"
}
```

`POST /accounts/logout`
- 退出登录，当前由前端清除 token 实现，服务端可视为客户端行为

`POST /accounts/refresh`
- 刷新令牌

`POST /accounts/reset-password`
- 重置密码，当前为规划项，后续可接入短信或邮箱验证

`GET /accounts/me`
- 获取当前用户信息

`PUT /accounts/me`
- 更新个人资料

`PUT /accounts/me/profile`
- 更新健康档案

请求示例：

```json
{
  "gender": "male",
  "birthday": "2000-01-01",
  "height_cm": 175,
  "weight_kg": 68.5,
  "target_weight_kg": 65,
  "activity_level": "medium",
  "diet_type": "high_protein"
}
```

`PUT /accounts/me/privacy`
- 更新隐私设置，当前为规划项，尚未实现

`PUT /accounts/me/health-condition`
- 更新过敏、忌口和慢病约束

`PUT /accounts/me/full-profile`
- 一次性更新基础资料、健康档案和约束信息

`DELETE /accounts/me`
- 注销账号

## 3. 菜谱管理

`GET /recipes`
- 菜谱列表

`POST /recipes`
- 新增菜谱

请求示例：

```json
{
  "title": "Steamed Egg",
  "description": "Simple and high protein breakfast",
  "portion_size": "1 serving",
  "servings": 1,
  "difficulty": "easy",
  "cook_time_minutes": 10,
  "prep_time_minutes": 5,
  "meal_type": "breakfast",
  "taste_tags": ["light"],
  "cuisine_tags": ["home-style"],
  "ingredients": [
    { "ingredient_id": 1, "amount": 2, "unit": "pcs", "is_main": true },
    { "ingredient_id": 2, "amount": 200, "unit": "ml", "is_main": false }
  ],
  "steps": [
    { "step_no": 1, "content": "Beat the eggs." },
    { "step_no": 2, "content": "Steam for 8 minutes." }
  ]
}
```

`GET /recipes/{id}`
- 菜谱详情

`PUT /recipes/{id}`
- 编辑菜谱

`DELETE /recipes/{id}`
- 删除或下架菜谱

`GET /recipes/search`
- 多条件搜索

`GET /recipes/recommend`
- 获取推荐菜谱

`GET /recipes/{id}/nutrition`
- 获取菜谱营养详情

`POST /recipes/{id}/favorite`
- 收藏菜谱

`DELETE /recipes/{id}/favorite`
- 取消收藏

`POST /recipes/{id}/feedback`
- 提交喜欢、不喜欢、评分等反馈

请求示例：

```json
{
  "feedback_type": "like",
  "rating": 5,
  "comment": "Suitable for breakfast"
}
```

## 4. 食材与营养

`GET /ingredients`
- 食材搜索

`GET /ingredients/{id}`
- 食材详情

`GET /nutrition/ingredients/search`
- 外部营养库查询入口

`POST /nutrition/calculate`
- 根据配料计算菜谱营养

请求示例：

```json
{
  "recipe_id": 1,
  "portion_multiplier": 1.0,
  "include_condiments": true
}
```

`GET /nutrition/dri`
- 获取营养参考摄入标准

`GET /nutrition/analysis`
- 返回个人营养分析结果

## 5. 饮食记录

`GET /meal-records`
- 饮食记录列表

`POST /meal-records`
- 新增饮食记录

请求示例：

```json
{
  "record_date": "2026-03-26",
  "meal_type": "lunch",
  "source_type": "manual",
  "items": [
    { "recipe_id": 1, "amount": 1, "unit": "serving" },
    { "ingredient_name_snapshot": "apple", "amount": 1, "unit": "piece" }
  ],
  "note": "Lunch at office"
}
```

`GET /meal-records/{id}`
- 饮食记录详情

`PUT /meal-records/{id}`
- 修改饮食记录

`DELETE /meal-records/{id}`
- 删除饮食记录

`GET /meal-records/statistics`
- 每日、每周、每月统计

`GET /meal-records/trend`
- 饮食趋势图数据

## 6. 健康目标

`GET /health-goals`
- 目标列表

`POST /health-goals`
- 新增目标

请求示例：

```json
{
  "goal_type": "weight_loss",
  "target_value": 65,
  "current_value": 68.5,
  "start_date": "2026-03-26",
  "target_date": "2026-06-26",
  "description": "Lose 3.5 kg in 3 months"
}
```

`GET /health-goals/{id}`
- 目标详情

`PUT /health-goals/{id}`
- 更新目标

`DELETE /health-goals/{id}`
- 删除目标

`POST /health-goals/{id}/progress`
- 录入目标进度

`GET /health-goals/{id}/progress`
- 获取目标进度

## 7. 社区模块

`GET /posts`
- 社区帖子列表

`POST /posts`
- 发布帖子

请求示例：

```json
{
  "title": "My healthy lunch",
  "content": "This recipe is easy and low fat.",
  "cover_image_url": "https://example.com/image.jpg"
}
```

`GET /posts/{id}`
- 帖子详情

`PUT /posts/{id}`
- 编辑帖子

`DELETE /posts/{id}`
- 删除帖子

`POST /posts/{id}/comments`
- 发表评论

`POST /posts/{id}/like`
- 点赞帖子

`POST /posts/{id}/report`
- 举报帖子或评论

`DELETE /comments/{id}`
- 隐藏评论，仅管理员或审核员可用

## 8. 推荐与行为数据

`POST /events/track`
- 记录浏览、停留、点击、收藏、评分等行为

请求示例：

```json
{
  "behavior_type": "view",
  "recipe_id": 1,
  "behavior_value": 12.5,
  "context_scene": "home"
}
```

`GET /recommendations/home`
- 首页推荐

`GET /recommendations/by-profile`
- 基于用户画像的冷启动推荐

`GET /recommendations/explain/{recipe_id}`
- 返回推荐理由

返回示例：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "recipe_id": 1,
    "reason_text": "Low fat, suitable for breakfast, matches high-protein preference"
  }
}
```

## 9. 报表与导出

`GET /reports/weekly`
- 周报

`GET /reports/monthly`
- 月报

`POST /reports/export`
- 导出 PDF 或其他文件

请求示例：

```json
{
  "report_type": "weekly",
  "start_date": "2026-03-20",
  "end_date": "2026-03-26",
  "format": "pdf"
}
```

`GET /reports/tasks/{id}`
- 查询报表生成任务状态

## 10. 后台管理

`GET /admin/users`
- 用户管理

`GET /admin/recipes`
- 菜谱审核列表

`POST /admin/recipes/{id}/audit`
- 审核菜谱

`POST /admin/posts/{id}/audit`
- 审核社区内容

`GET /admin/logs`
- 查看系统日志

`GET /admin/config`
- 查看系统配置

`PUT /admin/config`
- 更新系统配置

## 11. 外部 API 接口适配层

`GET /external/usda/search`
- USDA 食材查询代理

`GET /external/nutritionix/search`
- Nutritionix 食品查询代理

`GET /external/edamam/recipes`
- Edamam 菜谱查询代理

`GET /external/openfoodfacts/barcode/{code}`
- 条码营养查询代理

## 12. 接口实现建议

- 推荐和报表类接口要做缓存。
- 写操作要统一审计日志。
- 列表接口要支持分页、排序、过滤。
- 外部接口调用要做超时、重试和降级处理。
- 统一返回码，错误信息要可读，避免前端只能拿到模糊 500。

## 13. 建议补充的响应字段

- `request_id`：用于链路追踪。
- `timestamp`：用于调试和时序分析。
- `error_detail`：仅在开发或受控后台场景下返回。
- `next_cursor`：如果后续采用游标分页可加上。
