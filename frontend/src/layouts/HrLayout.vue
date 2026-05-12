<template>
  <div class="hr-layout">
    <div class="layout">
      <!-- 侧边栏 -->
      <aside class="sidebar">
        <div class="sidebar-logo">
          <span class="icon">🏢</span>
          <span>培训管理后台</span>
        </div>

        <nav class="sidebar-nav">
          <router-link to="/hr" class="nav-item" :class="{ active: route.path === '/hr' }">
            <span class="icon">📊</span>
            <span>工作台</span>
          </router-link>
          <router-link to="/hr/training" class="nav-item" :class="{ active: route.path.startsWith('/hr/training') }">
            <span class="icon">📚</span>
            <span>培训管理</span>
          </router-link>
          <router-link to="/hr/department" class="nav-item" :class="{ active: route.path === '/hr/department' }">
            <span class="icon">👥</span>
            <span>部门管理</span>
          </router-link>
          <router-link to="/hr/employee" class="nav-item" :class="{ active: route.path === '/hr/employee' }">
            <span class="icon">👔</span>
            <span>员工管理</span>
          </router-link>
          <router-link to="/hr/progress" class="nav-item" :class="{ active: route.path === '/hr/progress' }">
            <span class="icon">📈</span>
            <span>学习报表</span>
          </router-link>
          <router-link to="/hr/notification" class="nav-item" :class="{ active: route.path === '/hr/notification' }">
            <span class="icon">✉️</span>
            <span>发送通知</span>
          </router-link>
          <router-link to="/hr/settings" class="nav-item" :class="{ active: route.path === '/hr/settings' }">
            <span class="icon">⚙️</span>
            <span>系统设置</span>
          </router-link>
        </nav>

        <div class="sidebar-footer">
          <div class="user-card">
            <div class="user-avatar">👔</div>
            <div class="user-details">
              <div class="name">{{ userStore.userInfo?.real_name || '管理员' }}</div>
              <div class="role">HR管理员</div>
            </div>
          </div>
          <button class="logout-btn" @click="handleLogout">
            <span class="icon">🚪</span>
            <span>退出登录</span>
          </button>
        </div>
      </aside>

      <!-- 主内容 -->
      <main class="main-content">
        <header class="top-header">
          <div class="page-title">{{ pageTitle }}</div>
          <div class="header-actions">
            <button class="btn btn-outline" @click="goToEmployee">🏠 返回前台</button>
          </div>
        </header>

        <div class="content">
          <router-view />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const pageTitle = computed(() => {
  const titles = {
    '/hr': '工作台',
    '/hr/training': '培训项目管理',
    '/hr/training/create': '创建培训',
    '/hr/training/manage': '管理培训',
    '/hr/department': '部门管理',
    '/hr/progress': '学习报表',
    '/hr/notification': '发送通知',
    '/hr/settings': '系统设置',
  }
  return titles[route.path] || '工作台'
})

function goToEmployee() {
  router.push('/')
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
</script>

<style scoped>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.hr-layout {
  font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
}

.layout {
  display: flex;
  min-height: 100vh;
}

/* 侧边栏 */
.sidebar {
  width: 220px;
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
  color: #fff;
  display: flex;
  flex-direction: column;
}

.sidebar-logo {
  padding: 20px;
  font-size: 16px;
  font-weight: 600;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  gap: 10px;
}

.sidebar-logo .icon {
  font-size: 24px;
}

.sidebar-nav {
  flex: 1;
  padding: 15px 0;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  color: rgba(255, 255, 255, 0.7);
  text-decoration: none;
  font-size: 14px;
  transition: all 0.3s;
  cursor: pointer;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.nav-item.active {
  background: rgba(102, 126, 234, 0.3);
  color: #fff;
  border-left: 3px solid #667eea;
}

.nav-item .icon {
  font-size: 18px;
  width: 24px;
  text-align: center;
}

.sidebar-footer {
  padding: 15px 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.user-card {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #667eea;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
}

.user-details .name {
  font-size: 14px;
  font-weight: 500;
}

.user-details .role {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
}

.logout-btn {
  width: 100%;
  margin-top: 10px;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 6px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s;
}

.logout-btn:hover {
  background: rgba(255, 77, 79, 0.2);
  color: #ff6b6b;
}

/* 主内容 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #f0f2f5;
}

.top-header {
  background: #fff;
  padding: 0 30px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.btn {
  height: 36px;
  padding: 0 20px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  border: none;
  transition: all 0.3s;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.btn-outline {
  background: #fff;
  color: #667eea;
  border: 1px solid #667eea;
}

.btn-outline:hover {
  background: #f5f7ff;
}

.content {
  flex: 1;
  padding: 25px;
}
</style>
