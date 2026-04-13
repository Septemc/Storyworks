import { createRouter, createWebHistory } from 'vue-router'

import CharactersPage from '@/pages/CharactersPage.vue'
import HomePage from '@/pages/HomePage.vue'
import PresetsPage from '@/pages/PresetsPage.vue'
import ProjectsPage from '@/pages/ProjectsPage.vue'
import SettingsPage from '@/pages/SettingsPage.vue'
import ScriptsPage from '@/pages/ScriptsPage.vue'
import WorldbookPage from '@/pages/WorldbookPage.vue'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: HomePage },
    { path: '/projects', name: 'projects', component: ProjectsPage },
    { path: '/characters', name: 'characters', component: CharactersPage },
    { path: '/presets', name: 'presets', component: PresetsPage },
    { path: '/scripts', name: 'scripts', component: ScriptsPage },
    { path: '/worldbook', name: 'worldbook', component: WorldbookPage },
    { path: '/settings', name: 'settings', component: SettingsPage },
  ],
})
