import request from '@/utils/request'

export function getUserList(params) {
  return request({
    url: '/v1/user/list',
    method: 'get',
    params,
  })
}

export function createUser(data) {
  return request({
    url: '/v1/user',
    method: 'post',
    data,
  })
}

export function updateUser(userId, data) {
  return request({
    url: `/v1/user/${userId}`,
    method: 'put',
    data,
  })
}

export function deleteUser(userId) {
  return request({
    url: `/v1/user/${userId}`,
    method: 'delete',
  })
}
