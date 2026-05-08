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
      <div v-if="material?.material_type === 1" class="video-container">
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
        </div>

        <div v-if="showResumePrompt" class="resume-prompt">
          <p>是否从 {{ formatTime(lastPosition) }} 位置继续播放？</p>
          <el-button type="primary" size="small" @click="resumePlay">继续</el-button>
          <el-button size="small" @click="startPlay">从头开始</el-button>
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
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useTrainingStore } from '@/stores/training'
import { getPlayToken } from '@/api/training'
import {
  ArrowLeft,
  VideoPlay,
  VideoPause,
  CircleCheck,
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const trainingStore = useTrainingStore()

const videoRef = ref(null)
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

function togglePlay() {
  if (!videoRef.value) return

  if (isPlaying.value) {
    videoRef.value.pause()
  } else {
    videoRef.value.play()
  }
  isPlaying.value = !isPlaying.value
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

  // Prevent seeking beyond max position (anti-cheat)
  if (currentTime.value > maxAllowedPosition.value + 5) {
    videoRef.value.currentTime = maxAllowedPosition.value
  }

  // Save progress every 10 seconds
  if (progressTimer.value) clearTimeout(progressTimer.value)
  progressTimer.value = setTimeout(() => {
    saveProgress()
  }, 10000)
}

function handleEnded() {
  isPlaying.value = false
  saveProgress()
}

function handleLoadedMetadata() {
  if (!videoRef.value) return

  duration.value = videoRef.value.duration

  // Check for resume prompt
  const progress = trainingStore.progress[route.params.materialId]
  if (progress && progress.max_position > 0) {
    lastPosition.value = progress.max_position
    showResumePrompt.value = true
    isCompleted.value = progress.is_completed
  }
}

function resumePlay() {
  if (!videoRef.value) return

  videoRef.value.currentTime = lastPosition.value
  maxAllowedPosition.value = lastPosition.value
  showResumePrompt.value = false
  videoRef.value.play()
  isPlaying.value = true
}

function startPlay() {
  if (!videoRef.value) return

  videoRef.value.currentTime = 0
  maxAllowedPosition.value = 0
  showResumePrompt.value = false
  videoRef.value.play()
  isPlaying.value = true
}

async function saveProgress() {
  if (!material.value) return

  const position = Math.floor(videoRef.value?.currentTime || 0)
  if (position > maxAllowedPosition.value) {
    maxAllowedPosition.value = position
  }

  await trainingStore.saveVideoProgress(
    route.params.materialId,
    position,
    maxAllowedPosition.value
  )

  // Check completion (95%)
  if (duration.value > 0 && maxAllowedPosition.value >= duration.value * 0.95) {
    isCompleted.value = true
  }
}

async function fetchPlayToken() {
  const materialId = route.params.materialId

  try {
    const res = await getPlayToken(materialId)
    if (res.code === 0) {
      videoSrc.value = res.data.play_url
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
  }

  await trainingStore.fetchProgress(projectId)
})

onUnmounted(() => {
  if (progressTimer.value) clearTimeout(progressTimer.value)
  saveProgress()
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