<template>
  <div class="dashboard">
    <h2 class="page-title">欢迎回来，{{ userStore.userInfo?.real_name }}</h2>

    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #409eff">
              <el-icon><Reading /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.requiredCount }}</div>
              <div class="stat-label">必修项目</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #67c23a">
              <el-icon><CircleCheck /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.completedCount }}</div>
              <div class="stat-label">已完成</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #e6a23c">
              <el-icon><Clock /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.pendingCount }}</div>
              <div class="stat-label">进行中</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #f56c6c">
              <el-icon><Warning /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.overdueCount }}</div>
              <div class="stat-label">已逾期</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="recent-card">
      <template #header>
        <div class="card-header">
          <span>最近学习</span>
          <el-button type="primary" link @click="$router.push('/training')">
            查看全部
          </el-button>
        </div>
      </template>

      <el-empty v-if="recentProjects.length === 0" description="暂无学习记录" />

      <div v-else class="recent-list">
        <div
          v-for="project in recentProjects"
          :key="project.project_id"
          class="recent-item"
          @click="$router.push(`/training/${project.project_id}`)"
        >
          <div class="item-cover">
            <img v-if="project.cover_image" :src="project.cover_image" />
            <div v-else class="cover-placeholder">
              <el-icon><Reading /></el-icon>
            </div>
          </div>
          <div class="item-info">
            <h4>{{ project.title }}</h4>
            <p class="item-meta">
              <el-tag size="small" :type="project.is_required ? 'danger' : 'info'">
                {{ project.is_required ? '必修' : '选修' }}
              </el-tag>
              <span class="deadline">
                截止: {{ formatDate(project.deadline) }}
              </span>
            </p>
            <el-progress
              :percentage="project.progress || 0"
              :stroke-width="6"
              :show-text="false"
            />
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { useTrainingStore } from '@/stores/training'
import dayjs from 'dayjs'

const userStore = useUserStore()
const trainingStore = useTrainingStore()

const stats = ref({
  requiredCount: 0,
  completedCount: 0,
  pendingCount: 0,
  overdueCount: 0,
})

const recentProjects = ref([])

function formatDate(date) {
  return dayjs(date).format('YYYY-MM-DD')
}

onMounted(async () => {
  await trainingStore.fetchProjectList({ page: 1, page_size: 4 })

  recentProjects.value = trainingStore.projectList.map((p) => ({
    ...p,
    progress: Math.floor(Math.random() * 100), // TODO: Get actual progress
  }))

  // Calculate stats
  stats.value.requiredCount = trainingStore.projectList.filter(
    (p) => p.is_required
  ).length
  stats.value.completedCount = Math.floor(stats.value.requiredCount * 0.4)
  stats.value.pendingCount = Math.floor(stats.value.requiredCount * 0.4)
  stats.value.overdueCount = stats.value.requiredCount - stats.value.completedCount - stats.value.pendingCount
})
</script>

<style scoped>
.dashboard {
  max-width: 1200px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 24px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 24px;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.recent-card {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.recent-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.recent-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.recent-item:hover {
  border-color: #409eff;
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.1);
}

.item-cover {
  width: 80px;
  height: 60px;
  border-radius: 4px;
  overflow: hidden;
  flex-shrink: 0;
}

.item-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  background: #f5f7fa;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #c0c4cc;
  font-size: 24px;
}

.item-info {
  flex: 1;
  min-width: 0;
}

.item-info h4 {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin: 0 0 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #909399;
  margin: 0 0 8px;
}

.deadline {
  color: #e6a23c;
}
</style>