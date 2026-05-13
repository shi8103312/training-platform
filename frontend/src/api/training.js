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

export function uploadMaterialWithProgress(formData, onProgress) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) {
        const percent = Math.round((e.loaded / e.total) * 100)
        const loadedMB = (e.loaded / (1024 * 1024)).toFixed(1)
        const totalMB = (e.total / (1024 * 1024)).toFixed(1)
        onProgress(percent, `${loadedMB}MB / ${totalMB}MB`)
      }
    }

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const res = JSON.parse(xhr.responseText)
          resolve(res)
        } catch {
          reject(new Error('Invalid JSON response'))
        }
      } else {
        reject(new Error(`Upload failed with status ${xhr.status}`))
      }
    }

    xhr.onerror = () => {
      reject(new Error('Network error'))
    }

    xhr.open('POST', `/api/v1/training/material/upload`)

    // Get token from localStorage
    const token = localStorage.getItem('token')
    if (token) {
      xhr.setRequestHeader('Authorization', `Bearer ${token}`)
    }

    xhr.send(formData)
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