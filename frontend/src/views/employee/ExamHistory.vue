<template>
  <div class="exam-history-page">
    <h1 class="page-title">📝 考试历史</h1>

    <!-- 标签栏 -->
    <div class="tab-bar">
      <div
        class="tab-item"
        :class="{ active: activeTab === 'all' }"
        @click="activeTab = 'all'"
      >
        全部 <span class="count">{{ allCount }}</span>
      </div>
      <div
        class="tab-item"
        :class="{ active: activeTab === 'passed' }"
        @click="activeTab = 'passed'"
      >
        已通过 <span class="count">{{ passedCount }}</span>
      </div>
      <div
        class="tab-item"
        :class="{ active: activeTab === 'failed' }"
        @click="activeTab = 'failed'"
      >
        未通过 <span class="count">{{ failedCount }}</span>
      </div>
    </div>

    <!-- 考试记录列表 -->
    <div class="history-list" v-if="filteredHistory.length">
      <div
        v-for="record in filteredHistory"
        :key="record.attempt_id"
        class="history-card"
        @click="goToExam(record)"
      >
        <div class="card-header">
          <div class="exam-title">{{ record.exam_title }}</div>
          <span class="status-badge" :class="record.passed ? 'passed' : 'failed'">
            {{ record.passed ? '通过' : '未通过' }}
          </span>
        </div>
        <div class="card-body">
          <div class="info-item">
            <span class="label">考试时间：</span>
            <span class="value">{{ formatTime(record.start_time) }}</span>
          </div>
          <div class="info-item">
            <span class="label">用时：</span>
            <span class="value">{{ formatDuration(record.time_spent) }}</span>
          </div>
          <div class="info-item">
            <span class="label">得分：</span>
            <span class="value score" :class="{ pass: record.passed }">
              {{ record.score }}分
            </span>
          </div>
          <div class="info-item" v-if="record.passing_score">
            <span class="label">及格分数：</span>
            <span class="value">{{ record.passing_score }}分</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div class="empty-state" v-else-if="!loading">
      <div class="icon">📋</div>
      <h3>暂无考试记录</h3>
      <p>完成培训课程后即可参加考试</p>
    </div>

    <!-- 加载状态 -->
    <div class="loading-state" v-if="loading">
      <div class="icon">⏳</div>
      <h3>加载中...</h3>
    </div>

    <!-- 分页 -->
    <div class="pagination" v-if="pagination.total > pagination.pageSize">
      <button
        class="btn btn-outline btn-sm"
        :disabled="pagination.page <= 1"
        @click="handlePrevPage"
      >
        上一页
      </button>
      <span class="page-info">
        {{ pagination.page }} / {{ pagination.totalPages }}
      </span>
      <button
        class="btn btn-outline btn-sm"
        :disabled="pagination.page >= pagination.totalPages"
        @click="handleNextPage"
      >
        下一页
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { getExamHistory } from '@/api/exam'
import dayjs from 'dayjs'

const router = useRouter()

const loading = ref(false)
const activeTab = ref('all')
const history = ref([])

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
  totalPages: 0,
})

const allCount = computed(() => history.value.length)
const passedCount = computed(() => history.value.filter(h => h.passed).length)
const failedCount = computed(() => history.value.filter(h => !h.passed && h.score !== null).length)

const filteredHistory = computed(() => {
  if (activeTab.value === 'passed') {
    return history.value.filter(h => h.passed)
  }
  if (activeTab.value === 'failed') {
    return history.value.filter(h => !h.passed && h.score !== null)
  }
  return history.value
})

function formatTime(time) {
  if (!time) return '--'
  return dayjs(time).format('YYYY-MM-DD HH:mm')
}

function formatDuration(seconds) {
  if (!seconds) return '--'
  const hours = Math.floor(seconds / 3600)
  const mins = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  if (hours > 0) return `${hours}小时${mins}分`
  if (mins > 0) return `${mins}分${secs}秒`
  return `${secs}秒`
}

function goToExam(record) {
  // Only allow re-exam if not passed
  if (!record.passed) {
    router.push(`/exam/${record.project_id}`)
  }
}

async function fetchHistory() {
  loading.value = true
  try {
    const res = await getExamHistory({
      page: pagination.page,
      page_size: pagination.pageSize,
    })
    if (res.code === 0) {
      history.value = res.data || []
      pagination.total = res.pagination?.total || 0
      pagination.totalPages = res.pagination?.total_pages || 1
    }
  } catch (error) {
    console.error('Failed to fetch exam history:', error)
  } finally {
    loading.value = false
  }
}

function handlePrevPage() {
  if (pagination.page > 1) {
    pagination.page--
    fetchHistory()
  }
}

function handleNextPage() {
  if (pagination.page < pagination.totalPages) {
    pagination.page++
    fetchHistory()
  }
}

onMounted(() => {
  fetchHistory()
})
</script>

<style scoped>
.exam-history-page {
  max-width: 900px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #333;
  margin-bottom: 25px;
}

.tab-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 25px;
  background: #fff;
  padding: 15px 20px;
  border-radius: 10px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.tab-item {
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 14px;
  color: #666;
  cursor: pointer;
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

.history-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.history-card {
  background: #fff;
  border-radius: 10px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  cursor: pointer;
  transition: transform 0.3s, box-shadow 0.3s;
}

.history-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.exam-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.status-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
}

.status-badge.passed {
  background: #f6ffed;
  color: #52c41a;
}

.status-badge.failed {
  background: #fff1f0;
  color: #ff4d4f;
}

.card-body {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 15px;
}

.info-item {
  display: flex;
  flex-direction: column;
}

.info-item .label {
  font-size: 12px;
  color: #999;
  margin-bottom: 4px;
}

.info-item .value {
  font-size: 14px;
  color: #333;
}

.info-item .value.score {
  font-weight: 600;
  color: #ff4d4f;
}

.info-item .value.score.pass {
  color: #52c41a;
}

.empty-state,
.loading-state {
  text-align: center;
  padding: 60px 20px;
  background: #fff;
  border-radius: 10px;
}

.empty-state .icon,
.loading-state .icon {
  font-size: 48px;
  margin-bottom: 15px;
}

.empty-state h3,
.loading-state h3 {
  font-size: 16px;
  color: #333;
  margin-bottom: 8px;
}

.empty-state p {
  font-size: 14px;
  color: #999;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 15px;
  margin-top: 20px;
}

.page-info {
  font-size: 14px;
  color: #666;
}

.btn {
  height: 32px;
  padding: 0 16px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  border: 1px solid #667eea;
  background: #fff;
  color: #667eea;
  transition: all 0.3s;
}

.btn:hover:not(:disabled) {
  background: #667eea;
  color: #fff;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>