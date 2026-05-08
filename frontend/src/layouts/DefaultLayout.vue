<template>
  <el-container class="default-layout">
    <el-header class="header">
      <div class="header-left">
        <h1 class="logo">集团内部员工培训平台</h1>
      </div>
      <div class="header-right">
        <el-dropdown @command="handleCommand">
          <span class="user-info">
            <el-avatar :size="32" icon="User" />
            <span class="username">{{ userStore.userInfo?.real_name }}</span>
            <span class="role-tag" :type="userStore.isHrAdmin ? 'danger' : 'primary'">
              {{ userStore.isHrAdmin ? 'HR管理员' : '员工' }}
            </span>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">个人中心</el-dropdown-item>
              <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-header>

    <el-container>
      <el-aside width="200px" class="sidebar">
        <el-menu :default-active="activeMenu" router class="sidebar-menu">
          <el-menu-item index="/">
            <el-icon><HomeFilled /></el-icon>
            <span>首页</span>
          </el-menu-item>
          <el-menu-item index="/training">
            <el-icon><Reading /></el-icon>
            <span>培训项目</span>
          </el-menu-item>
          <el-menu-item v-if="userStore.isHrAdmin" index="/hr">
            <el-icon><Setting /></el-icon>
            <span>管理后台</span>
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

function handleCommand(command) {
  if (command === 'logout') {
    ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }).then(() => {
      userStore.logout()
    })
  } else if (command === 'profile') {
    // TODO: Navigate to profile page
  }
}
</script>

<style scoped>
.default-layout {
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

.role-tag {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
}

.sidebar {
  background: #f5f7fa;
  border-right: 1px solid #e4e7ed;
}

.sidebar-menu {
  border-right: none;
  background: transparent;
}

.main-content {
  background: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
}
</style>