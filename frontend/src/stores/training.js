import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  getProjectList,
  getProjectDetail,
  createProject,
  updateProject,
  publishProject,
  unpublishProject,
  deleteProject,
  getProgress,
  updateProgress,
  getProgressReport,
  getProgressStats,
} from '@/api/training'

export const useTrainingStore = defineStore('training', () => {
  const projectList = ref([])
  const currentProject = ref(null)
  const materials = ref([])
  const progress = ref({})
  const pagination = ref({ page: 1, page_size: 20, total: 0 })
  const loading = ref(false)

  async function fetchProjectList(params = {}) {
    loading.value = true
    try {
      const res = await getProjectList(params)
      if (res.code === 0) {
        projectList.value = res.data.list
        pagination.value = res.data.pagination
      }
    } finally {
      loading.value = false
    }
  }

  async function fetchProjectDetail(projectId) {
    loading.value = true
    try {
      const res = await getProjectDetail(projectId)
      if (res.code === 0) {
        currentProject.value = res.data
        materials.value = res.data.materials || []
        return res.data
      }
    } finally {
      loading.value = false
    }
  }

  async function fetchProgress(projectId) {
    try {
      console.log('[DEBUG Store] fetchProgress called with projectId:', projectId)
      const res = await getProgress(projectId)
      console.log('[DEBUG Store] getProgress response:', res)
      if (res.code === 0) {
        // Build progress map
        const progressMap = {}
        ;(res.data.materials || []).forEach((m) => {
          progressMap[m.material_id] = m
        })
        progress.value = progressMap
        console.log('[DEBUG Store] progress.value after fetch:', JSON.parse(JSON.stringify(progress.value)))
        console.log('[DEBUG Store] returning res.data:', res.data)
        return res.data
      }
    } catch (error) {
      console.error('Failed to fetch progress:', error)
    }
  }

  async function saveVideoProgress(materialId, playPosition, maxPosition, totalWatchedSeconds = 0) {
    try {
      console.log('[DEBUG Store] saveVideoProgress called:', { materialId, playPosition, maxPosition, totalWatchedSeconds })
      const res = await updateProgress({
        material_id: materialId,
        play_position: playPosition,
        max_position: maxPosition,
        total_watched_seconds: totalWatchedSeconds,
      })
      console.log('[DEBUG Store] updateProgress response:', res)

      // Update local state
      if (!progress.value[materialId]) {
        progress.value[materialId] = {
          watched_seconds: 0,
          max_position: 0,
          total_watched_seconds: 0,
          is_completed: false,
        }
      }
      progress.value[materialId].watched_seconds = playPosition
      progress.value[materialId].max_position = maxPosition
      progress.value[materialId].total_watched_seconds = (progress.value[materialId].total_watched_seconds || 0) + totalWatchedSeconds
      console.log('[DEBUG Store] progress.value updated:', progress.value)
    } catch (error) {
      console.error('Failed to save progress:', error)
    }
  }

  async function fetchProgressReport(projectId, params = {}) {
    try {
      const res = await getProgressReport(projectId, params)
      if (res.code === 0) {
        return res.data
      }
    } catch (error) {
      console.error('Failed to fetch progress report:', error)
    }
  }

  async function fetchProgressStats(projectId) {
    try {
      const res = await getProgressStats(projectId)
      if (res.code === 0) {
        return res.data
      }
    } catch (error) {
      console.error('Failed to fetch progress stats:', error)
    }
  }

  async function create(projectData) {
    loading.value = true
    try {
      const res = await createProject(projectData)
      return res
    } finally {
      loading.value = false
    }
  }

  async function update(projectId, projectData) {
    loading.value = true
    try {
      const res = await updateProject(projectId, projectData)
      return res
    } finally {
      loading.value = false
    }
  }

  async function publish(projectId, sendNotification = false) {
    loading.value = true
    try {
      const res = await publishProject(projectId, sendNotification)
      return res
    } finally {
      loading.value = false
    }
  }

  async function unpublish(projectId) {
    loading.value = true
    try {
      const res = await unpublishProject(projectId)
      return res
    } finally {
      loading.value = false
    }
  }

  async function remove(projectId) {
    loading.value = true
    try {
      const res = await deleteProject(projectId)
      return res
    } finally {
      loading.value = false
    }
  }

  return {
    projectList,
    currentProject,
    materials,
    progress,
    pagination,
    loading,
    fetchProjectList,
    fetchProjectDetail,
    fetchProgress,
    saveVideoProgress,
    fetchProgressReport,
    fetchProgressStats,
    create,
    update,
    publish,
    unpublish,
    remove,
  }
})