<template>
  <el-dropdown trigger="click" @command="handleThemeChange">
    <span class="theme-switcher-trigger">
      <span class="theme-preview" :style="{ background: currentGradient }"></span>
      <span class="theme-name">{{ currentThemeName }}</span>
      <el-icon><ArrowDown /></el-icon>
    </span>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item
          v-for="(theme, key) in themes"
          :key="key"
          :command="key"
          :class="{ 'is-active': currentTheme === key }"
        >
          <span class="theme-option">
            <span class="theme-color-preview" :style="{ background: theme.gradient }"></span>
            <span>{{ theme.name }}</span>
            <el-icon v-if="currentTheme === key" class="check-icon"><Check /></el-icon>
          </span>
        </el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<script setup>
import { computed } from 'vue'
import { useThemeStore } from '@/stores/theme'
import { ArrowDown, Check } from '@element-plus/icons-vue'

const themeStore = useThemeStore()

const currentTheme = computed(() => themeStore.currentTheme)
const themes = themeStore.themes

const currentThemeName = computed(() => {
  return themes[currentTheme.value]?.name || '默认'
})

const currentGradient = computed(() => {
  return themes[currentTheme.value]?.gradient || themes.default.gradient
})

async function handleThemeChange(themeKey) {
  if (themeKey === currentTheme.value) return

  // Set locally first for immediate feedback
  themeStore.setTheme(themeKey, false)

  // Then save to server if logged in
  try {
    await themeStore.setTheme(themeKey, true)
  } catch (error) {
    console.error('Failed to save theme preference:', error)
  }
}
</script>

<style scoped>
.theme-switcher-trigger {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.1);
  transition: background 0.2s;
}

.theme-switcher-trigger:hover {
  background: rgba(255, 255, 255, 0.2);
}

.theme-preview {
  width: 20px;
  height: 20px;
  border-radius: 4px;
  flex-shrink: 0;
}

.theme-name {
  font-size: 13px;
  color: #fff;
}

.theme-option {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
}

.theme-color-preview {
  width: 24px;
  height: 24px;
  border-radius: 4px;
  flex-shrink: 0;
}

.check-icon {
  margin-left: auto;
  color: var(--theme-primary);
}

:deep(.el-dropdown-menu__item.is-active) {
  background: var(--el-fill-color-light);
  color: var(--theme-primary);
}
</style>
