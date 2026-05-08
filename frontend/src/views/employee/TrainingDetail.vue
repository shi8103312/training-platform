<template>
  <div class="training-detail" v-if="project">
    <el-button class="back-btn" :icon="ArrowLeft" @click="$router.back()">
      返回
    </el-button>

    <el-card class="project-header">
      <div class="header-content">
        <div class="cover">
          <img v-if="project.cover_image" :src="project.cover_image" />
          <div v-else class="cover-placeholder">
            <el-icon><Reading /></el-icon>
          </div>
        </div>

        <div class="info">
          <h1>{{ project.title }}</h1>

          <div class="meta">
            <el-tag :type="project.is_required ? 'danger' : 'info'">
              {{ project.is_required ? '必修' : '选修' }}
            </el-tag>
            <el-tag :type="getStatusType(project.status)">
              {{ project.status_text }}
            </el-tag>
            <span class="deadline">
              <el-icon><Clock /></el-icon>
              截止: {{ formatDate(project.deadline) }}
            </span>
          </div>

          <p class="description">{{ project.description || '暂无描述' }}</p>

          <div class="overall-progress">
            <span>学习进度</span>
            <el-progress :percentage="overallProgress" :stroke-width="10" style="width: 200px" />
            <span>{{ overallProgress }}%</span>
          </div>
        </div>
      </div>
    </el-card>

    <el-card class="materials-card">
      <template #header>
        <div class="card-header">
          <span>培训材料</span>
          <span class="count">{{ materials.length }} 个</span>
        </div>
      </template>

      <el-empty v-if="materials.length === 0" description="暂无材料" />

      <div v-else class="materials-list">
        <div
          v-for="(material, index) in materials"
          :key="material.material_id"
          class="material-item"
          @click="handleMaterialClick(material)"
        >
          <div class="material-index">{{ index + 1 }}</div>

          <div class="material-icon">
            <el-icon v-if="material.material_type === 1"><VideoPlay /></el-icon>
            <el-icon v-else><Document /></el-icon>
          </div>

          <div class="material-info">
            <h4>{{ material.title }}</h4>
            <div class="material-meta">
              <span>{{ material.material_type === 1 ? '视频' : '文档' }}</span>
              <span v-if="material.duration">{{ formatDuration(material.duration) }}</span>
            </div>
          </div>

          <div class="material-status">
            <el-tag v-if="isCompleted(material.material_id)" type="success" size="small">
              已完成
            </el-tag>
            <el-tag v-else-if="getProgress(material.material_id) > 0" type="warning" size="small">
              {{ getProgress(material.material_id) }}%
            </el-tag>
            <el-tag v-else size="small">未开始</el-tag>
          </div>

          <el-icon class="arrow"><ArrowRight /></el-icon>
        </div>
      </div>
    </el-card>

    <el-card v-if="project.exam" class="exam-card">
      <template #header>
        <div class="card-header">
          <span>关联考试</span>
        </div>
      </template>

      <div class="exam-info" @click="handleExamClick(project.exam)">
        <div class="exam-icon">
          <el-icon><Memo /></el-icon>
        </div>
        <div class="exam-details">
          <h4>{{ project.exam.title }}</h4>
          <p>点击开始考试</p>
        </div>
        <el-icon class="arrow"><ArrowRight /></el-icon>
      </div>
    </el-card>
  </div>

  <el-skeleton v-else :rows="10" animated />
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTrainingStore } from '@/stores/training'
import {
  ArrowLeft,
  ArrowRight,
  Reading,
  Clock,
  VideoPlay,
  Document,
  Memo,
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()
const trainingStore = useTrainingStore()

const project = ref(null)
const materials = ref([])
const progressMap = ref({})

function getStatusType(status) {
  const types = { 0: 'info', 1: 'success', 2: 'warning', 3: 'info' }
  return types[status] || 'info'
}

function formatDate(date) {
  return dayjs(date).format('YYYY-MM-DD HH:mm')
}

function formatDuration(seconds) {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

function getProgress(materialId) {
  const p = progressMap.value[materialId]
  return p?.progress || 0
}

function isCompleted(materialId) {
  return progressMap.value[materialId]?.is_completed
}

const overallProgress = computed(() => {
  if (materials.value.length === 0) return 0
  const completed = materials.value.filter((m) =>
    isCompleted(m.material_id)
  ).length
  return Math.round((completed / materials.value.length) * 100)
})

function handleMaterialClick(material) {
  router.push(`/training/${project.value.project_id}/material/${material.material_id}`)
}

function handleExamClick(exam) {
  router.push(`/exam/${exam.exam_id}`)
}

onMounted(async () => {
  const projectId = route.params.id

  await trainingStore.fetchProjectDetail(projectId)
  project.value = trainingStore.currentProject
  materials.value = trainingStore.materials

  const progressData = await trainingStore.fetchProgress(projectId)
  if (progressData?.materials) {
    progressData.materials.forEach((m) => {
      progressMap.value[m.material_id] = m
    })
  }
})
</script>

<style scoped>
.training-detail {
  max-width: 900px;
}

.back-btn {
  margin-bottom: 20px;
}

.project-header {
  margin-bottom: 20px;
}

.header-content {
  display: flex;
  gap: 24px;
}

.cover {
  width: 300px;
  height: 180px;
  border-radius: 8px;
  overflow: hidden;
  flex-shrink: 0;
  background: #f5f7fa;
}

.cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #c0c4cc;
  font-size: 48px;
}

.info {
  flex: 1;
}

.info h1 {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 16px;
}

.meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.deadline {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  color: #e6a23c;
}

.description {
  font-size: 14px;
  color: #606266;
  margin: 0 0 16px;
  line-height: 1.6;
}

.overall-progress {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  color: #606266;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.count {
  font-size: 14px;
  color: #909399;
}

.materials-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.material-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.material-item:hover {
  border-color: #409eff;
  background: #f5f7fa;
}

.material-index {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #409eff;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
}

.material-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: #ecf5ff;
  color: #409eff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.material-info {
  flex: 1;
}

.material-info h4 {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin: 0 0 4px;
}

.material-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #909399;
}

.arrow {
  color: #c0c4cc;
  font-size: 16px;
}

.exam-card {
  margin-top: 20px;
}

.exam-info {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.exam-info:hover {
  border-color: #409eff;
  background: #f5f7fa;
}

.exam-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  background: #fdf6ec;
  color: #e6a23c;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.exam-details {
  flex: 1;
}

.exam-details h4 {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin: 0 0 4px;
}

.exam-details p {
  font-size: 12px;
  color: #909399;
  margin: 0;
}
</style>