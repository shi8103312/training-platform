import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getUserInfo, login as apiLogin, logout as apiLogout } from '@/api/auth'
import router from '@/router'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(null)
  const loading = ref(false)

  const isLoggedIn = computed(() => !!token.value)
  const isHrAdmin = computed(() => userInfo.value?.role === 1)

  async function checkAuth() {
    if (!token.value) return

    try {
      await fetchUserInfo()
    } catch (error) {
      console.error('Auth check failed:', error)
      logout()
    }
  }

  async function fetchUserInfo() {
    loading.value = true
    try {
      const res = await getUserInfo()
      if (res.code === 0) {
        userInfo.value = res.data
      } else {
        throw new Error(res.message || '获取用户信息失败')
      }
    } finally {
      loading.value = false
    }
  }

  async function login(username, password) {
    loading.value = true
    try {
      const res = await apiLogin(username, password)
      if (res.code === 0) {
        token.value = res.data.token
        localStorage.setItem('token', res.data.token)
        localStorage.setItem('refreshToken', res.data.refresh_token)
        userInfo.value = res.data.user
        return { success: true }
      } else {
        return { success: false, message: res.message }
      }
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    try {
      await apiLogout()
    } catch (error) {
      console.error('Logout API failed:', error)
    } finally {
      token.value = ''
      userInfo.value = null
      localStorage.removeItem('token')
      localStorage.removeItem('refreshToken')
      router.push({ name: 'Login' })
    }
  }

  return {
    token,
    userInfo,
    loading,
    isLoggedIn,
    isHrAdmin,
    checkAuth,
    fetchUserInfo,
    login,
    logout,
  }
})