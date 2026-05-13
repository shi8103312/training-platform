<template>
  <div class="employee-layout">
    <!-- 顶部导航 -->
    <header class="header">
      <div class="header-left">
        <div class="logo">🏢 集团培训平台</div>
        <nav class="nav-links">
          <router-link to="/" :class="{ active: route.path === '/' }">我的学习</router-link>
          <router-link to="/training" :class="{ active: route.path.startsWith('/training') }">全部培训</router-link>
          <router-link to="/exam-history" :class="{ active: route.path === '/exam-history' }">我的考试</router-link>
          <router-link to="/notification" :class="{ active: route.path === '/notification' }">通知中心</router-link>
        </nav>
      </div>
      <div class="header-right">
        <el-badge :value="unreadCount" :max="99" class="notification-badge" v-if="unreadCount > 0">
          <span class="notification-icon" @click="goToNotification">🔔</span>
        </el-badge>
        <span v-else class="notification-icon" @click="goToNotification">🔔</span>
        <div class="user-info">
          <div class="avatar">👤</div>
          <span class="user-name">{{ userStore.userInfo?.real_name || '用户' }}</span>
        </div>
        <router-link v-if="userStore.isHrAdmin" to="/hr" class="hr-entry">
          ⚙️ 后台管理
        </router-link>
        <button class="logout-btn" @click="handleLogout">
          🚪 退出
        </button>
      </div>
    </header>

    <!-- 主内容 -->
    <main class="main-container">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { onMounted, onActivated, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useNotificationStore } from '@/stores/notification'
import { ElMessageBox, ElBadge } from 'element-plus'
import { storeToRefs } from 'pinia'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const notificationStore = useNotificationStore()

const { unreadCount } = storeToRefs(notificationStore)

function goToNotification() {
  router.push('/notification')
}

function handleLogout() {
  ElMessageBox.confirm('确定退出登录吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(() => {
    userStore.logout()
    router.push('/login')
  })
}

onMounted(() => {
  notificationStore.fetchUnreadCount()
  notificationStore.startPolling(30000) // Poll every 30 seconds
})

// Refresh when coming back from notification page
onActivated(() => {
  notificationStore.fetchUnreadCount()
})

onUnmounted(() => {
  notificationStore.stopPolling()
})
</script>

<style scoped>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.employee-layout {
  font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
  background: #f5f7fa;
  min-height: 100vh;
}

.header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  padding: 0 30px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 30px;
}

.logo {
  font-size: 18px;
  font-weight: 600;
}

.nav-links {
  display: flex;
  gap: 25px;
}

.nav-links a {
  color: rgba(255, 255, 255, 0.8);
  text-decoration: none;
  font-size: 14px;
  padding: 8px 0;
  border-bottom: 2px solid transparent;
  transition: all 0.3s;
}

.nav-links a:hover,
.nav-links a.active {
  color: #fff;
  border-bottom-color: #fff;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.notification-badge {
  cursor: pointer;
}

.notification-icon {
  font-size: 20px;
  cursor: pointer;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
}

.user-name {
  font-size: 14px;
}

.hr-entry {
  color: rgba(255, 255, 255, 0.8);
  font-size: 13px;
  text-decoration: none;
  padding: 6px 12px;
  border-radius: 6px;
  transition: all 0.3s;
  margin-right: 10px;
}

.hr-entry:hover {
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
}

.logout-btn {
  background: none;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 6px;
  padding: 6px 16px;
  color: rgba(255, 255, 255, 0.8);
  font-size: 13px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.3s;
}

.logout-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
}

.main-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 30px;
}
</style>
