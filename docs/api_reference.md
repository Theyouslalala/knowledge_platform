# API 参考文档

Base URL: `http://localhost:8000`

Swagger UI: `http://localhost:8000/docs`

## 认证

所有需要认证的端点要求 `Authorization: Bearer <access_token>` 请求头。

### POST /api/v1/auth/register
注册新用户，返回 JWT 令牌。

**Request Body:**
```json
{
  "email": "user@example.com",      // max 254 字符，EmailStr 格式
  "username": "username",           // 3-50 字符，仅字母数字
  "password": "password123",        // 8-128 字符
  "full_name": "Optional Name"      // 可选，max 100 字符
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
  "email": "user@example.com",      // max 254 字符
  "password": "password123"         // max 128 字符
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### POST /api/v1/auth/refresh
刷新访问令牌。

**Request Body:**
```json
{
  "refresh_token": "eyJ..."         // max 2048 字符
}
```

## 用户

### GET /api/v1/users/me
获取当前用户信息。需要认证。

**Response:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "username": "username",
  "full_name": "Name",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### PATCH /api/v1/users/me
更新用户信息。需要认证。

## 项目

### POST /api/v1/projects
创建项目。需要认证。

**Request Body:**
```json
{
  "name": "My Project",
  "description": "Optional description"
}
```

**Response:** `201 Created`

### GET /api/v1/projects
列出用户的所有项目（排除 archived）。需要认证。支持分页。

**Query Parameters:**
| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `page` | int | 1 | 页码（≥1） |
| `page_size` | int | 20 | 每页数量（1-100） |

**Response:**
```json
{
  "items": [...],
  "total": 42,
  "page": 1,
  "page_size": 20
}
```

### GET /api/v1/projects/{id}
获取项目详情。需要认证，仅限项目所有者。

### PATCH /api/v1/projects/{id}
更新项目。需要认证。

### DELETE /api/v1/projects/{id}
归档项目（软删除，`status="archived"`）。需要认证。

## 任务

### POST /api/v1/tasks/projects/{project_id}/tasks
在项目中创建任务。需要认证。

**Request Body:**
```json
{
  "title": "Research task",
  "description": "Optional description",
  "task_type": "research",          // research | analysis | writing | complex
  "priority": "medium",             // low | medium | high | urgent
  "agent_config": {}                // 可选 Agent 配置
}
```

### GET /api/v1/tasks/projects/{project_id}/tasks
列出项目中的任务。需要认证。

### GET /api/v1/tasks/{id}
获取任务详情。需要认证。

### POST /api/v1/tasks/{id}/execute
执行任务（启动 Agent 系统，后台运行）。需要认证。

任务状态流转：`pending` → `executing` → `completed` / `failed`

## 文档

### POST /api/v1/documents/projects/{project_id}/documents
上传文档（`multipart/form-data`）。需要认证。

- 流式写入（64KB chunks），实时大小检查（上限 50MB）
- 支持格式：`.txt`、`.md`、`.pdf`、`.docx`
- 上传后自动触发后台 RAG 处理（分块 + 嵌入 + 存储）
- 文档状态：`pending` → `processing` → `completed` / `failed`

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "filename": "document.pdf",
  "file_type": "pdf",
  "file_size_bytes": 102400,
  "status": "pending",
  "chunk_count": 0
}
```

### GET /api/v1/documents/projects/{project_id}/documents
列出项目中的文档。需要认证。

### GET /api/v1/documents/{id}
获取文档详情。需要认证。

### DELETE /api/v1/documents/{id}
删除文档（同时删除物理文件）。需要认证。

## 对话

### GET /api/v1/conversations
列出用户的对话。需要认证。

### POST /api/v1/conversations
创建对话。需要认证。

### GET /api/v1/conversations/{id}/messages
获取对话消息。需要认证。支持分页。

**Query Parameters:**
| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `page` | int | 1 | 页码（≥1） |
| `page_size` | int | 50 | 每页数量（1-200） |

## Traces

### GET /api/v1/traces/{task_id}
获取任务的执行 Trace。需要认证。

**Response:**
```json
{
  "task_id": "xxx",
  "agents": [
    {
      "name": "planner",
      "start_time": 1234567890.0,
      "end_time": 1234567891.5,
      "duration_ms": 1500.0,
      "status": "completed"
    }
  ],
  "tool_calls": [...],
  "errors": []
}
```

### GET /api/v1/traces/{task_id}/tokens
获取任务的 Token 用量明细。需要认证。

### GET /api/v1/traces/tokens/summary
获取全局 Token 用量汇总。需要认证。

**Response:**
```json
{
  "total_tokens": 50000,
  "total_cost": 0.05,
  "total_records": 120,
  "by_agent": {...},
  "by_model": {...}
}
```

## 导出

### GET /api/v1/export/tasks/json
导出任务为 JSON。需要认证。

### GET /api/v1/export/tasks/csv
导出任务为 CSV。需要认证。

## 搜索

### GET /api/v1/search/messages?query=xxx
语义搜索消息历史。需要认证。

## 健康检查

### GET /health
返回服务状态。无需认证。

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "database": "connected"
}
```

## 错误响应格式

所有错误返回统一格式：

```json
{
  "error": "NOT_FOUND",
  "message": "Resource not found"
}
```

常见错误码：
| HTTP | Error Code | 说明 |
|------|-----------|------|
| 400 | `VALIDATION_ERROR` | 请求参数验证失败 |
| 401 | `AUTHENTICATION_ERROR` | 未认证或令牌过期 |
| 403 | `AUTHORIZATION_ERROR` | 无权限访问 |
| 404 | `NOT_FOUND` | 资源不存在 |
| 413 | - | 文件过大（>50MB） |
| 422 | - | 请求格式错误 |
| 429 | `RATE_LIMIT_ERROR` | 请求过于频繁 |
| 502 | `LLM_PROVIDER_ERROR` | LLM 服务不可用 |
