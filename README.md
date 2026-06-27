# Storyworks 统一创作工作台

Storyworks 是面向互动叙事、修仙世界观和长篇剧本创作的统一工作台。当前主线应用已经合并为一个前端、一个后端和一个 SQLite 数据库，覆盖项目管理、世界书、人物卡、剧本、预设、AI 生成与迭代、跨模块引用、版本历史和导出。

旧的多模块应用目录和启动脚本仍保留作兼容参考；日常开发、验证和使用请以统一应用为主线。

## 当前主线

```text
apps/
  backend/        FastAPI 统一后端
  frontend/       Vue 3 + Vite + Vuetify 3 统一前端
data/
  storyworks.db   统一 SQLite 数据库
shared/
  config.py       全局配置读取
docs/
  Codex超长线目标Spec-Storyworks全面完善.md
```

## 快速启动

### Windows

双击或运行：

```bat
start.bat
```

默认地址：

- 前端：http://localhost:3000
- 后端：http://127.0.0.1:8000

### macOS / Linux / Git Bash

```bash
./start.sh
```

## 手动开发

后端：

```bash
cd apps/backend
pip install -r requirements.txt
python run.py --port 8000
```

前端：

```bash
cd apps/frontend
npm install
npm run dev -- --host 127.0.0.1 --port 3000
```

## 验证命令

后端：

```bash
python -m compileall apps/backend/app
python -m pytest apps/backend/tests
```

前端：

```bash
cd apps/frontend
npm run build
```

## 功能范围

- 项目管理：统一项目入口、项目切换、编辑、归档/恢复、确认删除、demo 重置和项目级数据隔离。
- 世界书：分类、条目、Markdown 正文、关系、图谱、AI 生成与迭代、版本历史、导出。
- 人物卡：Developer / Player 双视角、9 个通用核心分类、字段可见性、角色关系、世界书关联、AI 生成与迭代。
- 剧本：层级节点、Markdown 正文、角色与世界书引用、AI 生成与迭代、版本历史、导出。
- 预设：维度、文本块、应用场景、编译提示词、AI 生成/整理/迭代、组合与导出。

## AI 配置

复制 `config.example.json` 为本地 `config.json`，再填写自己的 AI 服务信息：

```json
{
  "ai": {
    "provider": "openai_compatible",
    "baseUrl": "https://example.com/v1",
    "apiKey": "your-api-key",
    "model": "your-model"
  }
}
```

不要把真实 API Key 提交到仓库。`config.json` 已作为本地文件忽略；也可以完全不写入文件，改用环境变量：

```bash
STORYWORKS_AI_BASE_URL=https://example.com/v1
STORYWORKS_AI_API_KEY=your-api-key
STORYWORKS_AI_MODEL=your-model
```

离线验证 AI 工作流时，可以启用 mock provider：

```bash
STORYWORKS_AI_PROVIDER=mock
```

mock 模式会返回确定性的结构化世界书、人物卡、剧本和预设结果，并写入 AI 历史，便于测试生成、迭代、预览、应用和日志闭环。无 API Key 且未启用 mock 时，普通 CRUD、demo 数据、构建和后端基础测试仍可运行；真实 AI 生成/迭代接口会返回配置错误。

## 长线完善方向

当前项目仍处于“统一原型向产品化系统过渡”的阶段。后续应按 `docs/Codex超长线目标Spec-Storyworks全面完善.md` 持续推进：

- 后端拆分 router / service / schema / migration。
- 前端拆分模块组件、API client 和 composables。
- 继续强化数据库迁移、引用一致性检查和 demo reset 验收。
- 完善 AI 预览、应用、版本、日志、回滚闭环。
- 增加 pytest、前端测试和端到端测试覆盖。
