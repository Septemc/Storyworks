# 预设生成模板

## 系统提示
你是一个专业的写作风格分析师，擅长创建精确的风格预设。

## 用户提示
请根据以下信息生成一个风格预设：

**风格描述**: {{description}}
**参考文本** (可选): {{reference}}

## 要求
1. 风格必须明确、可执行
2. 不能写成模糊空话
3. 必须能影响实际输出
4. 用词、句式、节奏都要具体

## 输出格式 (JSON)
```json
{
  "name": "预设名称",
  "category": "分类 (文风/题材/剧情偏好/人物塑造/质量/输出格式)",
  "description": "一句话描述",
  "style": "风格名称",
  "word_tendency": "用词倾向描述",
  "sentence_pattern": "句式倾向描述",
  "description_density": "描写密度 (低/中/高)",
  "dialogue_ratio": "对白比例 (如 30%)",
  "rhythm": "节奏倾向 (快/中/慢/起伏)",
  "emotion_intensity": "情感浓度 (克制/中等/浓烈)",
  "plot_preference": "剧情偏好",
  "character_portrayal": "人物刻画偏好",
  "forbidden_expression": ["禁止表达1", "禁止表达2"],
  "output_requirements": "输出要求"
}
```
