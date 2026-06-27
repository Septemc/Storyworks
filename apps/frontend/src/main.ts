import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'

import { createApp } from 'vue'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import App from './App.vue'
import './style.css'

const vuetify = createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'storyworks',
    themes: {
      storyworks: {
        dark: false,
        colors: {
          primary: '#1a73e8',
          secondary: '#5f6368',
          success: '#188038',
          warning: '#f9ab00',
          error: '#d93025',
          background: '#f8fafd',
          surface: '#ffffff',
        },
      },
    },
  },
  defaults: {
    VBtn: { rounded: 'sm' },
    VCard: { rounded: 'sm', elevation: 0 },
    VTextField: { variant: 'outlined', density: 'comfortable' },
    VTextarea: { variant: 'outlined', density: 'comfortable' },
    VSelect: { variant: 'outlined', density: 'comfortable' },
    VCombobox: { variant: 'outlined', density: 'comfortable' },
  },
})

createApp(App).use(vuetify).mount('#app')
