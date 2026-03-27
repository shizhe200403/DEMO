# API 说明

详细接口列表见 [api_spec.md](/Users/shizhe/Downloads/demo/api_spec.md)。

## 统一响应

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

## 认证

- 注册：`POST /api/v1/accounts/register/`
- 登录：`POST /api/v1/accounts/login/`
- 刷新：`POST /api/v1/accounts/refresh/`
- 当前用户：`GET /api/v1/accounts/me/`

