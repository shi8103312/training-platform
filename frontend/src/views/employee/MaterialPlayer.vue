<template>
  <div class="material-player">
    <el-button class="back-btn" :icon="ArrowLeft" @click="$router.back()">
      返回
    </el-button>

    <el-card class="player-card">
      <div class="player-header">
        <h2>{{ material?.title }}</h2>
        <el-tag v-if="material" :type="material.material_type === 1 ? 'primary' : 'success'">
          {{ material.material_type === 1 ? '视频' : '文档' }}
        </el-tag>
      </div>

      <!-- Video Player -->
      <div v-if="material?.material_type === 1 && videoSrc" ref="videoContainerRef" class="video-container">
        <video
          ref="videoRef"
          :src="videoSrc"
          :poster="material.thumbnail"
          @timeupdate="handleTimeUpdate"
          @ended="handleEnded"
          @loadedmetadata="handleLoadedMetadata"
        />

        <div class="video-controls">
          <div class="play-btn" @click="togglePlay">
            <el-icon v-if="isPlaying"><VideoPause /></el-icon>
            <el-icon v-else><VideoPlay /></el-icon>
          </div>

          <div class="progress-bar" @click="handleProgressClick">
            <div class="progress-bg">
              <div class="progress-watched" :style="{ width: watchedPercent + '%' }"></div>
              <div class="progress-allow" :style="{ width: allowedPercent + '%' }"></div>
            </div>
            <span class="time-display">
              {{ formatTime(currentTime) }} / {{ formatTime(duration) }}
            </span>
          </div>

          <div class="fullscreen-btn" @click="toggleFullscreen">
            <el-icon><FullScreen /></el-icon>
          </div>
        </div>

        <div v-if="showResumePrompt" class="resume-prompt">
          <p v-if="isCompleted">已学习完毕，可以重新观看</p>
          <p v-else>学习进度：{{ formatTime(lastPosition) }}，点击继续观看</p>
          <el-button type="primary" size="small" @click="resumePlay">继续播放</el-button>
          <el-button v-if="isCompleted" size="small" @click="startPlay">重新开始</el-button>
        </div>
      </div>

      <!-- Document Viewer -->
      <div v-else-if="material?.material_type === 2" class="document-container">
        <div class="watermark-layer">
          <div v-for="i in 20" :key="i" class="watermark-item">
            {{ watermarkText }}
          </div>
        </div>
        <iframe :src="documentSrc" class="document-frame" />
        <div class="document-actions">
          <el-button
            v-if="!isCompleted"
            type="primary"
            @click="markDocumentAsRead"
          >
            我已阅读
          </el-button>
          <el-tag v-else type="success" size="large">
            <el-icon><CircleCheck /></el-icon>
            已完成
          </el-tag>
        </div>
      </div>

      <div v-else class="unsupported">
        <p>暂不支持此格式的预览</p>
      </div>
    </el-card>

    <div v-if="isCompleted" class="completion-tip">
      <el-icon><CircleCheck /></el-icon>
      <span>恭喜！您已完成此材料的学习</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter, onBeforeRouteLeave } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useTrainingStore } from '@/stores/training'
import { getPlayToken, updateMaterialDuration } from '@/api/training'
import {
  ArrowLeft,
  VideoPlay,
  VideoPause,
  CircleCheck,
  FullScreen,
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const trainingStore = useTrainingStore()

const videoRef = ref(null)
const videoContainerRef = ref(null)
const material = ref(null)
const videoSrc = ref('')
const documentSrc = ref('')
const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const maxAllowedPosition = ref(0)
const lastPosition = ref(0)
const showResumePrompt = ref(false)
const isCompleted = ref(false)
const progressTimer = ref(null)

// Session watch tracking
const sessionStartTime = ref(0)  // Timestamp when current session started
const sessionStartPosition = ref(0)  // Position when current session started
const totalWatchedSeconds = ref(0)    // Total watched seconds in current session

// Debug: watch isPlaying changes
watch(isPlaying, (newVal, oldVal) => {
  console.log('[DEBUG] isPlaying changed:', oldVal, '->', newVal)
})

const watchedPercent = computed(() => {
  if (duration.value === 0) return 0
  return (currentTime.value / duration.value) * 100
})

const allowedPercent = computed(() => {
  if (duration.value === 0) return 0
  return (maxAllowedPosition.value / duration.value) * 100
})

const watermarkText = computed(() => {
  const user = userStore.userInfo
  const date = dayjs().format('YYYY-MM-DD')
  return `${user?.real_name || ''} (${user?.user_id || ''}) ${date}`
})

function formatTime(seconds) {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

async function togglePlay() {
  console.log('[DEBUG] togglePlay called, isPlaying:', isPlaying.value)
  if (!videoRef.value) return

  if (isPlaying.value) {
    console.log('[DEBUG] togglePlay: pausing')
    videoRef.value.pause()
    // Save progress when paused
    saveProgress()
    router.back()
  } else {
    // If resume prompt is shown, call resumePlay
    if (showResumePrompt.value) {
      console.log('[DEBUG] togglePlay: resuming from prompt')
      resumePlay()
      return
    } else {
      console.log('[DEBUG] togglePlay: starting fresh')
      videoRef.value.play()
    }
    isPlaying.value = !isPlaying.value
  }
}

function toggleFullscreen() {
  if (!videoContainerRef.value) return

  if (document.fullscreenElement) {
    document.exitFullscreen()
  } else {
    videoContainerRef.value.requestFullscreen()
  }
}

function handleProgressClick(e) {
  if (!videoRef.value) return

  const rect = e.currentTarget.getBoundingClientRect()
  const clickPosition = (e.clientX - rect.left) / rect.width
  const targetTime = clickPosition * duration.value

  // Can only seek to watched area
  if (targetTime <= maxAllowedPosition.value) {
    videoRef.value.currentTime = targetTime
  }
}

function handleTimeUpdate() {
  if (!videoRef.value) return

  currentTime.value = videoRef.value.currentTime

  // Track session watch time using timestamps
  if (isPlaying.value) {
    const now = Date.now()
    if (sessionStartTime.value > 0) {
      const elapsedSeconds = (now - sessionStartTime.value) / 1000
      // Only count forward progress (user watching forward, not rewinding)
      if (currentTime.value > sessionStartPosition.value) {
        totalWatchedSeconds.value += elapsedSeconds
      }
    }
    sessionStartTime.value = now
    sessionStartPosition.value = currentTime.value
  }

  // Anti-cheat: if not completed, only allow watching current position + small buffer
  // User must watch continuously without skipping
  if (!isCompleted.value && maxAllowedPosition.value >= 0) {
    const buffer = 5 // Allow 5 seconds buffer
    if (currentTime.value > maxAllowedPosition.value + buffer) {
      console.log('[DEBUG] Anti-cheat: skipping prevented, resetting to:', maxAllowedPosition.value)
      videoRef.value.currentTime = maxAllowedPosition.value
      currentTime.value = maxAllowedPosition.value
    }
    // Update maxAllowed to track progress (only forward)
    if (currentTime.value > maxAllowedPosition.value) {
      maxAllowedPosition.value = currentTime.value
    }
  }

  // Save progress periodically
  if (progressTimer.value) clearTimeout(progressTimer.value)
  progressTimer.value = setTimeout(() => {
    saveProgress()
  }, 10000)
}

function handleEnded() {
  console.log('[DEBUG] handleEnded: video ended')
  isPlaying.value = false
  // Video completed - mark as done and save
  isCompleted.value = true
  saveProgress()
}

function handleLoadedMetadata() {
  if (!videoRef.value) return

  duration.value = videoRef.value.duration
  console.log('[DEBUG] Metadata loaded, duration:', duration.value)

  // Update material duration in backend if it's 0
  if (material.value && material.value.duration === 0 && duration.value > 0) {
    console.log('[DEBUG] Updating material duration to backend:', Math.floor(duration.value))
    updateMaterialDuration(route.params.materialId, Math.floor(duration.value)).catch(err => {
      console.error('Failed to update material duration:', err)
    })
  }

  // Check if already completed
  const progress = trainingStore.progress[route.params.materialId]
  console.log('[DEBUG] Progress data from store:', progress)
  if (progress && progress.is_completed) {
    // Already completed - allow re-watch from any position
    isCompleted.value = true
    lastPosition.value = progress.max_position || 0
    showResumePrompt.value = true
    console.log('[DEBUG] Video already completed, allowing re-watch')
  } else if (progress && progress.max_position > 0) {
    // Not completed yet - must continue from last position (cannot restart)
    isCompleted.value = false
    lastPosition.value = progress.max_position || 0
    showResumePrompt.value = true
    console.log('[DEBUG] Video not completed, must continue from:', lastPosition.value)
  } else {
    // No progress at all - fresh start
    isCompleted.value = false
    lastPosition.value = 0
    showResumePrompt.value = true
    console.log('[DEBUG] Fresh start')
  }
}

function resumePlay() {
  if (!videoRef.value) return

  // Continue from last position
  console.log('[DEBUG] resumePlay: continuing from:', lastPosition.value)
  videoRef.value.currentTime = lastPosition.value
  maxAllowedPosition.value = lastPosition.value  // Must watch continuously from here
  sessionStartTime.value = Date.now()  // Track session start time
  sessionStartPosition.value = lastPosition.value  // Track session start position
  totalWatchedSeconds.value = 0  // Reset session watch time
  showResumePrompt.value = false
  videoRef.value.play()
  isPlaying.value = true
  currentTime.value = videoRef.value.currentTime
}

function startPlay() {
  if (!videoRef.value) return

  if (isCompleted.value) {
    // Completed video - can start from beginning for re-watch
    console.log('[DEBUG] startPlay: re-watching from beginning')
    videoRef.value.currentTime = 0
    maxAllowedPosition.value = 0
    sessionStartTime.value = Date.now()
    sessionStartPosition.value = 0
    totalWatchedSeconds.value = 0
  } else {
    // Not completed - must continue from last position
    console.log('[DEBUG] startPlay: not completed, resuming from:', lastPosition.value)
    videoRef.value.currentTime = lastPosition.value
    maxAllowedPosition.value = lastPosition.value
    sessionStartTime.value = Date.now()
    sessionStartPosition.value = lastPosition.value
    totalWatchedSeconds.value = 0
  }
  showResumePrompt.value = false
  videoRef.value.play()
  isPlaying.value = true
  currentTime.value = videoRef.value.currentTime
}

async function saveProgress() {
  if (!material.value || material.value.material_type !== 1) return
  if (!videoRef.value) return

  const videoEl = videoRef.value
  const position = Math.floor(videoEl.currentTime || 0)
  // Use maxAllowedPosition which tracks the furthest watched position
  const maxPos = Math.floor(maxAllowedPosition.value || 0)

  console.log('[DEBUG] saveProgress: position:', position, 'max:', maxPos, 'totalWatched:', Math.floor(totalWatchedSeconds.value), 'isCompleted:', isCompleted.value)
  try {
    await trainingStore.saveVideoProgress(
      route.params.materialId,
      position,
      maxPos,
      Math.floor(totalWatchedSeconds.value)
    )
  } catch (err) {
    console.error('[DEBUG] saveProgress: error:', err)
  }
}

async function markDocumentAsRead() {
  // For documents, mark as completed with a large position value
  await trainingStore.saveVideoProgress(
    route.params.materialId,
    600,
    600
  )
  isCompleted.value = true
  ElMessage.success('已标记为已完成')
}

async function fetchPlayToken() {
  const materialId = route.params.materialId

  try {
    const res = await getPlayToken(materialId)
    if (res.code === 0) {
      // Construct full URL for video playback - use window.location.origin which goes through vite proxy
      videoSrc.value = window.location.origin + '/uploads/' + res.data.play_url
      // TODO: Use token for authenticated playback
    }
  } catch (error) {
    console.error('Failed to get play token:', error)
  }
}

onMounted(async () => {
  const projectId = route.params.id
  const materialId = route.params.materialId

  await trainingStore.fetchProjectDetail(projectId)
  material.value = trainingStore.materials.find((m) => m.material_id === materialId)

  if (material.value?.material_type === 1) {
    await fetchPlayToken()
  } else if (material.value?.material_type === 2) {
    // For documents, construct URL directly from storage path
    const baseUrl = window.location.origin
    documentSrc.value = baseUrl + '/uploads/' + material.value.storage_path
  }

  await trainingStore.fetchProgress(projectId)
})

onUnmounted(() => {
  console.log('[DEBUG] onUnmounted called')
  if (progressTimer.value) clearTimeout(progressTimer.value)
  // Note: saveProgress is already called in togglePlay when user pauses
})

// Save progress when leaving the page
onBeforeRouteLeave(async () => {
  if (isPlaying.value) {
    videoRef.value?.pause()
    await saveProgress()
  }
})
</script>

<style scoped>
.material-player {
  max-width: 1000px;
}

.back-btn {
  margin-bottom: 20px;
}

.player-card {
  overflow: hidden;
}

.player-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.player-header h2 {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
}

.video-container {
  position: relative;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
}

.video-container:fullscreen {
  border-radius: 0;
}

.video-container:fullscreen video {
  width: 100vw;
  height: 100vh;
}

.video-container:fullscreen .video-controls {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16px 24px;
}

video {
  width: 100%;
  display: block;
}

.video-controls {
  display: flex;
  align-items: center;
  padding: 16px;
  background: rgba(0, 0, 0, 0.8);
  color: #fff;
}

.play-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 20px;
}

.play-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.fullscreen-btn {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 20px;
  margin-left: 16px;
}

.fullscreen-btn:hover {
  opacity: 0.8;
}

.progress-bar {
  flex: 1;
  margin-left: 16px;
  cursor: pointer;
}

.progress-bg {
  height: 6px;
  background: #444;
  border-radius: 3px;
  position: relative;
}

.progress-watched {
  position: absolute;
  height: 100%;
  background: #666;
  border-radius: 3px;
}

.progress-allow {
  position: absolute;
  height: 100%;
  background: #1a73e8;
  border-radius: 3px;
}

.time-display {
  display: block;
  margin-top: 8px;
  font-size: 12px;
  color: #ccc;
}

.resume-prompt {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: rgba(0, 0, 0, 0.9);
  padding: 24px 32px;
  border-radius: 8px;
  text-align: center;
  color: #fff;
  z-index: 10;
}

.resume-prompt p {
  margin: 0 0 16px;
}

.resume-prompt .el-button {
  margin: 0 8px;
}

.document-container {
  position: relative;
  height: 600px;
  background: #f5f5f5;
  border-radius: 8px;
  overflow: hidden;
}

.watermark-layer {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  z-index: 1;
}

.watermark-item {
  position: absolute;
  font-size: 12px;
  font-family: 'SimSun', serif;
  color: rgba(0, 0, 0, 0.1);
  transform: rotate(-30deg);
  white-space: nowrap;
}

.document-frame {
  width: 100%;
  height: 100%;
  border: none;
}

.document-actions {
  position: absolute;
  bottom: 20px;
  right: 20px;
  z-index: 10;
}

.completion-tip {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 20px;
  padding: 16px;
  background: #f0f9eb;
  border-radius: 8px;
  color: #67c23a;
  font-size: 14px;
}
</style>