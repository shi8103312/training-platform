import request from '@/utils/request'

export function login(username, password, deviceInfo, rememberMe = false) {
  return request({
    url: '/v1/auth/login',
    method: 'post',
    data: {
      username,
      password,
      device_info: deviceInfo,
      remember_me: rememberMe,
    },
  })
}

export function logout() {
  return request({
    url: '/v1/auth/logout',
    method: 'post',
  })
}

export function getUserInfo() {
  return request({
    url: '/v1/user/info',
    method: 'get',
  })
}

export function refreshToken(refreshToken) {
  return request({
    url: '/v1/auth/refresh',
    method: 'post',
    data: {
      refresh_token: refreshToken,
    },
  })
}

export function getDashboardStats() {
  return request({
    url: '/v1/user/stats/dashboard',
    method: 'get',
  })
}

export function getUserList(params) {
  return request({
    url: '/v1/user/list',
    method: 'get',
    params,
  })
}

export function forgotPassword(username) {
  return request({
    url: '/v1/auth/forgot-password',
    method: 'post',
    data: {
      username,
    },
  })
}

export function resetPassword(resetToken, newPassword) {
  return request({
    url: '/v1/auth/reset-password',
    method: 'post',
    data: {
      reset_token: resetToken,
      new_password: newPassword,
    },
  })
}