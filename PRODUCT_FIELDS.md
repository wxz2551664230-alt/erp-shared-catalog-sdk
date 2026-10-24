# 产品台账适配（1.3.0）

仅保存可用于其他店铺重新上架的产品资料。不接收上架信息快照、店铺、售价库存、订单、核价结果或平台任务。

在原新增请求中可增加 `product_info` 对象；每个 `variants[]` 可增加 `net_weight_grams`。详情响应会返回这些字段。其他路径、匿名访问、wff/ready 归类与原样重放规则不变。旧请求不传新字段仍可重放。

## product_info

所有字段均可省略。字符串默认空，数组默认空，WB 子类目默认 null。拒绝未定义字段。长度按字符数。

| 字段 | 类型/限制 | 台账对应 |
| --- | --- | --- |
| description | string，最多 20000 | 商品描述，作为新文案参考 |
| search_tags | string[]，最多 100 项，每项非空且最多 300 字符 | 搜索标签；按标签拆分，不传一整个 JSON 字符串 |
| purchase_url | string，最多 4000 | 1688采购链接 |
| ozon_source_url | string，最多 4000 | Ozon来源链接 |
| wb_source_url | string，最多 4000 | WB来源链接 |
| category_name | string，最多 800 | 类目名称/路径 |
| attributes_platform | `"ozon"`、`"wildberries"` 或空字符串 | 属性所属平台，避免跨平台直接套用 |
| wb_subject_id | 正整数或 null | WB子类目ID |
| attributes | ProductAttribute[]，最多 200 项 | 普通属性JSON解析后的数组 |
| complex_attributes | ComplexAttribute[]，最多 100 组 | 组合属性JSON解析后的数组 |

链接沿用公开 HTTPS 规则：无查询串、片段、用户名密码，不接受“测试”或本机路径。含追踪参数的参考链接需先确认移除参数仍指向同一商品，再使用规范地址；无法确认则留空。原 `source_url` 保留兼容，不要再把平台参考链接当作采购链接。

`ProductAttribute`：`id` 必填正整数；`complex_id` 可省略，默认 0，非负整数；`name` 可省略，最多 300 字符；`values` 默认空数组，最多 100 项。每项 `value` 是字符串（默认空，最多 6000 字符），`dictionary_value_id` 是非负整数或 null（默认 null）。

`ComplexAttribute`：只有 `attributes` 字段，格式为 ProductAttribute[]，默认空数组，最多 100 项。不是任意原始对象的存储入口。第三方平台其他格式需显式转换，不能直接发送含店铺信息的 payload。

## 规格与原字段

| 台账字段 | 接口字段 | 规则 |
| --- | --- | --- |
| 货号 | sku、variants[].sku | 保持稳定；多规格先按产品分组，不因多店铺发布重复建品 |
| 商品标题 | name | 保存参考名称；新店铺仍生成新文案 |
| 型号名称 | variants[].specification | 规格说明 |
| 采购成本 | variants[].purchase_price_cny | CNY，非负数或 null，不能用售价替代 |
| 包装长度/宽度/高度 | variants[].package_length_mm / package_width_mm / package_height_mm | mm，正数或 null |
| 包装毛重 | variants[].weight_grams | g，正数或 null；发布/物流使用毛重 |
| 商品净重 | variants[].net_weight_grams | 新增，g，正数或 null；不能代替毛重 |
| 类目ID、类型ID | description_category_id、type_id | 顶层正整数或 null；OZON 参考类目 |
| 主图/附图/全部图片链接JSON | variants[].images | 合并去重，主图第一，最多 15 张；JSON 要解析为数组 |

不传净重时保持 null，不能按毛重推算。描述、标签、属性用于新发布的资料参考，不能把原店铺成功文案直接复用到新上架任务。不同平台的类目和字典仍需重新核对。

## 新增示例片段

以下两部分加入原请求，完整示例见 [examples/product.json](examples/product.json)：

```json
{
  "product_info": {
    "description": "可调节阻力握力器，塑料手柄与金属弹簧。",
    "search_tags": ["握力器", "手部训练"],
    "purchase_url": "",
    "ozon_source_url": "https://www.ozon.ru/product/example-123/",
    "category_name": "运动与休闲 / 健身 / 握力器",
    "attributes_platform": "ozon",
    "attributes": [{"id": 10097, "values": [{"value": "蓝色"}]}],
    "complex_attributes": []
  },
  "variants": [{"sku": "DEMO-200", "weight_grams": 149, "net_weight_grams": 130}]
}
```

API 仍为单产品请求；较大属性资料遇到 413 时应检查请求体大小，不要重复紧密重试或静默截断字段。

## 已上传产品

这次增加字段不提供公开修改权限。同一 `source + external_id` 新增更多资料属于内容变化，仍返回 409。开发者应保存原始上传 JSON，重试必须原样；已有记录需由 ERP 管理员确认补充，不能换编号重复上传。本次台账补充只按准确货号匹配既有产品，不新建未匹配商品。

读取时 `product_info` 在详情中返回，不在分页摘要中返回；`net_weight_grams` 在详情的各规格中返回。缺失资料显示“未提供”，不补零、不臆测。
