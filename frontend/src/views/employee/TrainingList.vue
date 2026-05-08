<template>
  <div class="training-list-page">
    <h1 class="page-title">📚 全部培训</h1>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <div class="filter-item">
        <label>培训类型</label>
        <select v-model="filters.type">
          <option value="">全部</option>
          <option value="required">必修</option>
          <option value="optional">选修</option>
        </select>
      </div>
      <div class="filter-item">
        <label>状态</label>
        <select v-model="filters.status">
          <option value="">全部</option>
          <option value="not-started">未开始</option>
          <option value="in-progress">进行中</option>
          <option value="deadline-soon">即将截止</option>
          <option value="completed">已完成</option>
        </select>
      </div>
      <div class="filter-item">
        <label>关键词</label>
        <input type="text" v-model="filters.keyword" placeholder="搜索培训名称" />
      </div>
      <button class="filter-btn" @click="handleSearch">🔍 搜索</button>
    </div>

    <!-- 标签栏 -->
    <div class="tab-bar">
      <div
        class="tab-item"
        :class="{ active: activeTab === 'all' }"
        @click="activeTab = 'all'"
      >
        全部 <span class="count">{{ tabCounts.all }}</span>
      </div>
      <div
        class="tab-item"
        :class="{ active: activeTab === 'in-progress' }"
        @click="activeTab = 'in-progress'"
      >
        进行中 <span class="count">{{ tabCounts.inProgress }}</span>
      </div>
      <div
        class="tab-item"
        :class="{ active: activeTab === 'completed' }"
        @click="activeTab = 'completed'"
      >
        已完成 <span class="count">{{ tabCounts.completed }}</span>
      </div>
    </div>

    <!-- 培训列表 -->
    <div class="training-grid" v-if="filteredProjects.length">
      <div
        v-for="project in filteredProjects"
        :key="project.project_id"
        class="training-card"
        @click="$router.push(`/training/${project.project_id}`)"
      >
        <div class="training-cover" :style="{ background: getCoverGradient(project) }">
          {{ getCoverEmoji(project) }}
          <div class="overlay">
            <span class="tag" :class="project.is_required ? 'required' : 'optional'">
              {{ project.is_required ? '必修' : '选修' }}
            </span>
          </div>
        </div>
        <div class="training-content">
          <div class="training-title">{{ project.title }}</div>
          <div class="training-meta">
            <span>{{ project.materialCount || 0 }}个材料</span>
            <span>{{ getDeadlineText(project.deadline) }}</span>
          </div>
          <div class="progress-bar">
            <div
              class="fill"
              :style="{ width: (project.userProgress || 0) + '%', background: getProgressGradient(project) }"
            ></div>
          </div>
          <div class="progress-text">
            <span>进度 {{ project.userProgress || 0 }}%</span>
            <span class="status-badge" :class="getStatusClass(project)">{{ getStatusText(project) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div class="empty-state" v-else-if="!loading">
      <div class="icon">📭</div>
      <h3>暂无符合条件的培训</h3>
      <p>请尝试调整筛选条件</p>
    </div>

    <!-- 加载状态 -->
    <div class="loading-state" v-if="loading">
      <div class="icon">⏳</div>
      <h3>加载中...</h3>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import { useTrainingStore } from '@/stores/training'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'

dayjs.extend(relativeTime)

const trainingStore = useTrainingStore()

const loading = ref(false)
const activeTab = ref('all')
const filters = reactive({
  type: '',
  status: '',
  keyword: '',
})

const projects = ref([])
const userProgressMap = ref({})

const tabCounts = computed(() => {
  const all = projects.value.length
  const inProgress = projects.value.filter(p => {
    const progress = p.userProgress || 0
    return progress > 0 && progress < 100
  }).length
  const completed = projects.value.filter(p => (p.userProgress || 0) >= 100).length
  return { all, inProgress, completed }
})

const filteredProjects = computed(() => {
  let result = projects.value

  // Filter by tab
  if (activeTab.value === 'in-progress') {
    result = result.filter((p) => {
      const progress = p.userProgress || 0
      return progress > 0 && progress < 100
    })
  } else if (activeTab.value === 'completed') {
    result = result.filter((p) => (p.userProgress || 0) >= 100)
  }

  // Filter by type
  if (filters.type === 'required') {
    result = result.filter((p) => p.is_required)
  } else if (filters.type === 'optional') {
    result = result.filter((p) => !p.is_required)
  }

  // Filter by status
  if (filters.status) {
    if (filters.status === 'not-started') {
      result = result.filter((p) => (p.userProgress || 0) === 0)
    } else if (filters.status === 'in-progress') {
      result = result.filter((p) => {
        const progress = p.userProgress || 0
        return progress > 0 && progress < 100
      })
    } else if (filters.status === 'completed') {
      result = result.filter((p) => (p.userProgress || 0) >= 100)
    } else if (filters.status === 'deadline-soon') {
      const threeDaysLater = dayjs().add(3, 'day')
      result = result.filter((p) => {
        if (!p.deadline) return false
        const deadline = dayjs(p.deadline)
        return deadline.isBefore(threeDaysLater) && deadline.isAfter(dayjs())
      })
    }
  }

  // Filter by keyword
  if (filters.keyword) {
    const kw = filters.keyword.toLowerCase()
    result = result.filter((p) => p.title.toLowerCase().includes(kw))
  }

  return result
})

function getCoverGradient(project) {
  const gradients = [
    'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)',
    'linear-gradient(135deg, #fc4a1a 0%, #f7b733 100%)',
    'linear-gradient(135deg, #52c41a 0%, #73d13d 100%)',
    'linear-gradient(135deg, #1890ff 0%, #69c0ff 100%)',
    'linear-gradient(135deg, #722ed1 0%, #b37feb 100%)',
  ]
  const index = project.project_id.charCodeAt(project.project_id.length - 1) % gradients.length
  return gradients[index]
}

function getCoverEmoji(project) {
  if (project.title.includes('安全')) return '🛡️'
  if (project.title.includes('技能')) return '💻'
  if (project.title.includes('制度')) return '📋'
  if (project.title.includes('沟通')) return '🤝'
  if (project.title.includes('数据')) return '🔒'
  return '🎬'
}

function getProgressGradient(project) {
  if (project.title.includes('安全')) return 'linear-gradient(90deg, #11998e, #38ef7d)'
  if (project.title.includes('技能')) return 'linear-gradient(90deg, #fc4a1a, #f7b733)'
  if (project.title.includes('制度')) return '#52c41a'
  if (project.title.includes('沟通')) return '#722ed1'
  if (project.title.includes('数据')) return '#1890ff'
  return 'linear-gradient(90deg, #667eea, #764ba2)'
}

function getDeadlineText(deadline) {
  if (!deadline) return '无截止日期'
  const d = dayjs(deadline)
  const now = dayjs()
  if (d.isBefore(now)) return '已截止'
  const diff = d.diff(now, 'day')
  if (diff <= 3) return `还剩${diff}天`
  return d.format('YYYY-MM-DD')
}

function getStatusClass(project) {
  const progress = project.userProgress || 0
  if (progress >= 100) return 'completed'
  if (progress > 0) return 'in-progress'
  return 'not-started'
}

function getStatusText(project) {
  const progress = project.userProgress || 0
  if (progress >= 100) return '已完成'
  if (progress > 0) return '进行中'
  return '未开始'
}

async function fetchProjects() {
  loading.value = true
  try {
    await trainingStore.fetchProjectList({ page: 1, page_size: 100 })
    projects.value = trainingStore.projectList || []

    // Fetch progress for each project
    for (const project of projects.value) {
      try {
        const res = await trainingStore.fetchProgress(project.project_id)
        if (res && res.data) {
          project.userProgress = res.data.overall_status === 2 ? 100 : (res.data.overall_status === 1 ? 50 : 0)
        }
      } catch (e) {
        project.userProgress = 0
      }
    }
  } catch (error) {
    console.error('Failed to fetch projects:', error)
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  // Trigger computed to re-filter
  activeTab.value = activeTab.value
}

onMounted(() => {
  fetchProjects()
})
</script>

<style scoped>
.training-list-page {
  max-width: 1400px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #333;
  margin-bottom: 25px;
}

.filter-bar {
  background: #fff;
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 25px;
  display: flex;
  gap: 20px;
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

.filter-item select,
.filter-item input {
  height: 36px;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  padding: 0 12px;
  font-size: 14px;
}

.filter-item input[type='text'] {
  width: 200px;
}

.filter-btn {
  height: 36px;
  padding: 0 20px;
  background: #667eea;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  margin-left: auto;
}

.filter-btn:hover {
  background: #5a70d9;
}

.tab-bar {
  display: flex;
  gap: 20px;
  margin-bottom: 25px;
}

.tab-item {
  padding: 10px 20px;
  border-radius: 6px;
  font-size: 14px;
  color: #666;
  cursor: pointer;
  background: #fff;
  transition: all 0.3s;
}

.tab-item:hover {
  color: #667eea;
}

.tab-item.active {
  background: #667eea;
  color: #fff;
}

.tab-item .count {
  display: inline-block;
  margin-left: 6px;
  padding: 2px 8px;
  background: rgba(0, 0, 0, 0.1);
  border-radius: 10px;
  font-size: 12px;
}

.tab-item.active .count {
  background: rgba(255, 255, 255, 0.2);
}

.training-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.training-card {
  background: #fff;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  transition: transform 0.3s, box-shadow 0.3s;
  cursor: pointer;
}

.training-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.training-cover {
  height: 140px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 48px;
  position: relative;
}

.training-cover .overlay {
  position: absolute;
  top: 10px;
  right: 10px;
}

.tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.tag.required {
  background: #ffecde;
  color: #ff6600;
}

.tag.optional {
  background: #e6f7ed;
  color: #00a854;
}

.training-content {
  padding: 20px;
}

.training-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 10px;
}

.training-meta {
  font-size: 13px;
  color: #999;
  margin-bottom: 15px;
  display: flex;
  justify-content: space-between;
}

.progress-bar {
  height: 6px;
  background: #f0f0f0;
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-bar .fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  border-radius: 3px;
  transition: width 0.5s;
}

.progress-text {
  font-size: 12px;
  color: #999;
  display: flex;
  justify-content: space-between;
}

.status-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
}

.status-badge.not-started {
  background: #f5f5f5;
  color: #999;
}

.status-badge.in-progress {
  background: #e6f7ff;
  color: #1890ff;
}

.status-badge.completed {
  background: #f6ffed;
  color: #52c41a;
}

.status-badge.deadline-soon {
  background: #fff7e6;
  color: #fa8c16;
}

.empty-state,
.loading-state {
  text-align: center;
  padding: 80px 20px;
  background: #fff;
  border-radius: 10px;
}

.empty-state .icon,
.loading-state .icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.empty-state h3,
.loading-state h3 {
  font-size: 18px;
  color: #333;
  margin-bottom: 10px;
}

.empty-state p {
  font-size: 14px;
  color: #999;
}
</style>