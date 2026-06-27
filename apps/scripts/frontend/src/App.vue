<template>
  <v-app>
    <v-app-bar color="primary" density="comfortable">
      <v-app-bar-title>
        <v-icon icon="mdi-script-text" class="mr-2"></v-icon>
        Storyworks 剧本
      </v-app-bar-title>
      <template v-slot:append>
        <v-chip v-if="currentProject" color="white" variant="outlined" class="mr-2">
          {{ currentProject }}
        </v-chip>
      </template>
    </v-app-bar>
    <v-main>
      <router-view />
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useScriptStore } from '@/stores/script'
const store = useScriptStore()
const currentProject = computed(() => store.currentProject)
</script>
