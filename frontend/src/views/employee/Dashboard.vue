<template>
  <div class="dashboard">
    <!-- 欢迎横幅 -->
    <div class="welcome-banner">
      <h2>👋 {{ userStore.userInfo?.real_name || '用户' }}，欢迎回来！</h2>
      <p>您有 {{ stats.pendingCount }} 项培训即将截止，请尽快完成学习～</p>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="icon blue">📚</div>
        <div class="value">{{ stats.requiredCount }}</div>
        <div class="label">进行中的培训</div>
      </div>
      <div class="stat-card">
        <div class="icon green">✅</div>
        <div class="value">{{ stats.completedCount }}</div>
        <div class="label">已完成培训</div>
      </div>
      <div class="stat-card">
        <div class="icon orange">⏰</div>
        <div class="value">{{ stats.pendingCount }}</div>
        <div class="label">待完成考试</div>
      </div>
      <div class="stat-card">
        <div class="icon purple">🔔</div>
        <div class="value">{{ notificationCount }}</div>
        <div class="label">未读通知</div>
      </div>
    </div>

    <!-- 进行中培训 -->
    <div class="section-title">
      <span>📖 进行中的培训</span>
      <router-link to="/training">查看全部 →</router-link>
    </div>
    <div class="training-grid" v-if="inProgressProjects.length">
      <div
        v-for="project in inProgressProjects"
        :key="project.project_id"
        class="training-card"
        @click="$router.push(`/training/${project.project_id}`)"
      >
        <div class="training-cover" :style="{ background: getCoverGradient(project) }">
          {{ getCoverEmoji(project) }}
        </div>
        <div class="training-content">
          <div class="training-title">{{ project.title }}</div>
          <div class="training-meta">
            <span class="tag" :class="project.is_required ? 'required' : 'optional'">
              {{ project.is_required ? '必修' : '选修' }}
            </span>
            <span class="tag deadline" v-if="project.deadline">
              还剩{{ getDaysLeft(project.deadline) }}天
            </span>
          </div>
          <div class="progress-bar">
            <div class="fill" :style="{ width: (project.progress || 0) + '%' }"></div>
          </div>
          <div class="progress-text">
            <span>学习进度 {{ project.progress || 0 }}%</span>
            <span>{{ project.materialCompleted || 0 }}/{{ project.materialTotal || 0 }} 材料</span>
          </div>
        </div>
      </div>
    </div>
    <div class="empty-tip" v-else>
      <p>暂无进行中的培训</p>
    </div>

    <!-- 最近通知 -->
    <div class="section-title">
      <span>🔔 最近通知</span>
      <router-link to="/notification">查看全部 →</router-link>
    </div>
    <div class="notification-list" v-if="recentNotifications.length">
      <div
        v-for="notif in recentNotifications"
        :key="notif.notif_id"
        class="notification-item"
        :class="{ unread: notif.read_status === 0 }"
      >
        <div class="notif-icon">{{ getNotifIcon(notif.notif_type) }}</div>
        <div class="notif-content">
          <div class="notif-title">{{ notif.title }}</div>
          <div class="notif-time">{{ formatTime(notif.create_time) }}</div>
        </div>
      </div>
    </div>
    <div class="empty-tip" v-else>
      <p>暂无通知</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { useTrainingStore } from '@/stores/training'
import { useThemeStore } from '@/stores/theme'
import { getMyNotifications } from '@/api/notification'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'

dayjs.extend(relativeTime)

const userStore = useUserStore()
const trainingStore = useTrainingStore()
const themeStore = useThemeStore()

const stats = ref({
  requiredCount: 0,
  completedCount: 0,
  pendingCount: 0,
})

const notificationCount = ref(0)
const inProgressProjects = ref([])
const recentNotifications = ref([])

function getCoverGradient(project) {
  const gradients = [
    themeStore.themes[themeStore.currentTheme]?.gradient || 'var(--theme-gradient)',
    'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)',
    'linear-gradient(135deg, #fc4a1a 0%, #f7b733 100%)',
    'linear-gradient(135deg, #52c41a 0%, #73d13d 100%)',
    'linear-gradient(135deg, #1890ff 0%, #69c0ff 100%)',
    'linear-gradient(135deg, #722ed1 0%, #b37feb 100%)',
  ]
  const index = project.project_id?.charCodeAt(project.project_id.length - 1) % gradients.length || 0
  return gradients[index]
}

function getCoverEmoji(project) {
  if (!project.title) return '📚'
  if (project.title.includes('安全')) return '🛡️'
  if (project.title.includes('技能')) return '💻'
  if (project.title.includes('制度')) return '📋'
  if (project.title.includes('沟通')) return '🤝'
  if (project.title.includes('数据')) return '🔒'
  return '📚'
}

function getDaysLeft(deadline) {
  if (!deadline) return 0
  const now = dayjs()
  const end = dayjs(deadline)
  return Math.max(0, end.diff(now, 'day'))
}

function getNotifIcon(type) {
  const icons = { 1: '📚', 2: '⏰', 3: '📝' }
  return icons[type] || '🔔'
}

function formatTime(time) {
  if (!time) return ''
  return dayjs(time).fromNow()
}

async function fetchDashboardData() {
  try {
    // Fetch project list
    await trainingStore.fetchProjectList({ page: 1, page_size: 50 })
    const projects = trainingStore.projectList || []

    // Fetch user progress for each project
    const inProgress = []
    let completed = 0

    for (const project of projects) {
      try {
        const progress = await trainingStore.fetchProgress(project.project_id)

        // Calculate actual progress percentage based on materials
        const materials = progress?.materials || []
        let progressPct = 0
        if (materials.length > 0) {
          const totalProgress = materials.reduce((sum, m) => sum + (m.progress || 0), 0)
          progressPct = Math.round(totalProgress / materials.length)
        } else if (progress?.overall_status === 2) {
          progressPct = 100
        }

        const completedCount = materials.filter(m => m.is_completed).length

        if (progressPct >= 100) {
          completed++
        } else {
          inProgress.push({
            ...project,
            progress: progressPct,
            materialCompleted: completedCount,
            materialTotal: materials.length,
          })
        }
      } catch (e) {
        inProgress.push({
          ...project,
          progress: 0,
          materialCompleted: 0,
          materialTotal: 0,
        })
      }
    }

    inProgressProjects.value = inProgress.slice(0, 6)
    stats.value.requiredCount = inProgress.length
    stats.value.completedCount = completed
    stats.value.pendingCount = 0 // Would need exam API

    // Fetch notifications
    try {
      const notifRes = await getMyNotifications({ page: 1, page_size: 5 })
      if (notifRes.code === 0) {
        recentNotifications.value = notifRes.data || []
        notificationCount.value = notifRes.data?.filter(n => n.read_status === 0).length || 0
      }
    } catch (e) {
      console.error('Failed to fetch notifications:', e)
    }
  } catch (error) {
    console.error('Failed to fetch dashboard data:', error)
  }
}

onMounted(() => {
  fetchDashboardData()
})
</script>

<style scoped>
.dashboard {
  max-width: 1400px;
}

.welcome-banner {
  background: var(--theme-gradient);
  border-radius: 12px;
  padding: 30px;
  color: #fff;
  margin-bottom: 30px;
}

.welcome-banner h2 {
  font-size: 24px;
  margin-bottom: 8px;
}

.welcome-banner p {
  font-size: 14px;
  opacity: 0.9;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  background: #fff;
  border-radius: 10px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.stat-card .icon {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  margin-bottom: 15px;
}

.stat-card .icon.blue { background: #e6f0ff; }
.stat-card .icon.green { background: #e6f7ed; }
.stat-card .icon.orange { background: #fff3e6; }
.stat-card .icon.purple { background: #f3e6ff; }

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

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-title a {
  font-size: 14px;
  color: var(--theme-primary);
  text-decoration: none;
}

.section-title a:hover {
  text-decoration: underline;
}

.training-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 40px;
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
  height: 120px;
  background: var(--theme-gradient);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 40px;
}

.training-content {
  padding: 16px;
}

.training-title {
  font-size: 15px;
  font-weight: 600;
  color: #333;
  margin-bottom: 10px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.training-meta {
  font-size: 12px;
  color: #999;
  margin-bottom: 12px;
}

.tag {
  display: inline-block;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  margin-right: 6px;
}

.tag.required { background: #ffecde; color: #ff6600; }
.tag.optional { background: #e6f7ed; color: #00a854; }
.tag.deadline { background: #fff; color: #d93026; border: 1px solid #d93026; }

.progress-bar {
  height: 5px;
  background: #f0f0f0;
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-bar .fill {
  height: 100%;
  background: var(--theme-gradient);
  border-radius: 3px;
}

.progress-text {
  font-size: 11px;
  color: #999;
  display: flex;
  justify-content: space-between;
}

.notification-list {
  background: #fff;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  margin-bottom: 40px;
}

.notification-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 16px 20px;
  border-bottom: 1px solid #f5f7fa;
}

.notification-item:last-child {
  border-bottom: none;
}

.notification-item.unread {
  background: #f8f8ff;
}

.notification-item:hover {
  background: #f5f7fa;
}

.notif-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: #e6f0ff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}

.notif-content {
  flex: 1;
}

.notif-title {
  font-size: 14px;
  color: #333;
  margin-bottom: 4px;
}

.notif-time {
  font-size: 12px;
  color: #999;
}

.empty-tip {
  text-align: center;
  padding: 40px;
  background: #fff;
  border-radius: 10px;
  margin-bottom: 40px;
  color: #999;
}
</style>