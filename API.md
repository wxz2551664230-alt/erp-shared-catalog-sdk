# API v1

所有路径相对于管理员提供的 HTTPS 根地址。SDK 仅允许远程 HTTPS；本机开发允许 HTTP localhost。请求 JSON，响应 JSON，不跟随重定向。

## 登录和权限

`POST /api/v1/auth/login`

```json
{"username":"YOUR_ACCOUNT","password":"ENTER_PRIVATELY","remember":false}
```

成功返回 HTTP 200 并设置 `erp_session` Cookie。后续请求带同一个 Cookie。使用个人产品库协作者账号，不分享管理员账号；不使用 Ozon API Key、店铺 Client ID 或数据库密码登录。SDK 用 `requests.Session` 保持会话；密码和 Cookie 不得进入日志、Git、提交备份或图片下载请求。

`POST /api/v1/auth/logout` 注销当前会话。401 表示需要重新登录；账号停用后不可继续使用。当前不提供独立长期 API Key。

## 接口

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| GET | `/api/v1/shared-catalog/v1/capabilities` | 协议版本及能力边界 |
| GET | `/api/v1/shared-catalog/v1/products` | 搜索及分页 |
| GET | `/api/v1/shared-catalog/v1/products/{id}` | 读取产品详情 |
| POST | `/api/v1/shared-catalog/v1/products` | 添加产品或重放原请求 |

### 搜索

参数 `search`（最多 200 字符，匹配名称或产品 SKU）、`limit`（1–100，默认 50）、`after_id`（上一页 `next_cursor`）。

返回 `{"items":[...],"next_cursor":null}`。`next_cursor` 为 null 时结束。换关键词时清空游标。按产品 ID 排序，不是按更新时间；查询不是快照或增量同步，遍历过程中新增的产品可能需要下一轮重新搜索。归档产品不返回。

摘要字段：`id, sku, name, supplier, source_url, description_category_id, type_id, status, updated_at`。`source_url` 不保证是采购链接；使用方需辨别来源。

### 详情

返回上述摘要字段及 `variants`。每个有效规格含 `id, sku, specification, color, size, purchase_price_cny, package_length_mm, package_width_mm, package_height_mm, weight_grams, images`。

`images` 最多 15 个公开 HTTPS 链接，按主图优先顺序排列，可能为空。不存在或已归档返回 404。不返回本机路径、内部备注、任意原始快照、店铺凭据或订单。

### 新增

请求见 [示例](examples/product.json) 和 [OpenAPI 字段约束](openapi.json)。拒绝未定义的字段；不要直接发送原平台 payload。

| 字段 | 要求 |
| --- | --- |
| source | 必填；1–60 字符，正则 `^[a-z0-9][a-z0-9._-]{0,59}$` |
| external_id | 必填；1–200 字符，来源系统的稳定产品身份 |
| sku | 必填；1–200 字符，产品 SKU |
| name | 必填；1–600 字符 |
| source_url | 可省略或空；非空须公开 HTTPS，不含认证参数、查询串或片段 |
| supplier | 可省略，最多 120 字符 |
| description_category_id / type_id | 可省略或 null；提供时为正整数 |
| variants | 必填；1–100 个，SKU 不重复 |

规格：`sku` 必填（1–200 字符）；`specification` 最多 500，`color/size` 最多 200，默认空字符串。`purchase_price_cny` 非负数或 null；尺寸重量为正数或 null，默认 null，不允许 NaN/Infinity。`images` 默认空数组，最多 15 个不重复的公开 HTTPS 链接，每个最多 4000 字符；不能携带认证参数、用户密码、查询串或片段。

成功均返回 HTTP 200：

```json
{"product_id":"0123456789abcdef0123456789abcdef","created":true,"replayed":false}
```

产品状态为 `draft`。相同身份与内容重试返回同一个 ID，`created=false,replayed=true`。身份绑定登录账号 + source + external_id，不同账号之间不共用幂等身份。同身份不同内容返回 409；原资料不会被覆盖。

一个产品及其规格、图片关联在同一事务内保存。网络超时不代表保存失败；原样重试确认，不能更换 external_id。请保持转换算法和原始 JSON 稳定，尤其不得把每次当前时间放入来源 ID。

## 错误与恢复

| HTTP | 处理 |
| --- | --- |
| 401 | 重新登录，不重复平台上架 |
| 403 | 联系管理员检查账号权限 |
| 404 | 产品不存在、已归档，或服务未部署对应接口 |
| 409 | 同一来源内容冲突，核对原产品；不能换 ID 绕过 |
| 422 | 字段、长度、URL、数值或格式错误 |
| 429 | 若网关限流，遵守 Retry-After；无该头时延后人工重试 |
| 5xx / 超时 | 结果可能未知，保留原始请求，有限退避或人工原样重试 |

错误一般包含 `code,message,trace_id`，422 可含 `details`。SDK 默认只报告 HTTP 状态，避免泄漏任意响应内容。应用可以记录脱敏 trace_id；不要记录密码、Cookie 或请求头。

API 不执行任何 OZON/WB 请求。使用库内资料创建新的平台上架任务前，使用者仍需核对店铺、类目、属性、图片、价格和库存，并生成新文案及确认提交。
