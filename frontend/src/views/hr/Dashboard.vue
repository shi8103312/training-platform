<template>
  <div class="hr-dashboard">
    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="header">
          <div class="icon" style="background: #e6f0ff">📚</div>
          <span class="trend up" v-if="statsTrend.projectChange > 0">↑ {{ statsTrend.projectChange }}%</span>
          <span class="trend down" v-else-if="statsTrend.projectChange < 0">↓ {{ Math.abs(statsTrend.projectChange) }}%</span>
        </div>
        <div class="value">{{ stats.projectCount }}</div>
        <div class="label">进行中培训</div>
      </div>
      <div class="stat-card">
        <div class="header">
          <div class="icon" style="background: #e6f7ed">👥</div>
          <span class="trend up" v-if="statsTrend.employeeChange > 0">↑ {{ statsTrend.employeeChange }}%</span>
          <span class="trend down" v-else-if="statsTrend.employeeChange < 0">↓ {{ Math.abs(statsTrend.employeeChange) }}%</span>
        </div>
        <div class="value">{{ stats.employeeCount }}</div>
        <div class="label">参与员工</div>
      </div>
      <div class="stat-card">
        <div class="header">
          <div class="icon" style="background: #fff3e6">⏰</div>
          <span class="trend down" v-if="statsTrend.pendingChange > 0">↑ {{ statsTrend.pendingChange }}%</span>
          <span class="trend up" v-else-if="statsTrend.pendingChange < 0">↓ {{ Math.abs(statsTrend.pendingChange) }}%</span>
        </div>
        <div class="value">{{ stats.pendingCount }}</div>
        <div class="label">待完成人数</div>
      </div>
      <div class="stat-card">
        <div class="header">
          <div class="icon" style="background: #f3e6ff">🏆</div>
          <span class="trend up" v-if="statsTrend.completionChange > 0">↑ {{ statsTrend.completionChange }}%</span>
          <span class="trend down" v-else-if="statsTrend.completionChange < 0">↓ {{ Math.abs(statsTrend.completionChange) }}%</span>
        </div>
        <div class="value">{{ stats.completionRate }}%</div>
        <div class="label">平均完成率</div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="charts-grid">
      <div class="chart-card">
        <div class="chart-title">📈 学习趋势（近7天）</div>
        <div class="chart-placeholder">
          <div class="bars">
            <div v-for="(val, idx) in trendData" :key="idx" class="bar" :style="{ height: val + 'px' }"></div>
          </div>
          <span>每日参与学习人数</span>
        </div>
      </div>

      <div class="chart-card">
        <div class="chart-title">⚡ 快捷操作</div>
        <div class="quick-actions">
          <button class="quick-btn" @click="$router.push('/hr/training/create')">
            <span class="icon">📚</span>
            <span class="text">创建培训</span>
          </button>
          <button class="quick-btn" @click="$router.push('/hr/training')">
            <span class="icon">✏️</span>
            <span class="text">管理项目</span>
          </button>
          <button class="quick-btn" @click="$router.push('/hr/department')">
            <span class="icon">📤</span>
            <span class="text">导入部门</span>
          </button>
          <button class="quick-btn" @click="$router.push('/hr/notification')">
            <span class="icon">✉️</span>
            <span class="text">发送通知</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 最新培训列表 -->
    <div class="data-card">
      <div class="header">
        <span class="title">📋 进行中培训</span>
        <button class="btn btn-outline" style="height: 32px; font-size: 13px" @click="$router.push('/hr/training')">
          查看全部
        </button>
      </div>
      <table>
        <thead>
          <tr>
            <th>培训名称</th>
            <th>类型</th>
            <th>参与人数</th>
            <th>完成率</th>
            <th>截止日期</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="project in projectList" :key="project.project_id">
            <td>{{ project.title }}</td>
            <td>
              <span :style="{ color: project.is_required ? '#ff6600' : '#00a854' }">
                {{ project.is_required ? '必修' : '选修' }}
              </span>
            </td>
            <td>{{ getProjectStatsData(project.project_id).enrolled_count || 0 }}</td>
            <td>
              <div style="display: flex; align-items: center; gap: 8px">
                <div style="flex: 1; height: 6px; background: #f0f0f0; border-radius: 3px">
                  <div :style="{ width: getProjectStatsData(project.project_id).completion_rate + '%', height: '100%', background: 'var(--theme-gradient)', borderRadius: '3px' }"></div>
                </div>
                <span style="font-size: 13px; color: var(--theme-primary)">{{ getProjectStatsData(project.project_id).completion_rate || 0 }}%</span>
              </div>
            </td>
            <td>{{ project.deadline ? formatDate(project.deadline) : '--' }}</td>
            <td>
              <span class="status-badge" :class="getStatusClass(project.status)">
                {{ project.status_text }}
              </span>
            </td>
            <td>
              <a
                href="javascript:void(0)"
                style="color: var(--theme-primary); text-decoration: none"
                @click="$router.push(`/hr/progress/${project.project_id}`)"
              >
                详情
              </a>
            </td>
          </tr>
          <tr v-if="projectList.length === 0 && !loading">
            <td colspan="7" style="text-align: center; color: #999; padding: 40px">暂无数据</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useTrainingStore } from '@/stores/training'
import { getDashboardStats, getProjectStats, getLearningTrend } from '@/api/auth'
import dayjs from 'dayjs'

const router = useRouter()
const trainingStore = useTrainingStore()

const loading = ref(false)
const projectList = ref([])
const projectStatsMap = ref({})
const stats = ref({
  projectCount: 0,
  employeeCount: 0,
  pendingCount: 0,
  completionRate: 0,
})

const statsTrend = reactive({
  projectChange: 0,
  employeeChange: 0,
  pendingChange: 0,
  completionChange: 0,
})

const trendData = ref([60, 90, 75, 110, 95, 130, 100])

function getStatusClass(status) {
  const classMap = { 0: 'draft', 1: 'published', 2: 'unpublished' }
  return classMap[status] || 'draft'
}

function formatDate(date) {
  return date ? dayjs(date).format('YYYY-MM-DD') : '--'
}

function getProjectStatsData(projectId) {
  return projectStatsMap.value[projectId] || { enrolled_count: 0, completion_rate: 0 }
}

async function fetchStats() {
  try {
    const res = await getDashboardStats()
    if (res.code === 0) {
      stats.value = {
        projectCount: res.data.project_count || 0,
        employeeCount: res.data.employee_count || 0,
        pendingCount: res.data.pending_count || 0,
        completionRate: res.data.completion_rate || 0,
      }
    }
  } catch (error) {
    console.error('Failed to fetch stats:', error)
  }
}

async function fetchProjectStats() {
  try {
    const res = await getProjectStats()
    if (res.code === 0 && res.data) {
      const map = {}
      res.data.forEach(item => {
        map[item.project_id] = item
      })
      projectStatsMap.value = map
    }
  } catch (error) {
    console.error('Failed to fetch project stats:', error)
  }
}

async function fetchTrend() {
  try {
    const res = await getLearningTrend()
    if (res.code === 0 && res.data) {
      trendData.value = res.data.trend || [60, 90, 75, 110, 95, 130, 100]
    }
  } catch (error) {
    console.error('Failed to fetch trend:', error)
  }
}

async function fetchProjectList() {
  loading.value = true
  try {
    await trainingStore.fetchProjectList({ page: 1, page_size: 10, status: 1 })
    projectList.value = trainingStore.projectList
  } catch (error) {
    console.error('Failed to fetch project list:', error)
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await fetchStats()
  await fetchProjectList()
  await fetchProjectStats()
  await fetchTrend()
})
</script>

<style scoped>
.hr-dashboard {
  font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
}

/* 统计卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 25px;
}

.stat-card {
  background: #fff;
  border-radius: 10px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.stat-card .header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.stat-card .icon {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.stat-card .trend {
  font-size: 13px;
  padding: 4px 8px;
  border-radius: 4px;
}

.stat-card .trend.up {
  background: #f6ffed;
  color: #52c41a;
}

.stat-card .trend.down {
  background: #fff1f0;
  color: #ff4d4f;
}

.stat-card .value {
  font-size: 28px;
  font-weight: 700;
  color: #333;
  margin-bottom: 5px;
}

.stat-card .label {
  font-size: 14px;
  color: #999;
}

/* 图表区域 */
.charts-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
  margin-bottom: 25px;
}

.chart-card {
  background: #fff;
  border-radius: 10px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.chart-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 20px;
}

.chart-placeholder {
  height: 200px;
  background: linear-gradient(90deg, #f5f7fa 0%, #e6f0ff 100%);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #999;
  font-size: 14px;
}

.chart-placeholder .bars {
  display: flex;
  align-items: flex-end;
  gap: 20px;
  height: 150px;
  margin-bottom: 10px;
}

.bar {
  width: 30px;
  background: var(--theme-gradient);
  border-radius: 4px 4px 0 0;
  animation: grow 1s ease-out;
}

@keyframes grow {
  from {
    height: 0;
  }
}

.quick-actions {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.quick-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px;
  background: #f8f8ff;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  border: none;
  text-align: left;
}

.quick-btn:hover {
  background: #e6f0ff;
  transform: translateY(-2px);
}

.quick-btn .icon {
  font-size: 24px;
}

.quick-btn .text {
  font-size: 14px;
  color: #333;
}

/* 数据列表 */
.data-card {
  background: #fff;
  border-radius: 10px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.data-card .header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.data-card .title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.data-card table {
  width: 100%;
  border-collapse: collapse;
}

.data-card th {
  text-align: left;
  padding: 12px;
  border-bottom: 1px solid #f0f0f0;
  font-size: 13px;
  color: #999;
  font-weight: 500;
}

.data-card td {
  padding: 14px 12px;
  border-bottom: 1px solid #f5f7fa;
  font-size: 14px;
  color: #333;
}

.data-card tr:hover {
  background: #f8f8ff;
}

.status-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
}

.status-badge.published {
  background: #f6ffed;
  color: #52c41a;
}

.status-badge.draft {
  background: #f5f7fa;
  color: #999;
}

.status-badge.unpublished {
  background: #fff7e6;
  color: #fa8c16;
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

.btn-primary {
  background: var(--theme-gradient);
  color: #fff;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.btn-outline {
  background: #fff;
  color: var(--theme-primary);
  border: 1px solid var(--theme-primary);
}

.btn-outline:hover {
  background: #f5f7ff;
}
</style>