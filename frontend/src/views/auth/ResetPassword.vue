<template>
  <div class="reset-page">
    <div class="reset-container">
      <div class="logo">
        <h1>🏢 集团内部培训平台</h1>
        <p>设置新密码</p>
      </div>

      <div v-if="!success" class="form-item">
        <label>新密码</label>
        <input
          type="password"
          v-model="form.newPassword"
          placeholder="请输入新密码（至少6位）"
        />
      </div>

      <div v-if="!success" class="form-item">
        <label>确认密码</label>
        <input
          type="password"
          v-model="form.confirmPassword"
          placeholder="请再次输入新密码"
          @keyup.enter="handleSubmit"
        />
      </div>

      <div v-if="!success" class="form-item">
        <el-button type="primary" :loading="loading" @click="handleSubmit" style="width: 100%">
          重置密码
        </el-button>
      </div>

      <div v-if="success" class="success-box">
        <el-icon color="#67c23a" :size="48"><CircleCheck /></el-icon>
        <p>密码重置成功！</p>
        <el-button type="primary" style="margin-top: 20px" @click="goToLogin">
          返回登录
        </el-button>
      </div>

      <div v-if="error" class="error-box">
        <el-icon color="#f56c6c" :size="48"><CircleClose /></el-icon>
        <p>{{ error }}</p>
        <el-button type="primary" style="margin-top: 20px" @click="goBack">
          返回登录
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { resetPassword } from '@/api/auth'
import { ElMessage } from 'element-plus'
import { CircleCheck, CircleClose } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()

const loading = ref(false)
const success = ref(false)
const error = ref('')
const token = ref('')

const form = reactive({
  newPassword: '',
  confirmPassword: '',
})

onMounted(() => {
  token.value = route.query.token || ''
  if (!token.value) {
    error.value = '重置链接无效或已过期'
  }
})

async function handleSubmit() {
  error.value = ''

  if (!form.newPassword) {
    ElMessage.warning('请输入新密码')
    return
  }

  if (form.newPassword.length < 6) {
    ElMessage.warning('密码长度不能少于6位')
    return
  }

  if (form.newPassword !== form.confirmPassword) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }

  if (!token.value) {
    error.value = '重置链接无效或已过期'
    return
  }

  loading.value = true
  try {
    const res = await resetPassword(token.value, form.newPassword)
    if (res.code === 0) {
      success.value = true
    }
  } catch (err) {
    error.value = err.message || '重置失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

function goToLogin() {
  router.push('/login')
}

function goBack() {
  router.push('/login')
}
</script>

<style scoped>
.reset-page {
  font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
  background: var(--theme-gradient);
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.reset-container {
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
  border-color: var(--theme-primary);
}

.success-box,
.error-box {
  text-align: center;
  padding: 30px 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.error-box {
  background: #fef0f0;
}

.success-box p,
.error-box p {
  margin-top: 15px;
  color: #606266;
  font-size: 14px;
}
</style>
