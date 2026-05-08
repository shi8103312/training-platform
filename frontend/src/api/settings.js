import request from '@/utils/request'

export function getSettings() {
  return request({
    url: '/v1/settings',
    method: 'get',
  })
}

export function updateSettings(data) {
  return request({
    url: '/v1/settings',
    method: 'put',
    data,
  })
}

export function testEmailConfig(email) {
  return request({
    url: '/v1/settings/test-email',
    method: 'post',
    data: { email },
  })
}