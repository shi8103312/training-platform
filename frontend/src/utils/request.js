import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'
import { useUserStore } from '@/stores/user'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
})

// Token refresh state
let isRefreshing = false
let refreshSubscribers = []

// Add request to queue
function subscribeTokenRefresh(callback) {
  refreshSubscribers.push(callback)
}

// Process queued requests after token refresh
function onTokenRefreshed(token) {
  refreshSubscribers.forEach(callback => callback(token))
  refreshSubscribers = []
}

// Decode JWT token
function decodeToken(token) {
  try {
    const payload = token.split('.')[1]
    return JSON.parse(atob(payload))
  } catch {
    return null
  }
}

// Check if token is about to expire (within 5 minutes)
function isTokenExpiringSoon() {
  const token = localStorage.getItem('token')
  if (!token) return true

  const payload = decodeToken(token)
  if (!payload || !payload.exp) return true

  const now = Math.floor(Date.now() / 1000)
  const expiresIn = payload.exp - now

  // Refresh if expires within 5 minutes
  return expiresIn < 300
}

// Refresh access token
async function refreshToken() {
  const refreshToken = localStorage.getItem('refreshToken')
  if (!refreshToken) {
    return null
  }

  try {
    const response = await axios.post(
      `${import.meta.env.VITE_API_BASE_URL || '/api'}/v1/auth/refresh`,
      { refresh_token: refreshToken }
    )

    if (response.data.code === 0) {
      const newToken = response.data.data.token
      localStorage.setItem('token', newToken)
      localStorage.setItem('refreshToken', response.data.data.refresh_token)
      return newToken
    }
  } catch (error) {
    console.error('Token refresh failed:', error)
  }

  return null
}

// Request interceptor
request.interceptors.request.use(
  async (config) => {
    const token = localStorage.getItem('token')

    if (token && isTokenExpiringSoon()) {
      if (!isRefreshing) {
        isRefreshing = true
        const newToken = await refreshToken()
        isRefreshing = false

        if (newToken) {
          onTokenRefreshed(newToken)
        } else {
          // Refresh failed, redirect to login
          localStorage.removeItem('token')
          localStorage.removeItem('refreshToken')
          router.push('/login')
          return Promise.reject(new Error('Token expired'))
        }
      } else {
        // Wait for token refresh to complete
        return new Promise((resolve) => {
          subscribeTokenRefresh((newToken) => {
            config.headers.Authorization = `Bearer ${newToken}`
            resolve(config)
          })
        })
      }
    }

    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
request.interceptors.response.use(
  (response) => {
    const { code, message } = response.data

    if (code === 0) {
      return response.data
    }

    // Business error
    ElMessage.error(message || '请求失败')
    return Promise.reject(new Error(message))
  },
  async (error) => {
    if (error.response) {
      const { status, data } = error.response

      switch (status) {
        case 401:
          // Token expired - clear everything and redirect to login
          ElMessage.error('登录已过期，请重新登录')
          localStorage.removeItem('token')
          localStorage.removeItem('refreshToken')

          // Clear store state
          const userStore = useUserStore()
          userStore.token = ''
          userStore.userInfo = null

          // Reject all queued requests
          refreshSubscribers = []
          isRefreshing = false

          // Navigate to login
          router.push('/login')
          return Promise.reject(error)
        case 403:
          // Don't show error if user has logged out (no token)
          if (localStorage.getItem('token')) {
            ElMessage.error('权限不足')
          }
          break
        case 404:
          ElMessage.error('资源不存在')
          break
        case 422:
          ElMessage.error('数据验证失败')
          break
        case 429:
          ElMessage.error('请求过于频繁')
          break
        case 500:
          ElMessage.error('服务器错误')
          break
        default:
          ElMessage.error(data?.message || '网络错误')
      }
    }
    return Promise.reject(error)
  }
)

export default request
