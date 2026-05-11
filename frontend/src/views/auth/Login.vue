<template>
  <div class="login-page">
    <div class="login-container">
      <div class="logo">
        <h1>🏢 集团内部培训平台</h1>
        <p>数字化学习 · 便捷培训管理</p>
      </div>

      <div class="form-item">
        <label>用户名</label>
        <input
          type="text"
          v-model="form.username"
          placeholder="请输入工号或用户名"
          @keyup.enter="handleLogin"
        />
      </div>

      <div class="form-item">
        <label>密码</label>
        <input
          type="password"
          v-model="form.password"
          placeholder="请输入密码"
          @keyup.enter="handleLogin"
        />
      </div>

      <div class="remember-row">
        <label>
          <input type="checkbox" v-model="rememberMe" />
          记住登录状态
        </label>
        <a href="#" class="forgot-link">忘记密码？</a>
      </div>

      <button
        class="login-btn"
        @click="handleLogin"
        :disabled="loading"
      >
        {{ loading ? '登录中...' : '登 录' }}
      </button>

     
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const loading = ref(false)
const rememberMe = ref(false)

const form = reactive({
  username: '',
  password: '',
})

async function handleLogin() {
  if (!form.username || !form.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }

  loading.value = true
  try {
    const result = await userStore.login(form.username, form.password)

    if (result.success) {
      ElMessage.success('登录成功')
      const redirect = route.query.redirect || (userStore.isHrAdmin ? '/hr' : '/')
      router.push(redirect)
    } else {
      ElMessage.error(result.message || '登录失败')
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.login-page {
  font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-container {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  width: 420px;
  padding: 50px 40px;
}

.logo {
  text-align: center;
  margin-bottom: 40px;
}

.logo h1 {
  color: #333;
  font-size: 24px;
  font-weight: 600;
}

.logo p {
  color: #666;
  font-size: 14px;
  margin-top: 8px;
}

.form-item {
  margin-bottom: 24px;
}

.form-item label {
  display: block;
  color: #333;
  font-size: 14px;
  margin-bottom: 8px;
  font-weight: 500;
}

.form-item input {
  width: 100%;
  height: 44px;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  padding: 0 15px;
  font-size: 14px;
  transition: border-color 0.3s;
}

.form-item input:focus {
  outline: none;
  border-color: #667eea;
}

.remember-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.remember-row label {
  display: flex;
  align-items: center;
  color: #666;
  font-size: 14px;
  cursor: pointer;
}

.remember-row input[type="checkbox"] {
  width: 16px;
  height: 16px;
  margin-right: 6px;
}

.forgot-link {
  color: #667eea;
  font-size: 14px;
  text-decoration: none;
}

.forgot-link:hover {
  text-decoration: underline;
}

.login-btn {
  width: 100%;
  height: 46px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.login-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
}

.login-btn:active:not(:disabled) {
  transform: translateY(0);
}

.login-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.demo-hint {
  margin-top: 30px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 6px;
  font-size: 12px;
  color: #666;
  text-align: left;
}

.demo-hint strong {
  color: #333;
}

.demo-hint em {
  color: #999;
  font-size: 11px;
  font-style: normal;
}
</style>
