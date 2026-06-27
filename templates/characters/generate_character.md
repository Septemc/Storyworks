# 人物卡生成模板

## 系统提示
你是一个专业的角色设计助手，擅长创建立体、有深度的角色。

## 用户提示
请根据以下信息生成一个人物卡：

**角色概念**: {{concept}}
**角色类型**: {{character_type}} (主角/配角/反派/NPC)

{{#if world_context}}
**世界背景参考**:
{{world_context}}
{{/if}}

{{#if preset}}
**风格预设**:
{{preset}}
{{/if}}

## 要求
1. 角色必须形象鲜明、设定完整
2. 性格必须能对应行为倾向
3. 背景必须解释角色当前状态
4. 技能、装备必须符合世界设定
5. 必须包含 developer_mode 和 player_mode 两个视角

## 输出格式 (JSON)
```json
{
  "developer_mode": {
    "basic": {
      "name": "角色名",
      "identity": "身份",
      "level": "修为/等级",
      "summary": "一句话简述"
    },
    "knowledge": {
      "personality": "性格特征",
      "appearance": "外貌细节",
      "background": "背景故事",
      "motivation": "动机目标"
    },
    "secrets": {
      "trauma": "心理创伤",
      "hidden_identity": "隐藏身份",
      "secret": "其他秘密"
    },
    "attributes": {
      "health": "健康状态",
      "special": "特殊状态"
    },
    "relations": [
      {"target": "关系对象", "type": "关系类型", "description": "关系描述"}
    ],
    "inventory": [
      {"name": "物品名", "type": "类型", "description": "描述"}
    ],
    "skills": [
      {"name": "技能名", "level": "等级", "description": "描述"}
    ],
    "fortune": {
      "destiny_tags": ["天命标签"],
      "causal_hints": ["因果提示"]
    }
  },
  "player_mode": {
    "basic": { ... },
    "knowledge": { ... },
    "secrets": "未知",
    "attributes": { ... },
    "relations": [ ... ],
    "inventory": [ ... ],
    "skills": [ ... ],
    "fortune": "未知"
  }
}
```
