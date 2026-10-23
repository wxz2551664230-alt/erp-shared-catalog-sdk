# ERP 共享产品库接入包

供 `ozon-seller-center` 及其他上架程序接入同一个产品库：**读取产品资料、添加产品**。无需访问 ERP 数据库或取得 ERP 私有源码。

这是独立开发者接入包，不包含服务端、店铺账号、产品数据或服务器凭据。服务地址及个人“产品库协作者”账号由产品库管理员私下提供；仓库中的 `https://erp.example.com` 仅为占位地址。

## 包内文件

- [API.md](API.md)：鉴权、字段、分页、错误处理及兼容边界。
- [openapi.json](openapi.json)：仅包含接入所需接口，可导入 API 调试工具。
- [client.py](client.py)：Python SDK、命令行和 OZON 成功提交记录转换器。
- [examples/product.json](examples/product.json)：虚构商品的新增请求。
- [examples/integrate.py](examples/integrate.py)：程序调用示例，默认只读。
- [ACCEPTANCE.md](ACCEPTANCE.md)：开发者联调清单及服务部署状态。

## 快速开始

Python 3.10 或更高版本：

```shell
python -m pip install -r requirements.txt
python client.py --url https://erp.example.com --username YOUR_ACCOUNT search --text 桌旗
python client.py --url https://erp.example.com --username YOUR_ACCOUNT read PRODUCT_ID --output product.json
```

密码通过交互输入，SDK 不保存到文件。搜索返回产品 ID；不能将上面的 PRODUCT_ID 占位文本直接用于查询。

确认需要新增后：

```shell
python client.py --url https://erp.example.com --username YOUR_ACCOUNT upload examples/product.json
```

该命令会真实写入所连接的产品库，请先使用管理员指定的测试环境或获准的测试商品。示例图片域名是占位符，不是可用图片；测试纯资料入库可以把 `images` 改成空数组。

## 给 ozon-seller-center 开发者

在现有程序中增加“产品库连接”“从产品库选品”“添加到产品库”入口，并调用 SDK；不必使用 ERP 网页端或把上架程序部署到服务器。

1. 登录后调用 `search()` 和 `read()`，在程序中选择规格。成本单位 CNY、包装尺寸 mm、重量 g；`null` 表示未知，不等于 0。
2. 使用返回的公开图片链接，仅下载用户选中的规格图片。图片请求使用独立连接，不携带 ERP Cookie。
3. 商品基础资料填入本地上架工作台；重新选择店铺、类目并核验属性，生成本次新文案，经用户确认后走原平台上架流程。
4. 添加产品调用 `add()`，持久保存返回的 `product_id` 和原始请求。产品库失败单独处理，不要重跑 OZON 上架。

本包提供 `from_ozon_submission(document, source_store_id)`，可转换明确成功的 `submitted-*.json`，或用命令行先生成待核对请求：

```shell
python client.py --url https://erp.example.com --username YOUR_ACCOUNT prepare-ozon submitted-item.json --source-store-id ORIGINAL_STABLE_SHOP_ID --output upload.json
```

此命令不连接服务器。需要人工核对原始店铺和文件：同货号提交文件可能被其他店铺覆盖，不能凭当前选中店铺推断来源。转换器不推算采购成本，不把平台售价当成本；缺少明确成功回执或尺寸单位时拒绝。

原项目的 `/catalog/follow-backups/*` 接口与本协议不同，不能直接复用旧备份上传方法。请改接本包的 `/shared-catalog/v1/*`，不需要 Supabase。

## 能力边界

- “双向”指程序向库内添加、从库内读取，不是自动双向覆盖。
- 协作者不能修改或删除已有产品，也不能访问订单、店铺密钥、发布任务。
- 同一账号、来源程序和来源 ID 的完全相同请求可安全重试；内容改变返回 409，须人工核对。
- 不同账号或不同来源 ID 的相似商品不会自动合并。来源 ID 必须稳定，不能每次随机生成。
- 当前为公开图片链接，不提供图片文件上传和永久托管保证。
- 不提供平台售价、库存、完整类目属性、历史发布文案或增量更新订阅。其他上架软件须完成自己的字段适配，不能直接把读取结果当作平台发布请求。

## 本地验证

```shell
python -m unittest discover -s tests -v
```

测试只使用模拟连接和虚构数据，不访问真实 ERP、OZON、WB 或图片服务。
