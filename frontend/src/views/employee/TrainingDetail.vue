<template>
  <div class="training-detail">
    <a class="back-btn" @click="$router.push('/training')">← 返回培训列表</a>

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
              <span class="exam-tag" :class="{ passed: exam.has_passed }">{{ exam.has_passed ? '已通过' : '未通过' }}</span>
            </div>
            <div class="exam-info">
              <p>🎯 及格分数：{{ exam.passing_score || 60 }}分</p>
              <p>⏱️ 考试时长：{{ exam.duration_minutes || 60 }}分钟</p>
              <p>🔄 允许次数：{{ exam.attempt_limit || 1 }}次</p>
              <p>📊 考试次数：已考{{ exam.attempt_count || 0 }}次，剩余{{ exam.remaining_attempts || 0 }}次</p>
              <p v-if="exam.best_score != null">🏆 最高成绩：{{ exam.best_score }}分</p>
              <p>📌 当前状态：
                <span v-if="exam.has_passed" style="color: #52c41a">已通过</span>
                <span v-else-if="userProgress < 100" style="color: #fa8c16">需完成全部材料后参加</span>
                <span v-else-if="exam.remaining_attempts <= 0" style="color: #f56c6c">已无考试机会</span>
                <span v-else style="color: #1890ff">可参加考试</span>
              </p>
            </div>
            <div class="exam-actions">
              <button
                class="btn btn-primary exam-btn"
                :disabled="userProgress < 100 || exam.has_passed || exam.remaining_attempts <= 0"
                @click="goExam"
              >
                {{ exam.has_passed ? '已通过' : userProgress < 100 ? '完成学习后参加' : exam.remaining_attempts <= 0 ? '无考试机会' : '参加考试' }}
              </button>
              <el-button link @click="goToExamHistory">查看考试成绩</el-button>
            </div>
          </div>
        </div>

        <!-- 评论区 -->
        <div class="panel">
          <h2 class="panel-title">💬 学员讨论</h2>

          <!-- 项目评论Tab -->
          <el-tabs v-model="commentTab">
            <el-tab-pane label="项目评论" name="project"></el-tab-pane>
            <el-tab-pane v-if="currentMaterialId" label="资料评论" name="material"></el-tab-pane>
          </el-tabs>

          <div class="comment-section">
            <!-- 评论输入 -->
            <div class="comment-input-wrap">
              <div class="input-container">
                <textarea
                  ref="commentInput"
                  v-model="commentContent"
                  :placeholder="replyTo ? `回复 @${replyTo.user_name}...` : '发表你的看法...（输入 @ 提及用户）'"
                  @input="handleCommentInput"
                  @keydown.enter.ctrl="submitComment"
                ></textarea>
                <!-- @提及用户搜索 -->
                <div v-if="mentionSearchVisible" class="mention-dropdown">
                  <div
                    v-for="user in mentionUsers"
                    :key="user.user_id"
                    class="mention-item"
                    @click="selectMention(user)"
                  >
                    <span class="mention-name">{{ user.real_name }}</span>
                    <span class="mention-username">@{{ user.username }}</span>
                  </div>
                  <div v-if="mentionUsers.length === 0 && mentionKeyword" class="mention-empty">
                    未找到用户
                  </div>
                </div>
              </div>
              <div class="input-actions">
                <div class="action-left">
                  <span v-if="replyTo" class="reply-hint">
                    回复 @{{ replyTo.user_name }}
                    <span class="cancel-reply" @click="cancelReply">×</span>
                  </span>
                  <!-- 表情按钮 -->
                  <span class="emoji-btn" @click="toggleEmojiPicker">
                    😀
                  </span>
                  <!-- 表情选择器 -->
                  <div v-if="emojiPickerVisible" class="emoji-dropdown">
                    <div class="emoji-grid">
                      <span
                        v-for="emoji in emojiList"
                        :key="emoji"
                        class="emoji-item"
                        @click="insertEmoji(emoji)"
                      >{{ emoji }}</span>
                    </div>
                  </div>
                </div>
                <button class="btn btn-primary" @click="submitComment" :disabled="!commentContent.trim()">
                  发表
                </button>
              </div>
            </div>

            <div v-if="comments.length === 0 && !commentLoading" class="empty-tip">
              暂无评论，快来发表第一条评论吧
            </div>

            <!-- 评论列表 -->
            <div class="comment-list">
              <div class="comment-item" v-for="comment in comments" :key="comment.comment_id">
                <div class="comment-avatar">{{ getAvatarName(comment.user_name) }}</div>
                <div class="comment-content">
                  <div class="comment-user">
                    {{ comment.user_name }}
                    <span class="comment-time">{{ formatCommentTime(comment.create_time) }}</span>
                  </div>
                  <div class="comment-text">
                    {{ comment.content }}
                  </div>
                  <div class="comment-actions">
                    <span class="action-btn like-btn" :class="{ liked: comment.liked }" @click="toggleLike(comment)">
                      {{ comment.liked ? '❤️' : '🤍' }} {{ comment.like_count || '' }}
                    </span>
                    <span class="action-btn" @click="startReply(comment)">回复</span>
                    <span v-if="comment.user_id === currentUserId || isHrAdmin" class="action-btn delete-btn" @click="handleDeleteComment(comment)">
                      删除
                    </span>
                  </div>

                  <!-- 回复列表 -->
                  <div v-if="comment.replies && comment.replies.length > 0" class="reply-list">
                    <div class="comment-item reply-item" v-for="reply in comment.replies" :key="reply.comment_id">
                      <div class="comment-avatar small">{{ getAvatarName(reply.user_name) }}</div>
                      <div class="comment-content">
                        <div class="comment-user">
                          {{ reply.user_name }}
                          <span class="comment-time">{{ formatCommentTime(reply.create_time) }}</span>
                        </div>
                        <div class="comment-text">{{ reply.content }}</div>
                        <div class="comment-actions">
                          <span class="action-btn like-btn" :class="{ liked: reply.liked }" @click="toggleLike(reply)">
                            {{ reply.liked ? '❤️' : '🤍' }} {{ reply.like_count || '' }}
                          </span>
                          <span class="action-btn" @click="startReply(reply, comment)">回复</span>
                          <span v-if="reply.user_id === currentUserId || isHrAdmin" class="action-btn delete-btn" @click="handleDeleteComment(reply)">
                            删除
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
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
import { ref, computed, onMounted, onActivated, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTrainingStore } from '@/stores/training'
import { useUserStore } from '@/stores/user'
import { useThemeStore } from '@/stores/theme'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getComments, createComment, deleteComment, likeComment, unlikeComment, searchUsers } from '@/api/comment'
import { getExamDetail } from '@/api/exam'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'

dayjs.extend(relativeTime)

const route = useRoute()
const router = useRouter()
const trainingStore = useTrainingStore()
const userStore = useUserStore()
const themeStore = useThemeStore()

const loading = ref(false)
const commentLoading = ref(false)
const project = ref(null)
const materials = ref([])
const exam = ref(null)
const comments = ref([])
const userProgress = ref(0)
const commentContent = ref('')
const materialProgressMap = ref({})

// 评论相关
const commentTab = ref('project')
const currentMaterialId = ref(null)
const mentionSearchVisible = ref(false)
const mentionUsers = ref([])
const mentionKeyword = ref('')
const replyTo = ref(null)
const replyParent = ref(null)
const likedComments = ref(new Set())
const commentInput = ref(null)

// 表情选择器
const emojiPickerVisible = ref(false)
const emojiList = [
  '😀', '😃', '😄', '😁', '😆', '😅', '🤣', '😂',
  '🙂', '😉', '😊', '😇', '🥰', '😍', '🤩', '😘',
  '😗', '😚', '😋', '😛', '😜', '🤪', '😝', '🤑',
  '🤗', '🤭', '🤫', '🤔', '🤐', '🤨', '😐', '😑',
  '😶', '😏', '😒', '🙄', '😬', '🤥', '😌', '😔',
  '😪', '🤤', '😴', '😷', '🤒', '🤕', '🤢', '🤮',
  '🤧', '🥵', '🥶', '🥴', '😵', '🤯', '🤠', '🥳',
  '😎', '🤓', '🧐', '😕', '😟', '🙁', '😮', '😯',
  '😲', '😳', '🥺', '😦', '😧', '😨', '😰', '😥',
  '😢', '😭', '😱', '😖', '😣', '😞', '😓', '😩',
  '😫', '🥱', '😤', '😡', '😠', '🤬', '😈', '👿',
  '👍', '👎', '👏', '🙌', '🤝', '🙏', '💪', '🤘',
  '❤️', '🧡', '💛', '💚', '💙', '💜', '🖤', '🤍',
  '💯', '💢', '💥', '💫', '💦', '💨', '🕳', '💣',
  '✅', '❌', '❓', '❗', '💚', '🔥', '⭐', '✨',
]

// 当前用户
const currentUserId = computed(() => userStore.userInfo?.user_id)
const isHrAdmin = computed(() => userStore.userInfo?.role === 1)

const enrolledCount = ref('--')
const isDeadlineSoon = computed(() => {
  if (!project.value?.deadline) return false
  const diff = dayjs(project.value.deadline).diff(dayjs(), 'day')
  return diff <= 3 && diff >= 0
})

const coverGradient = computed(() => {
  if (!project.value) return themeStore.themes[themeStore.currentTheme]?.gradient || 'var(--theme-gradient)'
  const gradients = [
    themeStore.themes[themeStore.currentTheme]?.gradient || 'var(--theme-gradient)',
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
    router.push(`/exam/${exam.value.exam_id}`)
  }
}

function goToExamHistory() {
  router.push('/exam-history')
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

    // Fetch full exam details if there's an exam
    if (exam.value?.exam_id) {
      try {
        const examRes = await getExamDetail(exam.value.exam_id)
        if (examRes.code === 0) {
          exam.value = examRes.data
        }
      } catch (error) {
        console.error('Failed to fetch exam detail:', error)
      }
    }
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

async function submitComment() {
  if (!commentContent.value.trim()) {
    ElMessage.warning('请输入评论内容')
    return
  }

  try {
    const data = {
      project_id: route.params.id,
      content: commentContent.value,
    }

    if (commentTab.value === 'material' && currentMaterialId.value) {
      data.material_id = currentMaterialId.value
    }

    if (replyTo.value) {
      data.parent_id = replyTo.value.comment_id
    }

    await createComment(data)
    ElMessage.success('评论发表成功')
    commentContent.value = ''
    replyTo.value = null
    replyParent.value = null
    mentionSearchVisible.value = false
    await fetchComments()
  } catch (error) {
    console.error('Failed to submit comment:', error)
    ElMessage.error('评论发表失败')
  }
}

async function fetchComments() {
  if (!route.params.id) return

  commentLoading.value = true
  try {
    const params = {
      project_id: route.params.id,
      page: 1,
      page_size: 50,
    }

    if (commentTab.value === 'material' && currentMaterialId.value) {
      params.material_id = currentMaterialId.value
    }

    const res = await getComments(params)
    if (res.code === 0) {
      comments.value = res.data.list || []

      // Restore liked state
      comments.value.forEach(c => {
        c.liked = likedComments.value.has(c.comment_id)
        if (c.replies) {
          c.replies.forEach(r => {
            r.liked = likedComments.value.has(r.comment_id)
          })
        }
      })
    }
  } catch (error) {
    console.error('Failed to fetch comments:', error)
  } finally {
    commentLoading.value = false
  }
}

async function handleDeleteComment(comment) {
  try {
    await ElMessageBox.confirm('确定要删除这条评论吗？', '提示', { type: 'warning' })
    await deleteComment(comment.comment_id)
    ElMessage.success('删除成功')
    await fetchComments()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete comment:', error)
      ElMessage.error('删除失败')
    }
  }
}

async function toggleLike(comment) {
  try {
    if (comment.liked) {
      await unlikeComment(comment.comment_id)
      comment.like_count = Math.max(0, (comment.like_count || 1) - 1)
      likedComments.value.delete(comment.comment_id)
    } else {
      await likeComment(comment.comment_id)
      comment.like_count = (comment.like_count || 0) + 1
      likedComments.value.add(comment.comment_id)
    }
    comment.liked = !comment.liked
  } catch (error) {
    console.error('Failed to toggle like:', error)
  }
}

function startReply(comment, parentComment = null) {
  replyTo.value = comment
  replyParent.value = parentComment
  commentInput.value?.focus()
}

function cancelReply() {
  replyTo.value = null
  replyParent.value = null
}

let mentionSearchTimer = null
function handleCommentInput(e) {
  const text = e.target.value
  const cursorPos = e.target.selectionStart

  // Find if user is typing @mention
  const textBeforeCursor = text.substring(0, cursorPos)
  const atIndex = textBeforeCursor.lastIndexOf('@')

  if (atIndex !== -1) {
    const textAfterAt = textBeforeCursor.substring(atIndex + 1)

    // Check if there's no space after @
    if (!textAfterAt.includes(' ') && textAfterAt.length <= 20) {
      mentionKeyword.value = textAfterAt
      searchMentionUsers(textAfterAt)
      return
    }
  }

  mentionSearchVisible.value = false
  mentionKeyword.value = ''
}

async function searchMentionUsers(keyword) {
  if (!keyword || keyword.length < 1) {
    mentionUsers.value = []
    mentionSearchVisible.value = false
    return
  }

  try {
    const res = await searchUsers(keyword)
    if (res.code === 0) {
      mentionUsers.value = res.data || []
      mentionSearchVisible.value = mentionUsers.value.length > 0
    }
  } catch (error) {
    console.error('Failed to search users:', error)
  }
}

function selectMention(user) {
  const text = commentContent.value
  const cursorPos = commentInput.value?.selectionStart || text.length
  const textBeforeCursor = text.substring(0, cursorPos)
  const atIndex = textBeforeCursor.lastIndexOf('@')

  // Replace @keyword with @username
  const beforeAt = text.substring(0, atIndex)
  const afterCursor = text.substring(cursorPos)
  commentContent.value = beforeAt + '@' + user.username + ' ' + afterCursor

  mentionSearchVisible.value = false
  mentionUsers.value = []

  // Focus back on textarea
  setTimeout(() => {
    const newPos = atIndex + user.username.length + 2
    commentInput.value?.setSelectionRange(newPos, newPos)
    commentInput.value?.focus()
  }, 0)
}

function toggleEmojiPicker() {
  emojiPickerVisible.value = !emojiPickerVisible.value
}

function insertEmoji(emoji) {
  const text = commentContent.value
  const cursorPos = commentInput.value?.selectionStart || text.length
  const before = text.substring(0, cursorPos)
  const after = text.substring(cursorPos)
  commentContent.value = before + emoji + after

  // Move cursor after emoji
  setTimeout(() => {
    const newPos = cursorPos + emoji.length
    commentInput.value?.setSelectionRange(newPos, newPos)
    commentInput.value?.focus()
  }, 0)

  emojiPickerVisible.value = false
}

// 点击外部关闭表情选择器
function handleClickOutside(e) {
  if (emojiPickerVisible.value && !e.target.closest('.emoji-btn') && !e.target.closest('.emoji-dropdown')) {
    emojiPickerVisible.value = false
  }
  if (mentionSearchVisible.value && !e.target.closest('.mention-dropdown') && !e.target.closest('textarea')) {
    mentionSearchVisible.value = false
  }
}

onMounted(async () => {
  await fetchProjectDetail()
  await fetchProgress()
  await fetchComments()
  console.log('[DEBUG] TrainingDetail mounted, progress:', materialProgressMap.value)
  // 注册点击外部关闭事件
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
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
      await fetchComments()
    }
  }
)

// Watch comment tab changes
watch(commentTab, () => {
  fetchComments()
})

// Extract material ID from route if in material view
watch(
  () => route.params.materialId,
  (materialId) => {
    currentMaterialId.value = materialId || null
    if (materialId) {
      commentTab.value = 'material'
    }
  },
  { immediate: true }
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
  color: var(--theme-primary);
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
  background: var(--theme-gradient);
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
  background: var(--theme-gradient);
  color: #fff;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.btn-outline {
  background: #fff;
  color: var(--theme-primary);
  border: 1px solid var(--theme-primary);
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
  border-color: var(--theme-primary);
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

.exam-tag.passed {
  background: #52c41a;
}

.exam-info {
  font-size: 13px;
  color: #666;
  margin-bottom: 15px;
}

.exam-info p {
  margin-bottom: 6px;
}

.exam-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.exam-btn {
  width: 100%;
}

.comment-section {
  margin-top: 20px;
}

.comment-input-wrap {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
}

.input-container {
  position: relative;
}

.comment-input-wrap textarea {
  width: 100%;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  padding: 12px;
  font-size: 14px;
  resize: none;
  height: 80px;
  font-family: inherit;
  box-sizing: border-box;
}

.comment-input-wrap textarea:focus {
  outline: none;
  border-color: var(--theme-primary);
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.action-left {
  display: flex;
  align-items: center;
  gap: 12px;
  position: relative;
}

.reply-hint {
  font-size: 13px;
  color: var(--theme-primary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.cancel-reply {
  cursor: pointer;
  font-size: 18px;
  color: #999;
}

.cancel-reply:hover {
  color: #666;
}

/* 表情选择器 */
.emoji-btn {
  cursor: pointer;
  font-size: 20px;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background 0.2s;
}

.emoji-btn:hover {
  background: #f5f7fa;
}

.emoji-dropdown {
  position: absolute;
  bottom: 100%;
  left: 0;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
  padding: 8px;
  z-index: 1000;
  margin-bottom: 8px;
}

.emoji-grid {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 4px;
}

.emoji-item {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  cursor: pointer;
  border-radius: 4px;
  transition: background 0.2s;
}

.emoji-item:hover {
  background: #f5f7fa;
}

/* @提及下拉 */
.mention-dropdown {
  position: absolute;
  top: -8px;
  left: 0;
  right: 0;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  max-height: 200px;
  overflow-y: auto;
  z-index: 100;
}

.mention-item {
  padding: 8px 12px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
}

.mention-item:hover {
  background: #f5f7fa;
}

.mention-name {
  font-size: 14px;
  color: #333;
}

.mention-username {
  font-size: 12px;
  color: #999;
}

.mention-empty {
  padding: 12px;
  text-align: center;
  color: #999;
  font-size: 13px;
}

/* 评论列表 */
.comment-list {
  margin-top: 20px;
}

.comment-item {
  display: flex;
  gap: 12px;
  padding: 15px 0;
  border-bottom: 1px solid #f5f7fa;
}

.comment-item:last-child {
  border-bottom: none;
}

.comment-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--theme-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  flex-shrink: 0;
}

.comment-avatar.small {
  width: 28px;
  height: 28px;
  font-size: 12px;
}

.comment-content {
  flex: 1;
}

.comment-user {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.comment-time {
  font-weight: normal;
  color: #999;
  font-size: 12px;
}

.comment-text {
  font-size: 14px;
  color: #666;
  line-height: 1.6;
}

.comment-actions {
  display: flex;
  gap: 16px;
  margin-top: 8px;
}

.action-btn {
  font-size: 13px;
  color: #999;
  cursor: pointer;
}

.action-btn:hover {
  color: var(--theme-primary);
}

.like-btn.liked {
  color: #ff4757;
}

.delete-btn:hover {
  color: #ff4757;
}

/* 回复列表 */
.reply-list {
  margin-top: 12px;
  padding-left: 12px;
  border-left: 2px solid #f5f7fa;
}

.reply-item {
  padding: 12px 0;
  border-bottom: 1px solid #f5f7fa;
}

.reply-item:last-child {
  border-bottom: none;
}

.sidebar .progress-card {
  background: var(--theme-gradient);
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