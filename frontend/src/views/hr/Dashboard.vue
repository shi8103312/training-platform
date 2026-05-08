<template>
  <div class="hr-dashboard">
    <h2 class="page-title">管理后台</h2>

    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #409eff">
              <el-icon><Reading /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.projectCount }}</div>
              <div class="stat-label">培训项目</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #67c23a">
              <el-icon><User /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.employeeCount }}</div>
              <div class="stat-label">员工总数</div>
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
              <div class="stat-value">{{ stats.ongoingCount }}</div>
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
              <div class="stat-value">{{ stats.completionRate }}%</div>
              <div class="stat-label">完成率</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :span="16">
        <el-card>
          <template #header>
            <span>最近培训项目</span>
          </template>
          <el-table :data="recentProjects" style="width: 100%">
            <el-table-column prop="title" label="项目名称" />
            <el-table-column prop="status_text" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)">
                  {{ row.status_text }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="deadline" label="截止日期" width="120">
              <template #default="{ row }">
                {{ formatDate(row.deadline) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button type="primary" link @click="$router.push(`/hr/training/${row.project_id}/edit`)">
                  编辑
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card>
          <template #header>
            <span>快捷操作</span>
          </template>
          <div class="quick-actions">
            <el-button type="primary" @click="$router.push('/hr/training/create')">
              <el-icon><Plus /></el-icon>
              创建培训项目
            </el-button>
            <el-button @click="$router.push('/hr/department')">
              <el-icon><OfficeBuilding /></el-icon>
              部门管理
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useTrainingStore } from '@/stores/training'
import { Reading, User, Clock, Warning, Plus, OfficeBuilding } from '@element-plus/icons-vue'
import dayjs from 'dayjs'

const trainingStore = useTrainingStore()

const stats = ref({
  projectCount: 0,
  employeeCount: 0,
  ongoingCount: 0,
  completionRate: 0,
})

const recentProjects = ref([])

function getStatusType(status) {
  const types = { 0: 'info', 1: 'success', 2: 'warning', 3: 'info' }
  return types[status] || 'info'
}

function formatDate(date) {
  return dayjs(date).format('YYYY-MM-DD')
}

onMounted(async () => {
  await trainingStore.fetchProjectList({ page: 1, page_size: 5 })

  recentProjects.value = trainingStore.projectList

  stats.value.projectCount = trainingStore.projectList.length
  stats.value.ongoingCount = trainingStore.projectList.filter(
    (p) => p.status === 1
  ).length
  stats.value.completionRate = Math.round((stats.value.ongoingCount / Math.max(stats.value.projectCount, 1)) * 100)
  stats.value.employeeCount = 128 // TODO: Get from API
})
</script>

<style scoped>
.hr-dashboard {
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

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.quick-actions .el-button {
  width: 100%;
  justify-content: flex-start;
}
</style>