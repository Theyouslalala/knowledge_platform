# API 参考文档

Base URL: `http://localhost:8000`

## 认证

### POST /api/v1/auth/register
注册新用户。

**Request Body:**
```json
{
  "email": "user@example.com",
  "username": "username",
  "password": "password123",
  "full_name": "Optional Name"
}
```

**Response:** `201 Created`
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### POST /api/v1/auth/login
用户登录。

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:** `200 OK`

### POST /api/v1/auth/refresh
刷新访问令牌。

## 用户

### GET /api/v1/users/me
获取当前用户信息。需要认证。

### PATCH /api/v1/users/me
更新用户信息。

## 项目

### POST /api/v1/projects
创建项目。

### GET /api/v1/projects
列出用户的所有项目。

### GET /api/v1/projects/{id}
获取项目详情。

### PATCH /api/v1/projects/{id}
更新项目。

### DELETE /api/v1/projects/{id}
归档项目（软删除）。

## 任务

### POST /api/v1/tasks/projects/{project_id}/tasks
在项目中创建任务。

### GET /api/v1/tasks/projects/{project_id}/tasks
列出项目中的任务。

### GET /api/v1/tasks/{id}
获取任务详情。

### POST /api/v1/tasks/{id}/execute
执行任务（启动 Agent 系统）。

## 文档

### POST /api/v1/documents/projects/{project_id}/documents
上传文档（multipart/form-data）。

### GET /api/v1/documents/projects/{project_id}/documents
列出项目中的文档。

### DELETE /api/v1/documents/{id}
删除文档。

## 导出

### GET /api/v1/export/tasks/json
导出任务为 JSON。

### GET /api/v1/export/tasks/csv
导出任务为 CSV。

## 搜索

### GET /api/v1/search/messages?query=xxx
搜索消息历史。

## 健康检查

### GET /health
返回服务状态。
