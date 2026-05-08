<template>
  <div class="notification-page">
    <h1 class="page-title">🔔 通知中心</h1>

    <!-- 标签栏 -->
    <div class="tab-bar">
      <div
        class="tab-item"
        :class="{ active: activeTab === 'all' }"
        @click="activeTab = 'all'"
      >
        全部 <span class="count">{{ totalCount }}</span>
      </div>
      <div
        class="tab-item"
        :class="{ active: activeTab === 'unread' }"
        @click="activeTab = 'unread'"
      >
        未读 <span class="count">{{ unreadCount }}</span>
      </div>
      <div
        class="tab-item"
        :class="{ active: activeTab === 'training' }"
        @click="activeTab = 'training'"
      >
        培训通知 <span class="count">{{ trainingCount }}</span>
      </div>
      <div
        class="tab-item"
        :class="{ active: activeTab === 'deadline' }"
        @click="activeTab = 'deadline'"
      >
        截止提醒 <span class="count">{{ deadlineCount }}</span>
      </div>
    </div>

    <!-- 通知列表 -->
    <div class="notification-list" v-if="filteredNotifications.length">
      <div
        v-for="notif in filteredNotifications"
        :key="notif.notif_id"
        class="notification-item"
        :class="{ unread: notif.read_status === 0 }"
        @click="handleClick(notif)"
      >
        <div class="notif-icon" :class="getNotifClass(notif.notif_type)">
          {{ getNotifIcon(notif.notif_type) }}
        </div>
        <div class="notif-content">
          <div class="notif-header">
            <span class="notif-title">{{ notif.title }}</span>
            <span class="notif-time">{{ formatTime(notif.create_time) }}</span>
          </div>
          <div class="notif-body">{{ notif.content }}</div>
          <div class="notif-meta" v-if="notif.project_title">
            来自：{{ notif.project_title }}
          </div>
        </div>
        <div class="notif-actions" v-if="notif.read_status === 0">
          <button class="mark-read-btn" @click.stop="markAsRead(notif.notif_id)">
            标为已读
          </button>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div class="empty-state" v-else-if="!loading">
      <div class="icon">📭</div>
      <h3>暂无通知</h3>
      <p>暂时没有新的通知消息</p>
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
import { getMyNotifications, markNotificationRead } from '@/api/notification'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'

dayjs.extend(relativeTime)

const router = useRouter()

const loading = ref(false)
const activeTab = ref('all')
const notifications = ref([])

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
  totalPages: 0,
})

const totalCount = computed(() => notifications.value.length)
const unreadCount = computed(() => notifications.value.filter(n => n.read_status === 0).length)
const trainingCount = computed(() => notifications.value.filter(n => n.notif_type === 1).length)
const deadlineCount = computed(() => notifications.value.filter(n => n.notif_type === 2).length)

const filteredNotifications = computed(() => {
  if (activeTab.value === 'unread') {
    return notifications.value.filter(n => n.read_status === 0)
  }
  if (activeTab.value === 'training') {
    return notifications.value.filter(n => n.notif_type === 1)
  }
  if (activeTab.value === 'deadline') {
    return notifications.value.filter(n => n.notif_type === 2)
  }
  return notifications.value
})

function getNotifIcon(type) {
  const icons = { 1: '📚', 2: '⏰', 3: '📝' }
  return icons[type] || '🔔'
}

function getNotifClass(type) {
  const classes = { 1: 'training', 2: 'deadline', 3: 'exam' }
  return classes[type] || 'default'
}

function formatTime(time) {
  if (!time) return ''
  return dayjs(time).fromNow()
}

async function fetchNotifications() {
  loading.value = true
  try {
    const res = await getMyNotifications({
      page: pagination.page,
      page_size: pagination.pageSize,
    })
    if (res.code === 0) {
      notifications.value = res.data || []
      pagination.total = res.pagination?.total || 0
      pagination.totalPages = res.pagination?.total_pages || 1
    }
  } catch (error) {
    console.error('Failed to fetch notifications:', error)
  } finally {
    loading.value = false
  }
}

async function markAsRead(notifId) {
  try {
    const res = await markNotificationRead(notifId)
    if (res.code === 0) {
      const notif = notifications.value.find(n => n.notif_id === notifId)
      if (notif) {
        notif.read_status = 1
      }
    }
  } catch (error) {
    console.error('Failed to mark as read:', error)
  }
}

function handleClick(notif) {
  if (notif.read_status === 0) {
    markAsRead(notif.notif_id)
  }
  if (notif.project_id) {
    router.push(`/training/${notif.project_id}`)
  }
}

function handlePrevPage() {
  if (pagination.page > 1) {
    pagination.page--
    fetchNotifications()
  }
}

function handleNextPage() {
  if (pagination.page < pagination.totalPages) {
    pagination.page++
    fetchNotifications()
  }
}

onMounted(() => {
  fetchNotifications()
})
</script>

<style scoped>
.notification-page {
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

.notification-list {
  background: #fff;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.notification-item {
  display: flex;
  align-items: flex-start;
  gap: 15px;
  padding: 20px;
  border-bottom: 1px solid #f5f7fa;
  cursor: pointer;
  transition: background 0.3s;
}

.notification-item:last-child {
  border-bottom: none;
}

.notification-item:hover {
  background: #f8f8ff;
}

.notification-item.unread {
  background: #f0f6ff;
}

.notification-item.unread:hover {
  background: #e6f0ff;
}

.notif-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}

.notif-icon.training { background: #e6f0ff; }
.notif-icon.deadline { background: #fff3e6; }
.notif-icon.exam { background: #f3e6ff; }
.notif-icon.default { background: #f5f7fa; }

.notif-content {
  flex: 1;
  min-width: 0;
}

.notif-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.notif-title {
  font-size: 15px;
  font-weight: 500;
  color: #333;
}

.notif-time {
  font-size: 12px;
  color: #999;
  flex-shrink: 0;
  margin-left: 10px;
}

.notif-body {
  font-size: 14px;
  color: #666;
  line-height: 1.6;
  margin-bottom: 8px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.notif-meta {
  font-size: 12px;
  color: #999;
}

.notif-actions {
  flex-shrink: 0;
}

.mark-read-btn {
  padding: 4px 12px;
  background: #fff;
  border: 1px solid #667eea;
  border-radius: 4px;
  color: #667eea;
  font-size: 12px;
  cursor: pointer;
}

.mark-read-btn:hover {
  background: #667eea;
  color: #fff;
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