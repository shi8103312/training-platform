<template>
  <div class="progress-report">
    <el-button class="back-btn" :icon="ArrowLeft" @click="$router.back()">
      返回
    </el-button>

    <el-card>
      <template #header>
        <span>学习进度 - {{ project?.title }}</span>
      </template>

      <el-table :data="progressList" v-loading="loading" style="width: 100%">
        <el-table-column prop="user_name" label="姓名" />
        <el-table-column prop="dept_name" label="部门" />
        <el-table-column prop="progress" label="学习进度" width="200">
          <template #default="{ row }">
            <el-progress :percentage="row.progress" :stroke-width="10" />
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusName(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="start_time" label="开始时间" width="120">
          <template #default="{ row }">
            {{ formatDate(row.start_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="completion_time" label="完成时间" width="120">
          <template #default="{ row }">
            {{ formatDate(row.completion_time) }}
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-if="pagination.total > pagination.pageSize"
        class="pagination"
        layout="prev, pager, next"
        :total="pagination.total"
        :page-size="pagination.pageSize"
        :current-page="pagination.page"
        @current-change="handlePageChange"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useTrainingStore } from '@/stores/training'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import dayjs from 'dayjs'

const route = useRoute()
const trainingStore = useTrainingStore()

const loading = ref(false)
const project = ref(null)
const progressList = ref([])
const pagination = ref({ page: 1, pageSize: 20, total: 0 })

function getStatusType(status) {
  const types = { 0: 'info', 1: 'warning', 2: 'success' }
  return types[status] || 'info'
}

function getStatusName(status) {
  const names = { 0: '未开始', 1: '进行中', 2: '已完成' }
  return names[status] || '未知'
}

function formatDate(date) {
  return date ? dayjs(date).format('YYYY-MM-DD') : '-'
}

function handlePageChange(page) {
  pagination.value.page = page
  fetchProgress()
}

async function fetchProgress() {
  loading.value = true
  try {
    await trainingStore.fetchProjectDetail(route.params.id)
    project.value = trainingStore.currentProject

    // TODO: Fetch actual progress data from API
    // For now, use mock data
    progressList.value = []
    pagination.value.total = 0
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchProgress()
})
</script>

<style scoped>
.progress-report {
  max-width: 1200px;
}

.back-btn {
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  justify-content: center;
}
</style>