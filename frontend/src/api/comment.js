import request from '@/utils/request'

export function getComments(params) {
  return request({
    url: '/v1/comment/' + params.project_id,
    method: 'get',
    params,
  })
}

export function createComment(data) {
  return request({
    url: '/v1/comment',
    method: 'post',
    data,
  })
}

export function deleteComment(commentId) {
  return request({
    url: `/v1/comment/${commentId}`,
    method: 'delete',
  })
}

export function likeComment(commentId) {
  return request({
    url: `/v1/comment/${commentId}/like`,
    method: 'post',
  })
}

export function unlikeComment(commentId) {
  return request({
    url: `/v1/comment/${commentId}/like`,
    method: 'delete',
  })
}

export function getMyMentions(params) {
  return request({
    url: '/v1/comment/mentions/me',
    method: 'get',
    params,
  })
}

export function searchUsers(keyword) {
  return request({
    url: '/v1/comment/users/search',
    method: 'get',
    params: { keyword },
  })
}
