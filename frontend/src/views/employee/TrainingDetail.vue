<template>
  <div class="training-detail">
    <a class="back-btn" @click="$router.back()">← 返回培训列表</a>

    <!-- 项目详情头部 -->
    <div class="detail-header" v-if="project">
      <div class="detail-cover" :style="{ background: coverGradient }">
        {{ coverEmoji }}
      </div>
      <div class="detail-info">
        <h1 class="detail-title">{{ project.title }}</h1>
        <div class="detail-tags">
          <span class="tag" :class="project.is_required ? 'required' : 'optional'">
            {{ project.is_required ? '必修' : '选修' }}
          </span>
          <span class="tag" style="background: #e6f0ff; color: #1890ff;">
            📹 {{ videoCount }}个视频
          </span>
          <span class="tag" style="background: #fff7e6; color: #fa8c16;">
            📄 {{ docCount }}个文档
          </span>
        </div>
        <div class="detail-meta">
          <span>⏱️ 预计时长 {{ totalDuration }}</span>
          <span>📅 截止日期 {{ formatDate(project.deadline) }}</span>
          <span>👀 {{ enrolledCount }}人已学习</span>
        </div>
        <div class="progress-section">
          <div class="progress-label">
            <span>学习进度</span>
            <span>{{ userProgress }}%</span>
          </div>
          <div class="progress-bar">
            <div class="fill" :style="{ width: userProgress + '%' }"></div>
          </div>
        </div>
        <div class="action-btns">
          <button class="btn btn-primary" @click="continueLearn">继续学习</button>
          <button
            class="btn btn-outline"
            @click="goExam"
            :disabled="userProgress < 100 || !hasExam"
          >
            参加考试
          </button>
        </div>
      </div>
    </div>

    <div class="content-layout">
      <!-- 左侧内容 -->
      <div>
        <!-- 学习材料 -->
        <div class="panel">
          <h2 class="panel-title">📚 学习材料</h2>

          <div
            v-for="(material, index) in materials"
            :key="material.material_id"
            class="material-item"
            :class="{ completed: isMaterialCompleted(material) }"
            @click="openMaterial(material)"
          >
            <div class="icon" :class="material.is_video ? 'video' : 'doc'">
              {{ material.is_video ? '🎬' : '📄' }}
            </div>
            <div class="info">
              <div class="title">{{ index + 1 }}. {{ material.title }}</div>
              <div class="meta">
                {{ material.is_video ? '视频' : '文档' }}
                {{ material.duration ? ' · ' + formatDuration(material.duration) : '' }}
                <span v-if="isMaterialCompleted(material)"> · 已看完</span>
                <span v-else-if="getMaterialProgress(material) > 0"> · 已观看 {{ formatDuration(getMaterialProgress(material)) }}</span>
              </div>
            </div>
            <div class="status" :class="getMaterialStatusClass(material)">
              {{ getMaterialStatusText(material) }}
            </div>
          </div>

          <div v-if="materials.length === 0 && !loading" class="empty-tip">
            暂无学习材料
          </div>
        </div>

        <!-- 考试信息 -->
        <div class="panel" v-if="exam">
          <h2 class="panel-title">📝 培训考试</h2>
          <div class="exam-section">
            <div class="exam-header">
              <span class="exam-title">{{ exam.title || '培训结业考试' }}</span>
              <span class="exam-tag">必须通过</span>
            </div>
            <div class="exam-info">
              <p>🎯 及格分数：{{ exam.passing_score || 60 }}分</p>
              <p>⏱️ 考试时长：{{ exam.duration || 60 }}分钟</p>
              <p>🔄 允许次数：{{ exam.allow_retry !== false ? '无限' : '1次' }}</p>
              <p>📌 当前状态：<span :style="{ color: userProgress >= 100 ? '#52c41a' : '#fa8c16' }">
                {{ userProgress >= 100 ? '可参加考试' : '需完成全部材料后参加' }}
              </span></p>
            </div>
            <button
              class="btn btn-primary exam-btn"
              :disabled="userProgress < 100"
            >
              {{ userProgress >= 100 ? '参加考试' : '完成学习后参加考试' }}
            </button>
          </div>
        </div>

        <!-- 评论区 -->
        <div class="panel">
          <h2 class="panel-title">💬 学员讨论</h2>
          <div class="comment-section">
            <div class="comment-input-wrap">
              <textarea v-model="commentContent" placeholder="发表你的看法...（文明发言哦）"></textarea>
              <button class="btn btn-primary" style="height: 80px; width: 100px;" @click="submitComment">
                发表
              </button>
            </div>

            <div v-if="comments.length === 0 && !loading" class="empty-tip">
              暂无评论，快来发表第一条评论吧
            </div>

            <div class="comment-item" v-for="comment in comments" :key="comment.comment_id">
              <div class="comment-avatar">{{ getAvatarName(comment.user_name) }}</div>
              <div class="comment-content">
                <div class="comment-user">
                  {{ comment.user_name }}
                  <span style="font-weight: normal; color: #999; font-size: 12px;">
                    {{ formatCommentTime(comment.create_time) }}
                  </span>
                </div>
                <div class="comment-text">{{ comment.content }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 侧边栏 -->
      <div class="sidebar">
        <div class="progress-card" v-if="project">
          <div class="big-num">{{ userProgress }}%</div>
          <div class="label">学习进度</div>
          <div class="sub">完成{{ materials.length }}/{{ materials.length }}个材料后可参加考试</div>
        </div>

        <div class="panel">
          <h2 class="panel-title">📊 培训信息</h2>
          <div class="info-list" v-if="project">
            <div class="info-item">
              <span class="label">培训类型</span>
              <span class="value">{{ project.is_required ? '必修' : '选修' }}</span>
            </div>
            <div class="info-item">
              <span class="label">参与人数</span>
              <span class="value">--</span>
            </div>
            <div class="info-item">
              <span class="label">完成人数</span>
              <span class="value">--</span>
            </div>
            <div class="info-item">
              <span class="label">平均成绩</span>
              <span class="value">--</span>
            </div>
            <div class="info-item">
              <span class="label">发布时间</span>
              <span class="value">{{ formatDate(project.published_at) }}</span>
            </div>
            <div class="info-item">
              <span class="label">截止日期</span>
              <span class="value" :style="{ color: isDeadlineSoon ? '#fa8c16' : '#333' }">
                {{ formatDate(project.deadline) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onActivated, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTrainingStore } from '@/stores/training'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'

dayjs.extend(relativeTime)

const route = useRoute()
const router = useRouter()
const trainingStore = useTrainingStore()

const loading = ref(false)
const project = ref(null)
const materials = ref([])
const exam = ref(null)
const comments = ref([])
const userProgress = ref(0)
const commentContent = ref('')
const materialProgressMap = ref({})

const enrolledCount = ref('--')
const isDeadlineSoon = computed(() => {
  if (!project.value?.deadline) return false
  const diff = dayjs(project.value.deadline).diff(dayjs(), 'day')
  return diff <= 3 && diff >= 0
})

const coverGradient = computed(() => {
  if (!project.value) return 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
  const gradients = [
    'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)',
    'linear-gradient(135deg, #fc4a1a 0%, #f7b733 100%)',
    'linear-gradient(135deg, #52c41a 0%, #73d13d 100%)',
    'linear-gradient(135deg, #1890ff 0%, #69c0ff 100%)',
    'linear-gradient(135deg, #722ed1 0%, #b37feb 100%)',
  ]
  const id = project.value.project_id || ''
  const index = id.charCodeAt(id.length - 1) % gradients.length
  return gradients[index]
})

const coverEmoji = computed(() => {
  if (!project.value?.title) return '🎬'
  const title = project.value.title
  if (title.includes('安全')) return '🛡️'
  if (title.includes('技能')) return '💻'
  if (title.includes('制度')) return '📋'
  if (title.includes('沟通')) return '🤝'
  if (title.includes('数据')) return '🔒'
  return '🎬'
})

const docCount = computed(() => {
  return materials.value.filter(m => !m.is_video).length
})

const videoCount = computed(() => {
  return materials.value.filter(m => m.is_video).length
})

const totalDuration = computed(() => {
  const totalSeconds = materials.value.reduce((sum, m) => sum + (m.duration || 0), 0)
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  if (hours > 0) return `${hours}小时${minutes}分钟`
  return `${minutes}分钟`
})

const hasExam = computed(() => !!exam.value)

function formatDate(date) {
  if (!date) return '--'
  return dayjs(date).format('YYYY-MM-DD')
}

function formatDuration(seconds) {
  if (!seconds) return '0秒'
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  if (mins > 0) return `${mins}分${secs}秒`
  return `${secs}秒`
}

function getMaterialProgress(material) {
  const data = materialProgressMap.value[material.material_id]
  console.log('[DEBUG] getMaterialProgress:', material.material_id, 'data:', data)
  // Return total_watched_seconds if available (actual watched time)
  // Otherwise fall back to max_position (furthest position reached)
  if (data?.total_watched_seconds > 0) {
    console.log('[DEBUG] getMaterialProgress returning total_watched_seconds:', data.total_watched_seconds)
    return data.total_watched_seconds
  }
  if (data?.max_position > 0) {
    console.log('[DEBUG] getMaterialProgress returning max_position:', data.max_position)
    return data.max_position
  }
  return data?.progress || 0
}

function isMaterialCompleted(material) {
  const completed = materialProgressMap.value[material.material_id]?.is_completed
  console.log('[DEBUG] isMaterialCompleted:', material.material_id, 'completed:', completed)
  return completed
}

function getMaterialStatusClass(material) {
  const data = materialProgressMap.value[material.material_id]
  console.log('[DEBUG] getMaterialStatusClass:', material.material_id, 'data:', data)
  if (isMaterialCompleted(material)) {
    console.log('[DEBUG] getMaterialStatusClass returning: completed')
    return 'completed'
  }
  // Check max_position instead of progress, since progress may be 0 when total_duration is unknown
  if (data?.max_position > 0) {
    console.log('[DEBUG] getMaterialStatusClass returning: in-progress')
    return 'in-progress'
  }
  console.log('[DEBUG] getMaterialStatusClass returning: not-start')
  return 'not-start'
}

function getMaterialStatusText(material) {
  if (isMaterialCompleted(material)) return '✅ 已完成'
  const progress = getMaterialProgress(material)
  if (progress > 0) return '▶️ 继续观看'
  return '📖 点击学习'
}

function getAvatarName(name) {
  if (!name) return '?'
  return name.charAt(0)
}

function formatCommentTime(time) {
  if (!time) return ''
  return dayjs(time).fromNow()
}

function continueLearn() {
  // Find first incomplete material
  const nextMaterial = materials.value.find(m => !isMaterialCompleted(m))
  if (nextMaterial) {
    router.push(`/training/${route.params.id}/material/${nextMaterial.material_id}`)
  }
}

function openMaterial(material) {
  router.push(`/training/${route.params.id}/material/${material.material_id}`)
}

function goExam() {
  if (exam.value && userProgress.value >= 100) {
    router.push(`/exam/${route.params.id}`)
  }
}

async function fetchProjectDetail() {
  loading.value = true
  try {
    await trainingStore.fetchProjectDetail(route.params.id)
    project.value = trainingStore.currentProject
    materials.value = (trainingStore.materials || []).map(m => ({
      ...m,
      is_video: m.material_type === 1,
    }))
    exam.value = trainingStore.currentProject?.exam || null
  } catch (error) {
    console.error('Failed to fetch project detail:', error)
  } finally {
    loading.value = false
  }
}

async function fetchProgress() {
  try {
    const res = await trainingStore.fetchProgress(route.params.id)
    console.log('[DEBUG] fetchProgress response:', res)
    // trainingStore.fetchProgress returns res.data directly, so res is the data object
    if (res && res.materials) {
      // Calculate progress based on actual material completion
      const totalMaterials = res.materials.length
      let completedCount = 0
      let totalProgress = 0

      res.materials.forEach(m => {
        if (m.is_completed) {
          completedCount++
          totalProgress += 100
        } else if (m.max_position > 0) {
          // Has progress but not completed - use progress percentage
          totalProgress += (m.progress || 0)
        }
      })

      // Calculate overall percentage
      if (totalMaterials > 0) {
        userProgress.value = Math.round(totalProgress / totalMaterials)
      } else {
        userProgress.value = 0
      }
      console.log('[DEBUG] userProgress calculated:', userProgress.value, 'completed:', completedCount, 'total:', totalMaterials)

      // Map material progress
      const progressMap = {}
      ;(res.materials || []).forEach(m => {
        console.log('[DEBUG] material progress:', m.material_id, 'progress:', m.progress, 'max_position:', m.max_position, 'total_watched:', m.total_watched_seconds)
        progressMap[m.material_id] = {
          progress: m.progress || 0,
          is_completed: m.is_completed || false,
          max_position: m.max_position || 0,
          total_watched_seconds: m.total_watched_seconds || 0,
        }
      })
      materialProgressMap.value = progressMap
      console.log('[DEBUG] Updated progressMap:', progressMap)
    } else {
      console.log('[DEBUG] fetchProgress: no materials in response or invalid res:', res)
    }
  } catch (error) {
    console.error('Failed to fetch progress:', error)
  }
}

function submitComment() {
  if (!commentContent.value.trim()) {
    ElMessage.warning('请输入评论内容')
    return
  }
  ElMessage.success('评论功能开发中...')
  commentContent.value = ''
}

onMounted(async () => {
  await fetchProjectDetail()
  await fetchProgress()
  console.log('[DEBUG] TrainingDetail mounted, progress:', materialProgressMap.value)
})

// Watch for route changes to refresh data when returning from video player
watch(
  () => route.path,
  async (newPath, oldPath) => {
    console.log('[DEBUG] Route changed:', oldPath, '->', newPath)
    if (newPath.includes('/training/') && !newPath.includes('/material/')) {
      console.log('[DEBUG] Detected return to training detail, refreshing project detail and progress')
      await fetchProjectDetail()  // Refresh to get updated material durations
      await fetchProgress()
    }
  }
)
</script>

<style scoped>
.training-detail {
  max-width: 1200px;
  font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #667eea;
  text-decoration: none;
  font-size: 14px;
  margin-bottom: 20px;
  cursor: pointer;
}

.back-btn:hover {
  text-decoration: underline;
}

.detail-header {
  background: #fff;
  border-radius: 12px;
  padding: 30px;
  margin-bottom: 20px;
  display: flex;
  gap: 30px;
}

.detail-cover {
  width: 280px;
  height: 160px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 64px;
  color: #fff;
  flex-shrink: 0;
}

.detail-info {
  flex: 1;
}

.detail-title {
  font-size: 22px;
  font-weight: 600;
  color: #333;
  margin-bottom: 12px;
}

.detail-tags {
  margin-bottom: 15px;
}

.tag {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 13px;
  margin-right: 10px;
}

.tag.required {
  background: #ffecde;
  color: #ff6600;
}

.tag.optional {
  background: #e6f7ed;
  color: #00a854;
}

.detail-meta {
  font-size: 14px;
  color: #666;
  margin-bottom: 20px;
}

.detail-meta span {
  margin-right: 25px;
}

.progress-section {
  margin-bottom: 20px;
}

.progress-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
  display: flex;
  justify-content: space-between;
}

.progress-bar {
  height: 10px;
  background: #f0f0f0;
  border-radius: 5px;
  overflow: hidden;
}

.progress-bar .fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  border-radius: 5px;
  transition: width 0.5s;
}

.action-btns {
  display: flex;
  gap: 12px;
}

.btn {
  height: 40px;
  padding: 0 24px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  border: none;
  transition: all 0.3s;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.btn-primary:hover:not(:disabled) {
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

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.content-layout {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 20px;
}

.panel {
  background: #fff;
  border-radius: 12px;
  padding: 25px;
  margin-bottom: 20px;
}

.panel-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #f0f0f0;
}

.material-item {
  display: flex;
  align-items: center;
  padding: 15px;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  margin-bottom: 12px;
  cursor: pointer;
  transition: all 0.3s;
}

.material-item:hover {
  border-color: #667eea;
  background: #f8f8ff;
}

.material-item.completed {
  border-color: #52c41a;
  background: #f6ffed;
}

.material-item .icon {
  width: 44px;
  height: 44px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  margin-right: 15px;
}

.material-item .icon.video {
  background: #e6f0ff;
}

.material-item .icon.doc {
  background: #fff7e6;
}

.material-item .info {
  flex: 1;
}

.material-item .title {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
}

.material-item .meta {
  font-size: 12px;
  color: #999;
}

.material-item .status {
  font-size: 13px;
}

.material-item .status.not-start {
  color: #999;
}

.material-item .status.in-progress {
  color: #1890ff;
}

.material-item .status.completed {
  color: #52c41a;
}

.exam-section {
  background: linear-gradient(135deg, #fff7e6 0%, #fffbe6 100%);
  border: 1px solid #ffe58f;
  border-radius: 8px;
  padding: 20px;
}

.exam-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 15px;
}

.exam-title {
  font-size: 15px;
  font-weight: 600;
  color: #333;
}

.exam-tag {
  background: #faad14;
  color: #fff;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.exam-info {
  font-size: 13px;
  color: #666;
  margin-bottom: 15px;
}

.exam-info p {
  margin-bottom: 6px;
}

.exam-btn {
  width: 100%;
}

.comment-section {
  margin-top: 20px;
}

.comment-input-wrap {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.comment-input-wrap textarea {
  flex: 1;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  padding: 12px;
  font-size: 14px;
  resize: none;
  height: 80px;
  font-family: inherit;
}

.comment-input-wrap textarea:focus {
  outline: none;
  border-color: #667eea;
}

.comment-item {
  display: flex;
  gap: 12px;
  padding: 15px 0;
  border-bottom: 1px solid #f5f7fa;
}

.comment-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #667eea;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  flex-shrink: 0;
}

.comment-content {
  flex: 1;
}

.comment-user {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
}

.comment-text {
  font-size: 14px;
  color: #666;
  line-height: 1.6;
}

.sidebar .progress-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 10px;
  padding: 25px;
  color: #fff;
  text-align: center;
  margin-bottom: 20px;
}

.progress-card .big-num {
  font-size: 48px;
  font-weight: 700;
  line-height: 1;
  margin-bottom: 5px;
}

.progress-card .label {
  font-size: 14px;
  opacity: 0.9;
}

.progress-card .sub {
  font-size: 13px;
  opacity: 0.8;
  margin-top: 15px;
}

.info-list .info-item {
  display: flex;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid #f5f7fa;
  font-size: 14px;
}

.info-list .info-item:last-child {
  border-bottom: none;
}

.info-list .label {
  color: #999;
}

.info-list .value {
  color: #333;
  font-weight: 500;
}

.empty-tip {
  text-align: center;
  color: #999;
  padding: 20px;
}
</style>