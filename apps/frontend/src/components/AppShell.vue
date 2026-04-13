<template>
  <div class="shell">
    <aside class="sidebar">
      <div class="brand">
        <h1>Storyworks</h1>
        <p>独立叙事资产工坊</p>
      </div>

      <nav class="nav">
        <RouterLink to="/">总览</RouterLink>
        <RouterLink to="/projects">项目</RouterLink>
        <RouterLink to="/characters">人物卡</RouterLink>
        <RouterLink to="/presets">预设</RouterLink>
        <RouterLink to="/scripts">剧本</RouterLink>
        <RouterLink to="/worldbook">世界书</RouterLink>
        <RouterLink to="/settings">设置</RouterLink>
      </nav>
    </aside>

    <main class="main">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
</script>
