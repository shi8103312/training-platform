import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import request from '@/utils/request'

const THEME_KEY = 'app_theme'
const VALID_THEMES = ['default', 'sky', 'forest', 'sunset', 'berry']

export const useThemeStore = defineStore('theme', () => {
  const themes = {
    default: {
      name: '默认蓝紫',
      primary: '#667eea',
      secondary: '#764ba2',
      gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      gradientStart: '#667eea',
      gradientEnd: '#764ba2',
    },
    sky: {
      name: '天空蓝',
      primary: '#69C0FF',
      secondary: '#36CFC9',
      gradient: 'linear-gradient(135deg, #69C0FF 0%, #36CFC9 100%)',
      gradientStart: '#69C0FF',
      gradientEnd: '#36CFC9',
    },
    forest: {
      name: '森林绿',
      primary: '#95DE64',
      secondary: '#29BF6B',
      gradient: 'linear-gradient(135deg, #95DE64 0%, #29BF6B 100%)',
      gradientStart: '#95DE64',
      gradientEnd: '#29BF6B',
    },
    sunset: {
      name: '日落橙',
      primary: '#FFD591',
      secondary: '#FFA940',
      gradient: 'linear-gradient(135deg, #FFD591 0%, #FFA940 100%)',
      gradientStart: '#FFD591',
      gradientEnd: '#FFA940',
    },
    berry: {
      name: '浆果红',
      primary: '#FF7875',
      secondary: '#D43A69',
      gradient: 'linear-gradient(135deg, #FF7875 0%, #D43A69 100%)',
      gradientStart: '#FF7875',
      gradientEnd: '#D43A69',
    },
  }

  // Initialize from localStorage, default to 'default'
  const currentTheme = ref(localStorage.getItem(THEME_KEY) || 'default')

  // Apply theme to document
  function applyTheme(themeName) {
    const theme = themes[themeName]
    if (!theme) {
      console.warn(`Theme ${themeName} not found, using default`)
      themeName = 'default'
    }

    const root = document.documentElement
    const t = themes[themeName]

    // Set CSS variables
    root.style.setProperty('--theme-primary', t.primary)
    root.style.setProperty('--theme-secondary', t.secondary)
    root.style.setProperty('--theme-gradient', t.gradient)
    root.style.setProperty('--theme-gradient-start', t.gradientStart)
    root.style.setProperty('--theme-gradient-end', t.gradientEnd)

    // Set data attribute for CSS selectors
    root.setAttribute('data-theme', themeName)
  }

  // Watch for theme changes and persist
  watch(currentTheme, (newTheme) => {
    if (VALID_THEMES.includes(newTheme)) {
      localStorage.setItem(THEME_KEY, newTheme)
      applyTheme(newTheme)
    } else {
      console.warn(`Invalid theme ${newTheme}, using default`)
      currentTheme.value = 'default'
    }
  })

  // Set theme and optionally save to server
  async function setTheme(themeName, saveToServer = false) {
    if (!VALID_THEMES.includes(themeName)) {
      console.warn(`Invalid theme ${themeName}`)
      return
    }

    currentTheme.value = themeName

    // Save to server if user is logged in
    if (saveToServer) {
      try {
        await request({
          url: '/v1/user/preferences',
          method: 'PUT',
          data: { theme: themeName },
        })
      } catch (error) {
        console.error('Failed to save theme to server:', error)
      }
    }
  }

  // Load theme from server preferences
  async function loadThemeFromServer() {
    try {
      const res = await request({
        url: '/v1/user/info',
        method: 'GET',
      })
      if (res.code === 0 && res.data?.preferences?.theme) {
        const serverTheme = res.data.preferences.theme
        if (VALID_THEMES.includes(serverTheme)) {
          // Only update if different from local
          if (currentTheme.value !== serverTheme) {
            currentTheme.value = serverTheme
          }
        }
      }
    } catch (error) {
      console.error('Failed to load theme from server:', error)
    }
  }

  // Initialize theme on first load
  applyTheme(currentTheme.value)

  return {
    currentTheme,
    themes,
    setTheme,
    loadThemeFromServer,
    applyTheme,
    VALID_THEMES,
  }
})
