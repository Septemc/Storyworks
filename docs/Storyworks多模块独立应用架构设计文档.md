# Storyworks 多模块独立应用架构设计文档

版本：v1.0
日期：2026-06-26
状态：架构设计基线稿

> 说明：本文定义 Storyworks 为多独立模块应用架构，每个模块（世界书、人物卡、剧本、预设）都是独立的小应用，可单独启动和使用，通过共享目录结构实现数据互通。

---

## 1. 项目定义

Storyworks 是面向互动叙事创作的多模块独立应用集合，包含五个独立应用：

| 应用               | 定位             | 核心职责                        |
| ------------------ | ---------------- | ------------------------------- |
| **项目管理** | 项目入口与管理   | 创建/管理项目，跳转到各功能模块 |
| **世界书**   | 世界观设定生成器 | 创建、编辑、生成世界设定资产    |
| **人物卡**   | 角色资料生成器   | 创建、编辑、生成角色卡片资产    |
| **剧本**     | 剧情结构生成器   | 创建、编辑、生成剧本约束文档    |
| **预设**     | 文风偏好生成器   | 创建、编辑、生成风格预设资产    |

**核心理念**：

- 每个模块都是独立的小应用，可单独启动/停止
- 通过约定的目录结构实现数据互通
- 共享项目管理入口，但各模块数据独立存储
- 所有模块可读取其他模块的数据用于关联生成

---

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                     项目管理应用                             │
│                   (独立入口应用)                              │
└─────────────────────────────────────────────────────────────┘
                            │
         ┌──────────────────┼──────────────────┐
         │                  │                  │
         ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   世界书应用  │  │   人物卡应用  │  │    剧本应用   │
│  (独立应用)   │  │  (独立应用)   │  │  (独立应用)   │
└──────────────┘  └──────────────┘  └──────────────┘
         │                  │                  │
         └──────────────────┼──────────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │   预设应用    │
                    │  (独立应用)   │
                    └──────────────┘
```

### 2.2 技术栈

| 层级                | 技术选择        | 说明                        |
| ------------------- | --------------- | --------------------------- |
| **前端框架**  | Vue 3 + Vite    | 响应式构建                  |
| **UI 组件库** | Vuetify 3       | Google Material Design 风格 |
| **后端框架**  | FastAPI         | Python 异步高性能           |
| **数据库**    | SQLite          | 轻量本地存储                |
| **数据格式**  | JSONL           | 可选，用于模板/配置         |
| **AI 服务**   | OpenAI 兼容接口 | deepseek-v4-pro             |

### 2.3 目录结构约定

所有应用共享统一的项目目录结构：

```
storyworks-projects/
├── {项目名称}/
│   ├── project.json           # 项目元数据
│   ├── worldbook/             # 世界书数据
│   │   ├── worldbook.db       # SQLite 数据库
│   │   └── export/            # 导出文件
│   ├── characters/            # 人物卡数据
│   │   ├── characters.db
│   │   └── export/
│   ├── scripts/               # 剧本数据
│   │   ├── scripts.db
│   │   └── export/
│   ├── presets/               # 预设数据
│   │   ├── presets.db
│   │   └── export/
│   └── templates/             # 项目自定义模板
│       ├── worldbook/
│       ├── characters/
│       ├── scripts/
│       └── presets/
├── templates/                 # 全局共享模板
│   ├── worldbook/
│   ├── characters/
│   ├── scripts/
│   └── presets/
└── config.json                # 全局配置（AI设置等）
```

---

## 3. 应用详细设计

### 3.1 项目管理应用

**职责**：作为统一入口，管理所有项目的生命周期

**功能范围**：

- 创建新项目（自动初始化目录结构）
- 查看/编辑项目信息
- 列出所有项目
- 跳转到各功能模块（带项目上下文）
- 全局设置（AI配置、模板管理等）

**数据结构**：

```json
// project.json
{
  "name": "我的故事项目",
  "description": "一个奇幻冒险故事",
  "genre": "奇幻",
  "created_at": "2026-06-26T10:00:00Z",
  "updated_at": "2026-06-26T10:00:00Z",
  "settings": {
    "default_ai_model": "deepseek-v4-pro",
    "default_preset": null
  }
}
```

**API 端点**：

- `GET /api/projects` - 获取项目列表
- `POST /api/projects` - 创建新项目
- `GET /api/projects/{id}` - 获取项目详情
- `PUT /api/projects/{id}` - 更新项目信息
- `DELETE /api/projects/{id}` - 删除项目

---

### 3.2 世界书应用

**职责**：管理世界观设定资产，支持AI生成和手动编辑

**功能范围**：

- 世界书条目的CRUD操作
- 分类管理（历史、地理、政治等）
- 条目关联（建立条目间关系）
- AI生成（从概念生成条目、扩写、润色）
- 模板应用
- 导出（Markdown、JSON）
- 读取其他模块数据（如人物卡、剧本引用的设定）

**数据结构**：

```sql
-- worldbook.db
CREATE TABLE worldbook_entries (
    id TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT,
    content TEXT,           -- JSON格式存储多个字段
    keywords TEXT,          -- JSON数组
    relations TEXT,         -- JSON数组，关联条目ID
    status TEXT DEFAULT 'draft',
    created_at DATETIME,
    updated_at DATETIME
);

CREATE TABLE world_blueprints (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    content TEXT,           -- JSON格式存储蓝图数据
    created_at DATETIME
);
```

**AI生成能力**：

- 从世界观概念生成世界蓝图
- 从分类生成条目草稿
- 从简略设定扩写为完整条目
- 条目语言润色与结构规范化

**API 端点**：

- `GET /api/worldbook/entries` - 获取条目列表
- `POST /api/worldbook/entries` - 创建条目
- `GET /api/worldbook/entries/{id}` - 获取条目详情
- `PUT /api/worldbook/entries/{id}` - 更新条目
- `DELETE /api/worldbook/entries/{id}` - 删除条目
- `POST /api/worldbook/generate` - AI生成条目
- `GET /api/worldbook/blueprints` - 获取蓝图列表
- `POST /api/worldbook/blueprints` - 创建蓝图

---

### 3.3 人物卡应用

**职责**：管理角色资料资产，支持双视角模式

**功能范围**：

- 人物卡的CRUD操作
- 双视角模式（developer_mode / player_mode）
- 模板系统（应用不同角色模板）
- AI生成（从概念生成角色、扩写、批量生成）
- 关联世界书（引用世界设定）
- 关联剧本（引用出场场景）
- 导出（Markdown、JSON）

**数据结构**：

```sql
-- characters.db
CREATE TABLE characters (
    id TEXT PRIMARY KEY,
    template_id TEXT,
    name TEXT NOT NULL,
    developer_mode TEXT,    -- JSON格式存储完整角色数据
    player_mode TEXT,       -- JSON格式存储玩家可见数据
    status TEXT DEFAULT 'draft',
    created_at DATETIME,
    updated_at DATETIME
);

CREATE TABLE character_templates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    structure TEXT,         -- JSON格式存储模板结构
    is_builtin BOOLEAN DEFAULT FALSE,
    created_at DATETIME
);
```

**双视角模式**：

- `developer_mode`：完整角色真相，包含秘密信息
- `player_mode`：玩家当前已知信息，未知内容标记为"未知"

**AI生成能力**：

- 从一句话角色概念生成完整角色卡
- 基于世界书背景生成角色
- 基于阵营批量生成角色
- 角色扩写与润色

**API 端点**：

- `GET /api/characters` - 获取角色列表
- `POST /api/characters` - 创建角色
- `GET /api/characters/{id}` - 获取角色详情
- `PUT /api/characters/{id}` - 更新角色
- `DELETE /api/characters/{id}` - 删除角色
- `POST /api/characters/generate` - AI生成角色
- `GET /api/characters/templates` - 获取模板列表
- `POST /api/characters/templates` - 创建模板

---

### 3.4 剧本应用

**职责**：管理剧情结构资产，约束剧情发展

**功能范围**：

- 剧本文档的CRUD操作
- 多层级结构（总纲→篇章→章节→场景）
- 场景卡管理
- 约束管理（硬约束、软约束、顺序约束等）
- AI生成（从概念生成总纲、拆解结构）
- 关联人物卡（引用出场角色）
- 关联世界书（引用世界设定）
- 导出（Markdown、JSON）

**数据结构**：

```sql
-- scripts.db
CREATE TABLE scripts (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    type TEXT,              -- 总纲/篇章/章节/场景
    parent_id TEXT,         -- 上级文档ID
    content TEXT,           -- JSON格式存储内容
    constraints TEXT,       -- JSON格式存储约束
    status TEXT DEFAULT 'draft',
    sort_order INTEGER,
    created_at DATETIME,
    updated_at DATETIME
);

CREATE TABLE script_characters (
    script_id TEXT,
    character_id TEXT,
    role TEXT,              -- 主角/配角/反派等
    PRIMARY KEY (script_id, character_id)
);
```

**场景卡结构**：

```json
{
  "scene_id": "scene_xxx",
  "title": "场景标题",
  "purpose": "场景目的",
  "characters": ["char_001", "char_002"],
  "location": "场景地点",
  "conflict": "场景冲突",
  "must_events": ["必须发生的事件"],
  "can_events": ["可发生的事件"],
  "forbidden_events": ["禁止发生的事件"],
  "end_condition": "结束条件"
}
```

**AI生成能力**：

- 从故事概念生成总纲
- 从总纲拆解篇章/章节
- 从章节生成场景卡
- 剧情约束建议

**API 端点**：

- `GET /api/scripts` - 获取剧本列表
- `POST /api/scripts` - 创建剧本
- `GET /api/scripts/{id}` - 获取剧本详情
- `PUT /api/scripts/{id}` - 更新剧本
- `DELETE /api/scripts/{id}` - 删除剧本
- `POST /api/scripts/generate` - AI生成剧本
- `GET /api/scripts/{id}/scenes` - 获取场景列表
- `POST /api/scripts/{id}/scenes` - 创建场景

---

### 3.5 预设应用

**职责**：管理风格预设资产，控制生成偏好

**功能范围**：

- 预设的CRUD操作
- 预设分类（文风、题材、剧情偏好等）
- 预设参数调整
- AI生成（从风格说明生成预设、从参考文本总结）
- 模板应用
- 导出（Markdown、JSON）

**数据结构**：

```sql
-- presets.db
CREATE TABLE presets (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT,
    description TEXT,
    content TEXT,           -- JSON格式存储预设参数
    status TEXT DEFAULT 'draft',
    created_at DATETIME,
    updated_at DATETIME
);
```

**预设参数结构**：

```json
{
  "style": "古风正剧",
  "word_tendency": "典雅、含蓄",
  "sentence_pattern": "长短句结合，多用四字词",
  "description_density": "中等",
  "dialogue_ratio": "40%",
  "rhythm": "平稳推进",
  "emotion_intensity": "克制",
  "plot_preference": "注重人物内心",
  "character_portrayal": "细腻刻画",
  "forbidden_expression": ["现代网络用语", "过于直白的表达"],
  "output_requirements": "保持古风韵味"
}
```

**AI生成能力**：

- 从一句风格说明生成预设
- 从参考文本总结预设
- 从题材类型生成通用预设
- 预设优化与改写

**API 端点**：

- `GET /api/presets` - 获取预设列表
- `POST /api/presets` - 创建预设
- `GET /api/presets/{id}` - 获取预设详情
- `PUT /api/presets/{id}` - 更新预设
- `DELETE /api/presets/{id}` - 删除预设
- `POST /api/presets/generate` - AI生成预设

---

## 4. 数据互通设计

### 4.1 互通机制

各模块通过直接读取其他模块的 SQLite 数据库文件实现数据互通，无需API调用。

**读取示例**：

```python
# 人物卡应用读取世界书数据
import sqlite3

def get_worldbook_context(project_path: str) -> dict:
    db_path = f"{project_path}/worldbook/worldbook.db"
    conn = sqlite3.connect(db_path)
    # 查询相关世界设定...
    return context_data
```

### 4.2 互通场景

| 源模块 | 目标模块 | 用途                   |
| ------ | -------- | ---------------------- |
| 世界书 | 人物卡   | 生成角色时引用世界背景 |
| 世界书 | 剧本     | 生成剧情时引用世界设定 |
| 人物卡 | 剧本     | 关联出场角色           |
| 人物卡 | 世界书   | 角色所属阵营/组织      |
| 剧本   | 人物卡   | 角色出场场景           |
| 预设   | 全部     | 应用风格偏好到生成过程 |

### 4.3 数据一致性

- 各模块数据独立存储，不强制同步
- 读取时实时加载，不缓存
- 删除源数据时，引用方需处理"引用丢失"情况
- 建议在UI中提示用户检查关联数据

---

## 5. 共享组件设计

### 5.1 可共享的前端组件

虽然各应用独立，但以下UI组件可以在各应用间复用：

| 组件                 | 用途                                 |
| -------------------- | ------------------------------------ |
| `ProjectSelector`  | 项目选择器（从项目管理应用获取数据） |
| `AiGenerator`      | AI生成对话框（统一的生成界面）       |
| `TemplateSelector` | 模板选择器                           |
| `ExportDialog`     | 导出对话框                           |
| `MarkdownEditor`   | Markdown编辑器                       |
| `StatusBadge`      | 状态标签                             |

### 5.2 共享方式

**方案A：NPM包**
将共享组件发布为NPM包，各应用通过依赖引入。

**方案B：Git Submodule**
将共享组件放在单独的仓库，各应用作为submodule引入。

**方案C：复制**
各应用各自维护一份共享组件副本（简单但维护成本高）。

**推荐**：初期使用方案C，待组件稳定后迁移至方案A。

---

## 6. AI服务设计

### 6.1 统一AI服务配置

所有应用共享相同的AI服务配置，存储在 `config.json`：

```json
{
  "ai": {
    "provider": "openai_compatible",
    "baseUrl": "https://opencode.ai/zen/go/v1",
    "apiKey": "sk-xxx",
    "model": "deepseek-v4-pro",
    "temperature": 0.7,
    "max_tokens": 4096
  }
}
```

### 6.2 AI生成工作流

```
用户输入 → 选择生成模式 → 组装Prompt → 调用AI服务 → 解析返回 → 填充到表单
```

### 6.3 Prompt模板管理

每种生成场景对应一个Prompt模板，存储在 `templates/` 目录：

```
templates/
├── worldbook/
│   ├── generate_entry.md      # 生成世界书条目
│   └── expand_entry.md        # 扩写条目
├── characters/
│   ├── generate_character.md  # 生成角色卡
│   └── batch_generate.md      # 批量生成
├── scripts/
│   ├── generate_outline.md    # 生成总纲
│   └── generate_scene.md      # 生成场景
└── presets/
    └── generate_preset.md     # 生成预设
```

---

## 7. 模板系统设计

### 7.1 模板层级

```
全局模板 (templates/)
    ↓ 继承
项目模板 (projects/{项目}/templates/)
    ↓ 覆盖
用户自定义
```

### 7.2 模板格式（JSONL）

```jsonl
{"id": "character_default", "name": "默认角色模板", "type": "character", "fields": [...]}
{"id": "worldbook_default", "name": "默认世界书模板", "type": "worldbook", "fields": [...]}
```

### 7.3 模板扩展

用户可以通过以下方式扩展模板：

1. 复制内置模板并修改
2. 创建全新的模板
3. 从其他项目导入模板

---

## 8. 启动与部署

### 8.1 独立启动

每个应用都有独立的启动脚本：

```bash
# 世界书应用
cd apps/worldbook
python run.py --port 8001

# 人物卡应用
cd apps/characters
python run.py --port 8002

# 剧本应用
cd apps/scripts
python run.py --port 8003

# 预设应用
cd apps/presets
python run.py --port 8004

# 项目管理应用
cd apps/project-manager
python run.py --port 8000
```

### 8.2 统一启动脚本（可选）

```bash
# start_all.sh
#!/bin/bash
cd apps/worldbook && python run.py --port 8001 &
cd apps/characters && python run.py --port 8002 &
cd apps/scripts && python run.py --port 8003 &
cd apps/presets && python run.py --port 8004 &
cd apps/project-manager && python run.py --port 8000 &
```

### 8.3 端口分配

| 应用     | 默认端口 |
| -------- | -------- |
| 项目管理 | 8000     |
| 世界书   | 8001     |
| 人物卡   | 8002     |
| 剧本     | 8003     |
| 预设     | 8004     |

---

## 9. 项目结构

```
storyworks/
├── apps/
│   ├── project-manager/          # 项目管理应用
│   │   ├── backend/
│   │   │   ├── app/
│   │   │   │   ├── main.py       # FastAPI入口
│   │   │   │   ├── api/          # API路由
│   │   │   │   ├── models/       # 数据模型
│   │   │   │   ├── services/     # 业务逻辑
│   │   │   │   └── core/         # 配置、工具
│   │   │   ├── requirements.txt
│   │   │   └── run.py
│   │   └── frontend/
│   │       ├── src/
│   │       │   ├── components/   # Vue组件
│   │       │   ├── views/        # 页面
│   │       │   ├── stores/       # Pinia状态
│   │       │   └── api/          # API调用
│   │       ├── package.json
│   │       └── vite.config.js
│   │
│   ├── worldbook/                # 世界书应用
│   │   ├── backend/
│   │   │   └── ... (同上结构)
│   │   └── frontend/
│   │       └── ... (同上结构)
│   │
│   ├── characters/               # 人物卡应用
│   │   ├── backend/
│   │   │   └── ...
│   │   └── frontend/
│   │       └── ...
│   │
│   ├── scripts/                  # 剧本应用
│   │   ├── backend/
│   │   │   └── ...
│   │   └── frontend/
│   │       └── ...
│   │
│   └── presets/                  # 预设应用
│       ├── backend/
│       │   └── ...
│       └── frontend/
│           └── ...
│
├── shared/                       # 共享组件/工具（可选）
│   ├── components/
│   ├── utils/
│   └── types/
│
├── templates/                    # 全局模板
│   ├── worldbook/
│   ├── characters/
│   ├── scripts/
│   └── presets/
│
├── docs/                         # 文档
│   └── Storyworks多模块独立应用架构设计文档.md
│
├── config.example.json           # 配置示例
└── README.md
```

---

## 10. MVP范围

### 10.1 第一阶段（核心闭环）

- [ ] 项目管理应用：创建/查看项目
- [ ] 世界书应用：基础CRUD + 1种AI生成
- [ ] 人物卡应用：基础CRUD + 双视角模式 + 1种AI生成
- [ ] 剧本应用：基础CRUD + 场景卡管理
- [ ] 预设应用：基础CRUD
- [ ] 导出功能：Markdown导出

### 10.2 第二阶段（功能完善）

- [ ] 各模块AI生成功能完善
- [ ] 模板系统实现
- [ ] 数据互通功能
- [ ] JSON导出
- [ ] 更多AI生成模式

### 10.3 第三阶段（体验优化）

- [ ] 共享组件抽取
- [ ] 错误处理完善
- [ ] 性能优化
- [ ] 用户引导

---

## 11. 开发规范

### 11.1 API规范

- RESTful风格
- 统一响应格式：
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {}
  }
  ```
- 错误响应：
  ```json
  {
    "code": 400,
    "message": "参数错误",
    "error": "详细错误信息"
  }
  ```

### 11.2 前端规范

- Vue 3 Composition API
- TypeScript（可选）
- Vuetify 3 组件规范
- Pinia 状态管理

### 11.3 后端规范

- FastAPI 最佳实践
- Pydantic 数据校验
- 异步编程
- 类型注解

---

## 12. 总结

Storyworks 多模块独立应用架构的核心特点：

1. **独立性**：每个模块都是独立应用，可单独启动/停止/部署
2. **数据互通**：通过约定的目录结构，各模块可直接读取其他模块的数据
3. **共享入口**：项目管理应用作为统一入口，管理所有项目
4. **统一AI**：所有模块共享相同的AI服务配置
5. **灵活模板**：支持全局模板和项目级自定义模板
6. **开发友好**：本地SQLite存储，无需复杂基础设施

这种架构既保持了各模块的独立性，又通过目录约定实现了数据互通，适合开发环境下的灵活使用。
