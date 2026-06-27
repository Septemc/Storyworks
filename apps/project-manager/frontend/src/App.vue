<template>
  <v-app>
    <v-app-bar color="primary" density="comfortable">
      <v-app-bar-title>
        <v-icon icon="mdi-cube-outline" class="mr-2"></v-icon>
        Storyworks 项目管理
      </v-app-bar-title>
      <template v-slot:append>
        <v-btn icon="mdi-github" href="https://github.com" target="_blank"></v-btn>
      </template>
    </v-app-bar>

    <v-main>
      <router-view />
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
// App component
</script>

<style>
html {
  overflow-y: auto;
}
</style>
