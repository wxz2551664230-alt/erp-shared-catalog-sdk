# wff 产品库：开发者数据结构与接入说明

**1.3.0 产品资料扩展：**描述、标签、独立采购/参考链接、平台属性和净重见 [PRODUCT_FIELDS.md](PRODUCT_FIELDS.md)。不接收上架信息快照；旧请求保持兼容。

版本：1.3.0，2026-10-24。接口路径仍为 v1。服务根地址由管理员提供；下文域名、编号和商品均为示例。

## 入库位置与流程

外部程序调用新增接口 → ERP **产品库 → wff产品库** → 状态 **可发布（ready）**，不进入草稿。

`source_type=wff` 和 `status=ready` 由服务端填写，**不要放进上传请求**。这表示跳过草稿环节，不代表资料完整、平台审核通过或已上架。上传不会创建发布任务，也不会请求 OZON/WB。发布仍需补齐对应平台必填资料并经过现有确认流程。

这是共享数据库中的独立产品库分类，不是另建一套数据库。一个产品包含 1–100 个规格，每个规格可关联 0–15 个图片链接。其他程序通过接口读取和添加，无需直连数据库。

## 接口与访问

不需要用户名、密码、API Key 或 Cookie。请求和响应为 JSON；新增发送 `Content-Type: application/json`。

| 方法 | 完整路径 | 说明 |
| --- | --- | --- |
| GET | `/api/v1/shared-catalog/v1/capabilities` | `upload_library=wff`、`initial_status=ready` 表示支持本规则 |
| GET | `/api/v1/shared-catalog/v1/products` | 按产品 SKU 或名称搜索并分页 |
| GET | `/api/v1/shared-catalog/v1/products/{product_id}` | 产品及有效规格详情 |
| POST | `/api/v1/shared-catalog/v1/products` | 添加一个产品；相同请求可重放 |

公开读取保持原有范围：返回所有未归档产品库的公开字段，**不只 wff**。可按响应 `source_type` 在使用端区分。当前没有服务端 `source_type` 查询参数，也没有修改、删除、批量导入或增量订阅接口。网页 ERP 的管理接口不属于本协议。

## 上传：产品对象

未定义字段会返回 422。不要直接把读取响应或 OZON 发布请求原样上传。字符串字段会去掉首尾空白；可省略的字符串默认 `""`，不接受 `null`。数值未知应省略或传 `null`。

| 字段 | 类型 | 必填/默认 | 约束与含义 |
| --- | --- | --- | --- |
| source | string | 必填 | 来源程序名，1–60 字符，匹配 `^[a-z0-9][a-z0-9._-]{0,59}$`，例如 `ozon-seller-center` |
| external_id | string | 必填 | 1–200 字符；原系统稳定的产品身份，建议含固定实例/店铺命名空间；重试不可重新生成 |
| sku | string | 必填 | 1–200 字符；产品货号，不是 ERP 产品 ID |
| name | string | 必填 | 1–600 字符；产品名称 |
| supplier | string | `""` | 最多 120 字符；供应商名称 |
| source_url | string | `""` | 最多 4000 字符；非空须符合下方公开链接规则，未必是采购链接 |
| description_category_id | integer 或 null | null | 正整数；OZON 描述类目参考 ID，其他平台需自行映射 |
| type_id | integer 或 null | null | 正整数；OZON 商品类型参考 ID |
| variants | array<object> | 必填 | 1–100 个规格；同一产品内规格 SKU 不能重复 |

## 上传：variants 中的规格对象

| 字段 | 类型 | 必填/默认 | 约束与单位 |
| --- | --- | --- | --- |
| sku | string | 必填 | 1–200 字符；规格货号 |
| specification | string | `""` | 最多 500 字符；规格描述 |
| color | string | `""` | 最多 200 字符；颜色 |
| size | string | `""` | 最多 200 字符；尺码/尺寸描述，不等于包装尺寸 |
| purchase_price_cny | number 或 null | null | 采购成本，人民币元，≥0；不能填平台售价 |
| package_length_mm | number 或 null | null | 包装长度，毫米，>0 |
| package_width_mm | number 或 null | null | 包装宽度，毫米，>0 |
| package_height_mm | number 或 null | null | 包装高度，毫米，>0 |
| weight_grams | number 或 null | null | 重量，克，>0 |
| images | array<string> | `[]` | 最多 15 个不重复链接，每个不超过 4000 字符；第一个为主图 |

数值必须有限，不允许 NaN/Infinity。`null` 表示未知，不能用 0 代替未知尺寸重量。无图可传 `[]`，但实际发布时仍需补齐图片。

公开链接规则：HTTPS，默认端口或 443，无用户名密码、查询串 `?` 或片段 `#`；拒绝 localhost、单段主机名及私有/保留 IP 字面地址。不接受临时签名 URL、磁盘路径或 base64。服务器保存链接及关联，不负责永久托管，也不保证链接可下载；开发者应提供长期可访问图片并自行核验。

## 完整新增示例

```http
POST https://erp.example.com/api/v1/shared-catalog/v1/products
Content-Type: application/json
```

```json
{
  "source": "ozon-seller-center",
  "external_id": "demo-install:shop-a:product-200",
  "sku": "DEMO-200",
  "name": "示例桌旗",
  "supplier": "示例供应商",
  "source_url": "https://example.com/products/demo-200",
  "description_category_id": null,
  "type_id": null,
  "variants": [{
    "sku": "DEMO-200-BLUE",
    "specification": "蓝色 30×180cm",
    "color": "蓝色",
    "size": "30×180cm",
    "purchase_price_cny": 18.5,
    "package_length_mm": 300,
    "package_width_mm": 200,
    "package_height_mm": 20,
    "weight_grams": 180,
    "images": ["https://example.com/images/demo-200-blue.jpg"]
  }]
}
```

示例图片域名仅作格式展示。最少可仅提供 `source, external_id, sku, name, variants:[{sku:...}]`。

新增成功 HTTP 200：

```json
{"product_id":"0123456789abcdef0123456789abcdef","created":true,"replayed":false}
```

| 返回字段 | 类型 | 含义 |
| --- | --- | --- |
| product_id | string | ERP 产品 ID，32 位小写十六进制；保存下来供详情查询 |
| created | boolean | 本次是否新建 |
| replayed | boolean | 是否原样重放已有记录；此时 created=false，ID 不变 |

## 读取响应结构

搜索参数：`search` 字符串（默认空，最多 200 字符）；`limit` 整数（默认 50，1–100）；`after_id`（默认空，最多 32 字符，填上一页 next_cursor）。按产品 ID 升序；更换关键词清空游标。不是更新时间增量接口，遍历期间新增记录不保证出现在同一轮。

列表格式：

```json
{
  "items": [{
    "id": "0123456789abcdef0123456789abcdef",
    "sku": "DEMO-200",
    "name": "示例桌旗",
    "supplier": "示例供应商",
    "source_url": "https://example.com/products/demo-200",
    "description_category_id": null,
    "type_id": null,
    "status": "ready",
    "source_type": "wff",
    "updated_at": "2026-10-24T04:00:00+00:00"
  }],
  "next_cursor": null
}
```

`items` 是摘要数组；`next_cursor` 是字符串或 null，null 表示结束。摘要字段全部固定返回；供应商/链接可能为空、类目可能为 null。

| 读取专有字段 | 类型 | 含义 |
| --- | --- | --- |
| id | string | 产品/规格各自的 ERP ID，不等于 sku 或 external_id |
| source_type | string | 产品库标识：wff、pod、pod_amazon、follow、self_selected；客户端宜兼容未来新增值 |
| status | string | wff 新增为 ready；其他/历史记录可能是 draft 等状态；archived 不返回 |
| updated_at | string | ISO 8601 时间，按返回的时区偏移解析，不要假定北京时间 |
| variants | array<object> | 仅详情返回，有效规格列表；每项是上述规格字段加只读 id |

详情 `GET .../products/0123456789abcdef0123456789abcdef` 返回同一摘要对象并增加：

```json
{
  "variants": [{
    "id": "abcdef0123456789abcdef0123456789",
    "sku": "DEMO-200-BLUE",
    "specification": "蓝色 30×180cm",
    "color": "蓝色",
    "size": "30×180cm",
    "purchase_price_cny": 18.5,
    "package_length_mm": 300,
    "package_width_mm": 200,
    "package_height_mm": 20,
    "weight_grams": 180,
    "images": ["https://example.com/images/demo-200-blue.jpg"]
  }]
}
```

上面是详情增加部分，不是完整详情。图片为当前主图/附图公开链接，去重且主图优先；可能包含适用于整个产品的图片。内部原始快照、来源身份元数据、备注、店铺凭据和生产文件不公开返回。平台售价、库存、完整类目属性及历史发布文案不在本协议中。

## 防重复与错误处理

全局 `source + external_id` 是身份，不是密码；内容规范化后相同则返回原产品 ID。相同身份不同内容返回 409，不能通过更换身份绕过。SKU 相同并不自动合并；不要每次上传生成新的 external_id。

产品、规格和图片关联在同一事务中保存。网络超时后保留原始请求原样重试；不能因产品库失败重新执行平台上架。改归 wff 不改变既有产品 ID 或防重复身份。早期账号模式身份仍保留，既有产品不要批量重新上传。

| 状态码 | 处理 |
| --- | --- |
| 200 | 读取或新增成功，按 created/replayed 判断新建或重放 |
| 401/403 | 核对路径、版本、请求方式或浏览器来源限制；专用接口不要求登录 |
| 404 | 产品不存在、已归档或接口地址错误 |
| 409 | 来源身份内容冲突，人工核对原产品 |
| 422 | 按字段约束修正请求，包括多余字段 |
| 429 | 遵守 Retry-After，避免紧密重试 |
| 5xx/超时 | 结果未知，保留请求并有限退避后原样重试 |

错误结构及 SDK 示例见 [API.md](API.md)、[README.md](README.md)，机器可读字段见 [openapi.json](openapi.json)。本接入面向桌面/服务端程序；目前不提供跨站浏览器 CORS。
