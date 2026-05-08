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
      const res = await getProgress(projectId)
      if (res.code === 0) {
        // Build progress map
        const progressMap = {}
        ;(res.data.materials || []).forEach((m) => {
          progressMap[m.material_id] = m
        })
        progress.value = progressMap
        return res.data
      }
    } catch (error) {
      console.error('Failed to fetch progress:', error)
    }
  }

  async function saveVideoProgress(materialId, playPosition, maxPosition) {
    try {
      await updateProgress({
        material_id: materialId,
        play_position: playPosition,
        max_position: maxPosition,
      })

      // Update local state
      if (!progress.value[materialId]) {
        progress.value[materialId] = {
          watched_seconds: 0,
          max_position: 0,
          is_completed: false,
        }
      }
      progress.value[materialId].watched_seconds = playPosition
      progress.value[materialId].max_position = maxPosition
    } catch (error) {
      console.error('Failed to save progress:', error)
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
    create,
    update,
    publish,
    unpublish,
    remove,
  }
})