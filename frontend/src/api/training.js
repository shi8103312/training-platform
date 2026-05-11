import request from '@/utils/request'

export function getProjectList(params) {
  return request({
    url: '/v1/training/project/list',
    method: 'get',
    params,
  })
}

export function getProjectDetail(projectId) {
  return request({
    url: `/v1/training/project/${projectId}`,
    method: 'get',
  })
}

export function createProject(data) {
  return request({
    url: '/v1/training/project',
    method: 'post',
    data,
  })
}

export function updateProject(projectId, data) {
  return request({
    url: `/v1/training/project/${projectId}`,
    method: 'put',
    data,
  })
}

export function publishProject(projectId, sendNotification = false) {
  return request({
    url: `/v1/training/project/${projectId}/publish`,
    method: 'post',
    data: { send_notification: sendNotification },
  })
}

export function unpublishProject(projectId) {
  return request({
    url: `/v1/training/project/${projectId}/unpublish`,
    method: 'post',
  })
}

export function deleteProject(projectId) {
  return request({
    url: `/v1/training/project/${projectId}`,
    method: 'delete',
  })
}

export function uploadMaterial(formData) {
  return request({
    url: '/v1/training/material/upload',
    method: 'post',
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    data: formData,
  })
}

export function getPlayToken(materialId) {
  return request({
    url: `/v1/training/material/${materialId}/play-token`,
    method: 'get',
  })
}

export function updateMaterialDuration(materialId, duration) {
  return request({
    url: `/v1/training/material/${materialId}/duration`,
    method: 'put',
    params: { duration },
  })
}

export function deleteMaterial(materialId) {
  return request({
    url: `/v1/training/material/${materialId}`,
    method: 'delete',
  })
}

export function getProgress(projectId) {
  return request({
    url: `/v1/training/progress/${projectId}`,
    method: 'get',
  })
}

export function updateProgress(data) {
  console.log('[DEBUG API] updateProgress called with:', data)
  return request({
    url: '/v1/training/progress/update',
    method: 'post',
    data,
  })
}

export function getProgressReport(projectId, params) {
  return request({
    url: `/v1/training/progress/hr/${projectId}/export`,
    method: 'get',
    params,
  })
}

export function getProgressStats(projectId) {
  return request({
    url: `/v1/training/progress/hr/stats/${projectId}`,
    method: 'get',
  })
}