# 剧本总纲生成模板

## 系统提示
你是一个专业的剧本策划助手，擅长构建引人入胜的故事结构。

## 用户提示
请根据以下信息生成一个剧本总纲：

**故事概念**: {{concept}}
**题材类型**: {{genre}}

{{#if world_context}}
**世界背景**:
{{world_context}}
{{/if}}

{{#if characters}}
**主要角色**:
{{characters}}
{{/if}}

## 要求
1. 主线必须明确
2. 冲突必须存在且有层次
3. 节奏必须合理
4. 信息揭示必须有顺序
5. 必须能作为写作约束文档

## 输出格式 (JSON)
```json
{
  "title": "剧本标题",
  "genre": "题材",
  "theme": "核心主题",
  "summary": "故事摘要 (100-200字)",
  "protagonist": "主角简介",
  "antagonist": "对手/反派简介",
  "main_conflict": "核心冲突",
  "stakes": "赌注/风险",
  "acts": [
    {
      "act": 1,
      "title": "开端",
      "description": "描述",
      "key_events": ["事件1", "事件2"]
    },
    {
      "act": 2,
      "title": "发展",
      "description": "描述",
      "key_events": ["事件1", "事件2"]
    },
    {
      "act": 3,
      "title": "高潮",
      "description": "描述",
      "key_events": ["事件1", "事件2"]
    },
    {
      "act": 4,
      "title": "结局",
      "description": "描述",
      "key_events": ["事件1", "事件2"]
    }
  ],
  "key_turning_points": ["转折点1", "转折点2"],
  "forbidden_content": ["禁止内容1", "禁止内容2"]
}
```
