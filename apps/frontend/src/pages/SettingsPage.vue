<template>
  <section class="page">
    <header class="page-header">
      <div>
        <p class="eyebrow">设置</p>
        <h2>应用与发布信息</h2>
      </div>
    </header>

    <div class="grid">
      <article class="card">
        <h3>应用定位</h3>
        <ul class="list">
          <li>Storyworks 是独立运行的叙事资产辅助生成器。</li>
          <li>当前版本聚焦世界书、人物卡、剧本、预设四类创作资产。</li>
          <li>不承担检索、运行时拼装或主项目集成编排职责。</li>
        </ul>
      </article>

      <article class="card">
        <h3>当前环境</h3>
        <ul class="list">
          <li>前端：Vue 3 + Vite + Pinia + Vue Router</li>
          <li>后端：FastAPI + SQLAlchemy + SQLite</li>
          <li>接口地址：<code>{{ apiBaseUrl }}</code></li>
        </ul>
      </article>

      <article class="card">
        <h3>已完成模块</h3>
        <ul class="list">
          <li>项目管理：项目创建与项目切换。</li>
          <li>世界书：分类条目、草稿生成、导出。</li>
          <li>人物卡：模板驱动编辑、双视图结构、导出。</li>
          <li>剧本：结构化剧本编辑、草稿生成、导出。</li>
          <li>预设：风格配置、测试预览、导出。</li>
        </ul>
      </article>

      <article class="card">
        <h3>发布检查</h3>
        <ul class="list">
          <li>前端导航与模块页面已统一中文文案。</li>
          <li>通用错误提示已做中文化处理。</li>
          <li>阶段开发文档已持续补齐，支持首发演示与验收。</li>
        </ul>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'
</script>
