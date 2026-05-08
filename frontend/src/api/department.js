import request from '@/utils/request'

export function getDepartmentTree() {
  return request({
    url: '/v1/department/tree',
    method: 'get',
  })
}

export function getDepartmentList() {
  return request({
    url: '/v1/department/list',
    method: 'get',
  })
}

export function createDepartment(data) {
  return request({
    url: '/v1/department',
    method: 'post',
    data,
  })
}

export function updateDepartment(deptId, data) {
  return request({
    url: `/v1/department/${deptId}`,
    method: 'put',
    data,
  })
}

export function deleteDepartment(deptId) {
  return request({
    url: `/v1/department/${deptId}`,
    method: 'delete',
  })
}

export function importDepartments(file, mode = 'simulate') {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('mode', mode)

  return request({
    url: '/v1/department/import',
    method: 'post',
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    data: formData,
  })
}