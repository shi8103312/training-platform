import request from '@/utils/request'

export function sendNotification(data) {
  return request({
    url: '/v1/notification/send',
    method: 'post',
    data,
  })
}

export function getNotificationHistory(params) {
  return request({
    url: '/v1/notification/history',
    method: 'get',
    params,
  })
}

export function getMyNotifications(params) {
  return request({
    url: '/v1/notification/list',
    method: 'get',
    params,
  })
}

export function deleteNotification(id) {
  return request({
    url: `/v1/notification/${id}`,
    method: 'delete',
  })
}

export function markNotificationRead(id) {
  return request({
    url: `/v1/notification/${id}/read`,
    method: 'put',
  })
}