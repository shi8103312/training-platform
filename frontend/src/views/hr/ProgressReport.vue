<template>
  <div class="progress-report">
    <div class="page-header">
      <span class="page-title">📈 学习报表</span>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <div class="filter-item">
        <label>培训项目</label>
        <select v-model="filters.projectId" @change="handleProjectChange">
          <option value="">全部项目</option>
          <option v-for="p in projectList" :key="p.project_id" :value="p.project_id">
            {{ p.title }}
          </option>
        </select>
      </div>
      <div class="filter-item">
        <label>部门</label>
        <select v-model="filters.deptId">
          <option value="">全部部门</option>
          <option v-for="d in departmentList" :key="d.dept_id" :value="d.dept_id">
            {{ d.dept_name }}
          </option>
        </select>
      </div>
      <div class="filter-item">
        <label>状态</label>
        <select v-model="filters.status">
          <option value="">全部</option>
          <option value="2">已完成</option>
          <option value="1">进行中</option>
          <option value="0">未开始</option>
        </select>
      </div>
      <button class="btn btn-primary btn-sm" @click="handleQuery">
        🔍 查询
      </button>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="icon" style="background: #e6f0ff;">👥</div>
        <div class="value">{{ stats.total }}</div>
        <div class="label">应学人数</div>
      </div>
      <div class="stat-card">
        <div class="icon" style="background: #e6f7ed;">✅</div>
        <div class="value">{{ stats.completed }}</div>
        <div class="label">已完成</div>
      </div>
      <div class="stat-card">
        <div class="icon" style="background: #fff3e6;">⏳</div>
        <div class="value">{{ stats.inProgress }}</div>
        <div class="label">进行中</div>
      </div>
      <div class="stat-card">
        <div class="icon" style="background: #f3e6ff;">📊</div>
        <div class="value">{{ stats.completionRate }}%</div>
        <div class="label">完成率</div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="charts-grid">
      <div class="chart-card">
        <div class="chart-title">📊 学习趋势（近7天）</div>
        <div class="chart-placeholder">
          <div class="bars">
            <div v-for="(val, idx) in trendData" :key="idx" class="bar" :style="{ height: val + 'px' }"></div>
          </div>
          <span style="margin-top: 10px">每日新增完成人数</span>
        </div>
      </div>

      <div class="chart-card">
        <div class="chart-title">🎯 培训完成情况分布</div>
        <div class="pie-chart-wrapper">
          <div class="pie-placeholder" :style="pieStyle">
            <div class="pie-inner">
              <span style="font-size: 20px; font-weight: 700; color: #333;">{{ stats.completionRate }}%</span>
              <span style="font-size: 11px; color: #999;">完成率</span>
            </div>
          </div>
          <div class="pie-legend">
            <div class="legend-item">
              <div class="legend-color" style="background: #667eea;"></div>
              <span>已完成 {{ stats.completed }}人</span>
            </div>
            <div class="legend-item">
              <div class="legend-color" style="background: #52c41a;"></div>
              <span>进行中 {{ stats.inProgress }}人</span>
            </div>
            <div class="legend-item">
              <div class="legend-color" style="background: #fa8c16;"></div>
              <span>未开始 {{ stats.notStarted }}人</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 详细数据表 -->
    <div class="data-table">
      <div class="table-header">
        <span class="table-title">📋 学习明细</span>
        <button class="btn btn-outline btn-sm" @click="handleExportExcel">
          📥 导出Excel
        </button>
      </div>
      <table>
        <thead>
          <tr>
            <th>工号</th>
            <th>姓名</th>
            <th>部门</th>
            <th>培训项目</th>
            <th>学习进度</th>
            <th>学习时长</th>
            <th>考试分数</th>
            <th>完成状态</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in progressList" :key="item.user_id">
            <td>{{ item.user_id }}</td>
            <td>{{ item.user_name }}</td>
            <td>{{ item.dept_name }}</td>
            <td>{{ item.project_title }}</td>
            <td>
              <div class="progress-cell">
                <div class="progress-bar">
                  <div class="fill" :style="{ width: item.progress + '%' }"></div>
                </div>
                <span class="progress-text">{{ item.progress }}%</span>
              </div>
            </td>
            <td>{{ item.learning_time }}</td>
            <td>{{ item.exam_score !== null ? item.exam_score + '分' : '--' }}</td>
            <td>
              <span class="status-badge" :class="getStatusClass(item.status)">
                {{ item.status_text }}
              </span>
            </td>
          </tr>
          <tr v-if="progressList.length === 0 && !loading">
            <td colspan="8" class="empty-cell">暂无数据</td>
          </tr>
        </tbody>
      </table>

      <div class="pagination" v-if="pagination.total > 0">
        <span class="page-info">
          显示 {{ (pagination.page - 1) * pagination.pageSize + 1 }}-{{ Math.min(pagination.page * pagination.pageSize, pagination.total) }} 条，共 {{ pagination.total }} 条
        </span>
        <div class="page-buttons">
          <button class="btn btn-outline btn-sm" :disabled="pagination.page <= 1" @click="handlePrevPage">
            上一页
          </button>
          <button class="btn btn-outline btn-sm" :disabled="pagination.page >= pagination.totalPages" @click="handleNextPage">
            下一页
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTrainingStore } from '@/stores/training'
import { ElMessage } from 'element-plus'
import * as XLSX from 'xlsx'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()
const trainingStore = useTrainingStore()

const loading = ref(false)
const projectList = ref([])
const departmentList = ref([])
const progressList = ref([])
const trendData = ref([60, 90, 75, 110, 95, 130, 100])

const stats = reactive({
  total: 0,
  completed: 0,
  inProgress: 0,
  notStarted: 0,
  completionRate: 0,
})

const filters = reactive({
  projectId: '',
  deptId: '',
  status: '',
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
  totalPages: 0,
})

const pieStyle = computed(() => {
  const completedDeg = stats.total > 0 ? (stats.completed / stats.total) * 360 : 0
  const inProgressDeg = stats.total > 0 ? (stats.inProgress / stats.total) * 360 : 0
  return {
    background: `conic-gradient(#667eea 0deg ${completedDeg}deg, #52c41a ${completedDeg}deg ${completedDeg + inProgressDeg}deg, #fa8c16 ${completedDeg + inProgressDeg}deg 360deg)`,
  }
})

function getStatusClass(status) {
  const classMap = { 0: 'not-started', 1: 'in-progress', 2: 'completed' }
  return classMap[status] || 'not-started'
}

function handleProjectChange() {
  pagination.page = 1
  fetchData()
  fetchStats()
}

function handleQuery() {
  pagination.page = 1
  fetchData()
}

function handlePrevPage() {
  if (pagination.page > 1) {
    pagination.page--
    fetchData()
  }
}

function handleNextPage() {
  if (pagination.page < pagination.totalPages) {
    pagination.page++
    fetchData()
  }
}

async function fetchProjectList() {
  try {
    await trainingStore.fetchProjectList({ page: 1, page_size: 100 })
    projectList.value = trainingStore.projectList
    console.log('[DEBUG] fetchProjectList:', projectList.value)
  } catch (error) {
    console.error('Failed to fetch project list:', error)
  }
}

async function fetchData() {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
    }
    if (filters.deptId) params.dept_id = filters.deptId
    if (filters.status !== '') params.status = filters.status

    const projectId = filters.projectId || route.params.id
    console.log('[DEBUG] fetchData projectId:', projectId, 'filters:', filters)
    if (!projectId) {
      console.log('[DEBUG] fetchData: no projectId, returning')
      return
    }

    const data = await trainingStore.fetchProgressReport(projectId, params)
    console.log('[DEBUG] fetchData response:', data)
    if (data) {
      progressList.value = data.list || []
      departmentList.value = data.departments || []
      pagination.total = data.pagination?.total || 0
      pagination.totalPages = data.pagination?.total_pages || 1
      stats.total = data.stats?.total || 0
      stats.completed = data.stats?.completed || 0
      stats.inProgress = data.stats?.in_progress || 0
      stats.notStarted = data.stats?.not_started || 0
      stats.completionRate = stats.total > 0 ? Math.round((stats.completed / stats.total) * 100) : 0
    }
  } catch (error) {
    console.error('Failed to fetch progress data:', error)
  } finally {
    loading.value = false
  }
}

async function fetchStats() {
  try {
    const projectId = filters.projectId || route.params.id
    if (!projectId) return

    const data = await trainingStore.fetchProgressStats(projectId)
    if (data) {
      trendData.value = data.trend || [60, 90, 75, 110, 95, 130, 100]
    }
  } catch (error) {
    console.error('Failed to fetch stats:', error)
  }
}

function handleExport() {
  if (progressList.value.length === 0) {
    ElMessage.warning('暂无数据可导出')
    return
  }

  try {
    // 构建导出数据
    const exportData = progressList.value.map(item => ({
      '工号': item.user_id,
      '姓名': item.user_name,
      '部门': item.dept_name,
      '培训项目': item.project_title,
      '学习进度(%)': item.progress,
      '学习时长': item.learning_time,
      '考试分数': item.exam_score !== null ? item.exam_score + '分' : '--',
      '完成状态': item.status_text,
    }))

    // 添加统计信息
    const statsData = [
      { '工号': '统计信息', '姓名': '', '部门': '', '培训项目': '', '学习进度(%)': '', '学习时长': '', '考试分数': '', '完成状态': '' },
      { '工号': '应学人数', '姓名': stats.total, '部门': '', '培训项目': '', '学习进度(%)': '', '学习时长': '', '考试分数': '', '完成状态': '' },
      { '工号': '已完成', '姓名': stats.completed, '部门': '', '培训项目': '', '学习进度(%)': '', '学习时长': '', '考试分数': '', '完成状态': '' },
      { '工号': '进行中', '姓名': stats.inProgress, '部门': '', '培训项目': '', '学习进度(%)': '', '学习时长': '', '考试分数': '', '完成状态': '' },
      { '工号': '未开始', '姓名': stats.notStarted, '部门': '', '培训项目': '', '学习进度(%)': '', '学习时长': '', '考试分数': '', '完成状态': '' },
      { '工号': '完成率', '姓名': stats.completionRate + '%', '部门': '', '培训项目': '', '学习进度(%)': '', '学习时长': '', '考试分数': '', '完成状态': '' },
    ]

    const allData = [...statsData, {}, ...exportData]

    // 创建工作簿和工作表
    const ws = XLSX.utils.json_to_sheet(allData)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, '学习报表')

    // 设置列宽
    ws['!cols'] = [
      { wch: 12 }, // 工号
      { wch: 12 }, // 姓名
      { wch: 15 }, // 部门
      { wch: 25 }, // 培训项目
      { wch: 15 }, // 学习进度
      { wch: 12 }, // 学习时长
      { wch: 12 }, // 考试分数
      { wch: 12 }, // 完成状态
    ]

    // 生成文件名
    const projectTitle = projectList.value.find(p => p.project_id === filters.projectId)?.title || '学习报表'
    const filename = `${projectTitle}_学习报表_${dayjs().format('YYYY-MM-DD')}.xlsx`

    // 下载文件
    XLSX.writeFile(wb, filename)
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('Export error:', error)
    ElMessage.error('导出失败')
  }
}

function handleExportExcel() {
  handleExport()
}

onMounted(async () => {
  await fetchProjectList()

  // Set default project from route
  if (route.params.id) {
    filters.projectId = route.params.id
  } else if (projectList.value.length > 0) {
    filters.projectId = projectList.value[0].project_id
  }

  await fetchData()
  await fetchStats()
})
</script>

<style scoped>
.progress-report {
  font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

/* 筛选栏 */
.filter-bar {
  background: #fff;
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 20px;
  display: flex;
  gap: 15px;
  align-items: center;
  flex-wrap: wrap;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-item label {
  font-size: 14px;
  color: #666;
}

.filter-item select {
  height: 36px;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  padding: 0 12px;
  font-size: 14px;
}

.filter-item select:focus {
  outline: none;
  border-color: #667eea;
}

/* 统计卡片 */
.stats-row {
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
  text-align: center;
}

.stat-card .icon {
  font-size: 32px;
  margin-bottom: 10px;
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
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
  grid-template-columns: repeat(2, 1fr);
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
  gap: 30px;
  height: 150px;
}

.bar {
  width: 40px;
  background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
  border-radius: 6px 6px 0 0;
}

.pie-chart-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 40px;
  height: 200px;
}

.pie-placeholder {
  width: 160px;
  height: 160px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pie-inner {
  width: 100px;
  height: 100px;
  background: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
}

.pie-legend {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: #333;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

/* 数据表 */
.data-table {
  background: #fff;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.table-header {
  padding: 20px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th {
  text-align: left;
  padding: 14px 16px;
  background: #fafafa;
  font-size: 13px;
  color: #999;
  font-weight: 500;
  border-bottom: 1px solid #f0f0f0;
}

td {
  padding: 16px;
  border-bottom: 1px solid #f5f7fa;
  font-size: 14px;
  color: #333;
}

tr:hover {
  background: #f8f8ff;
}

.empty-cell {
  text-align: center;
  color: #999;
  padding: 40px !important;
}

.status-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
}

.status-badge.completed {
  background: #f6ffed;
  color: #52c41a;
}

.status-badge.in-progress {
  background: #e6f0ff;
  color: #1890ff;
}

.status-badge.not-started {
  background: #f5f5f5;
  color: #999;
}

.progress-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.progress-bar {
  flex: 1;
  height: 6px;
  background: #f0f0f0;
  border-radius: 3px;
  max-width: 100px;
}

.progress-bar .fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  border-radius: 3px;
}

.progress-text {
  font-size: 13px;
  color: #667eea;
  min-width: 45px;
}

.pagination {
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-info {
  font-size: 14px;
  color: #666;
}

.page-buttons {
  display: flex;
  gap: 10px;
}

/* 按钮样式 */
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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.btn-outline {
  background: #fff;
  color: #667eea;
  border: 1px solid #667eea;
}

.btn-outline:hover:not(:disabled) {
  background: #f5f7ff;
}

.btn-outline:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-sm {
  height: 30px;
  padding: 0 12px;
  font-size: 13px;
}
</style>