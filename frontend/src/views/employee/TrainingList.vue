<template>
  <div class="training-list">
    <div class="header-actions">
      <h2 class="page-title">培训项目</h2>
      <el-input
        v-model="keyword"
        placeholder="搜索培训项目"
        :prefix-icon="Search"
        style="width: 300px"
        clearable
        @clear="handleSearch"
        @keyup.enter="handleSearch"
      />
    </div>

    <el-tabs v-model="activeTab" @tab-change="handleTabChange">
      <el-tab-pane label="进行中" name="ongoing" />
      <el-tab-pane label="已完成" name="completed" />
      <el-tab-pane label="已逾期" name="overdue" />
    </el-tabs>

    <el-empty v-if="loading === false && projectList.length === 0" description="暂无培训项目" />

    <div v-else class="project-grid">
      <el-card
        v-for="project in projectList"
        :key="project.project_id"
        class="project-card"
        shadow="hover"
        @click="$router.push(`/training/${project.project_id}`)"
      >
        <div class="card-cover">
          <img v-if="project.cover_image" :src="project.cover_image" />
          <div v-else class="cover-placeholder">
            <el-icon><Reading /></el-icon>
          </div>
          <el-tag
            class="status-tag"
            :type="getStatusType(project.status)"
            size="small"
          >
            {{ project.status_text }}
          </el-tag>
        </div>

        <div class="card-content">
          <h3 class="project-title">{{ project.title }}</h3>

          <p class="project-desc">{{ project.description || '暂无描述' }}</p>

          <div class="project-meta">
            <el-tag :type="project.is_required ? 'danger' : 'info'" size="small">
              {{ project.is_required ? '必修' : '选修' }}
            </el-tag>
            <span class="deadline">
              <el-icon><Clock /></el-icon>
              {{ formatDate(project.deadline) }}
            </span>
          </div>

          <div class="project-progress">
            <el-progress
              :percentage="getProgress(project)"
              :stroke-width="8"
              :show-text="false"
            />
            <span class="progress-text">{{ getProgress(project) }}%</span>
          </div>
        </div>
      </el-card>
    </div>

    <el-pagination
      v-if="pagination.total > pagination.pageSize"
      class="pagination"
      layout="prev, pager, next"
      :total="pagination.total"
      :page-size="pagination.pageSize"
      :current-page="pagination.page"
      @current-change="handlePageChange"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useTrainingStore } from '@/stores/training'
import { Search, Reading, Clock } from '@element-plus/icons-vue'
import dayjs from 'dayjs'

const trainingStore = useTrainingStore()

const keyword = ref('')
const activeTab = ref('ongoing')
const loading = ref(false)

const projectList = ref([])
const pagination = ref({ page: 1, pageSize: 20, total: 0 })

function getStatusType(status) {
  const types = { 0: 'info', 1: 'success', 2: 'warning', 3: 'info' }
  return types[status] || 'info'
}

function formatDate(date) {
  return dayjs(date).format('YYYY-MM-DD')
}

function getProgress(project) {
  // TODO: Get actual progress from API
  return Math.floor(Math.random() * 100)
}

function handleSearch() {
  fetchProjects()
}

function handleTabChange() {
  fetchProjects()
}

function handlePageChange(page) {
  pagination.value.page = page
  fetchProjects()
}

async function fetchProjects() {
  loading.value = true
  try {
    await trainingStore.fetchProjectList({
      page: pagination.value.page,
      page_size: pagination.value.pageSize,
      keyword: keyword.value || undefined,
    })

    projectList.value = trainingStore.projectList
    pagination.value = trainingStore.pagination
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchProjects()
})
</script>

<style scoped>
.training-list {
  max-width: 1200px;
}

.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.project-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.project-card {
  cursor: pointer;
  transition: all 0.3s;
}

.project-card:hover {
  transform: translateY(-4px);
}

.card-cover {
  position: relative;
  height: 160px;
  border-radius: 4px;
  overflow: hidden;
  background: #f5f7fa;
}

.card-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #c0c4cc;
  font-size: 48px;
}

.status-tag {
  position: absolute;
  top: 8px;
  right: 8px;
}

.card-content {
  padding: 12px 0;
}

.project-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.project-desc {
  font-size: 14px;
  color: #909399;
  margin: 0 0 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  height: 40px;
}

.project-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.deadline {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #e6a23c;
}

.project-progress {
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-text {
  font-size: 12px;
  color: #67c23a;
  min-width: 40px;
}

.pagination {
  margin-top: 20px;
  justify-content: center;
}
</style>