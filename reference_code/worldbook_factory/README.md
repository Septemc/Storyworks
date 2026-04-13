# worldbook_factory

世界书工坊层，负责**生成、修订、规整**世界书草稿，不直接读写数据库。

## 当前职责

- 接收来自 `gateway_frontend` 的工坊请求
- 通过 `BusinessBook + messaging` 进入 `worldbook_factory`
- 产出统一的：
  - `blueprint`
  - `payload`
  - `import_payload`
  - `overview`
  - `review`

## 边界说明

- **允许做**：自然语言到世界书草稿的启发式构建、分类规划、导入兼容性校验、前端展示摘要
- **不允许做**：直接访问数据库、直接写入世界书表、直接触发记忆索引重建

数据库写入仍由 `business_core` 负责，索引/向量准备仍由 `memory_knowledge` 或现有世界书导入链负责。

## 当前入口

- runtime: [runtime/worldbook_factory_runtime.py](/e:/文档/Storyteller-main/runtime/worldbook_factory_runtime.py)
- consumers:
  - [apps/worldbook_factory/message_consumers/generate_consumer.py](/e:/文档/Storyteller-main/apps/worldbook_factory/message_consumers/generate_consumer.py)
  - [apps/worldbook_factory/message_consumers/revise_consumer.py](/e:/文档/Storyteller-main/apps/worldbook_factory/message_consumers/revise_consumer.py)
- service:
  - [apps/worldbook_factory/service.py](/e:/文档/Storyteller-main/apps/worldbook_factory/service.py)

## 网关接口

`gateway_frontend` 当前暴露以下实验接口：

- `POST /experimental/worldbook-factory/blueprint`
- `POST /experimental/worldbook-factory/entries`
- `POST /experimental/worldbook-factory/generate`
- `POST /experimental/worldbook-factory/normalize`
- `POST /experimental/worldbook-factory/revise`

这些接口要求已登录用户，并由网关统一完成鉴权与错误映射。
