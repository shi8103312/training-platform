<template>
  <el-container class="hr-layout">
    <el-header class="header">
      <div class="header-left">
        <h1 class="logo">培训平台 - 管理后台</h1>
      </div>
      <div class="header-right">
        <el-space>
          <el-button type="primary" @click="goToTraining">培训管理</el-button>
          <el-button @click="goToEmployee">返回员工端</el-button>
        </el-space>
        <el-dropdown @command="handleCommand">
          <span class="user-info">
            <el-avatar :size="32" icon="User" />
            <span class="username">{{ userStore.userInfo?.real_name }}</span>
            <el-tag type="danger" size="small">HR管理员</el-tag>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-header>

    <el-container>
      <el-aside width="220px" class="sidebar">
        <el-menu :default-active="activeMenu" router class="sidebar-menu">
          <el-menu-item index="/hr">
            <el-icon><DataAnalysis /></el-icon>
            <span>数据看板</span>
          </el-menu-item>
          <el-menu-item index="/hr/training">
            <el-icon><Reading /></el-icon>
            <span>培训项目管理</span>
          </el-menu-item>
          <el-menu-item index="/hr/department">
            <el-icon><OfficeBuilding /></el-icon>
            <span>部门管理</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const activeMenu = computed(() => route.path)

function goToTraining() {
  router.push('/hr/training')
}

function goToEmployee() {
  router.push('/')
}

function handleCommand(command) {
  if (command === 'logout') {
    ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }).then(() => {
      userStore.logout()
    })
  }
}
</script>

<style scoped>
.hr-layout {
  height: 100vh;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  padding: 0 20px;
}

.header-left .logo {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}

.username {
  font-size: 14px;
  color: #606266;
}

.sidebar {
  background: #fff;
  border-right: 1px solid #e4e7ed;
}

.sidebar-menu {
  border-right: none;
}

.main-content {
  background: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
}
</style>