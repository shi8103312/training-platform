<template>
  <div class="forgot-page">
    <div class="forgot-container">
      <div class="logo">
        <h1>🏢 集团内部培训平台</h1>
        <p>密码重置</p>
      </div>

      <div v-if="!submitted" class="form-item">
        <label>用户名</label>
        <input
          type="text"
          v-model="form.username"
          placeholder="请输入您的用户名"
          @keyup.enter="handleSubmit"
        />
      </div>

      <div v-if="!submitted" class="form-item">
        <el-button type="primary" :loading="loading" @click="handleSubmit" style="width: 100%">
          发送重置链接
        </el-button>
      </div>

      <div v-if="submitted && !resetLink" class="success-box">
        <el-icon color="#67c23a" :size="48"><CircleCheck /></el-icon>
        <p>如果用户名存在，重置链接已发送到您的邮箱</p>
      </div>

      <div v-if="resetLink" class="demo-box">
        <el-icon color="#e6a23c" :size="48"><Warning /></el-icon>
        <p style="margin-top: 10px; color: #606266;">演示模式：重置链接如下</p>
        <el-link type="primary" :href="resetLink" target="_blank" style="margin-top: 10px; word-break: break-all;">
          {{ resetLink }}
        </el-link>
        <el-button type="success" size="small" style="margin-top: 15px" @click="goToReset">
          跳转到重置页面
        </el-button>
      </div>

      <div class="back-link">
        <el-link type="primary" @click="goBack">返回登录</el-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { forgotPassword } from '@/api/auth'
import { ElMessage } from 'element-plus'
import { CircleCheck, Warning } from '@element-plus/icons-vue'

const router = useRouter()

const loading = ref(false)
const submitted = ref(false)
const resetLink = ref('')

const form = reactive({
  username: '',
})

async function handleSubmit() {
  if (!form.username) {
    ElMessage.warning('请输入用户名')
    return
  }

  loading.value = true
  try {
    const res = await forgotPassword(form.username)
    if (res.code === 0) {
      submitted.value = true
      if (res.data?.reset_link) {
        resetLink.value = res.data.reset_link
      }
    }
  } catch (error) {
    console.error('Forgot password error:', error)
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.push('/login')
}

function goToReset() {
  router.push({ name: 'ResetPassword', query: { token: resetLink.value.split('token=')[1] } })
}
</script>

<style scoped>
.forgot-page {
  font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.forgot-container {
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

.success-box,
.demo-box {
  text-align: center;
  padding: 30px 20px;
  background: #f5f7fa;
  border-radius: 8px;
  margin-bottom: 24px;
}

.demo-box {
  background: #fdf6ec;
}

.success-box p,
.demo-box p {
  margin-top: 15px;
  color: #606266;
  font-size: 14px;
}

.back-link {
  text-align: center;
  margin-top: 20px;
}
</style>
