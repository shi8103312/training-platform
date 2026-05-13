import request from '@/utils/request'

export function createExam(data) {
  return request({
    url: '/v1/exam',
    method: 'post',
    data,
  })
}

export function getExamDetail(examId) {
  return request({
    url: `/v1/exam/${examId}`,
    method: 'get',
  })
}

export function startExam(examId) {
  return request({
    url: `/v1/exam/${examId}/start`,
    method: 'post',
  })
}

export function saveExamAttempt(attemptId, answers, violationCount = 0) {
  return request({
    url: `/v1/exam/attempt/${attemptId}/save`,
    method: 'post',
    data: { answers, violation_count: violationCount },
  })
}

export function submitExam(attemptId, answers, violationCount = 0) {
  return request({
    url: `/v1/exam/attempt/${attemptId}/submit`,
    method: 'post',
    data: { answers, violation_count: violationCount },
  })
}

export function getExamHistory(params) {
  return request({
    url: '/v1/exam/history',
    method: 'get',
    params,
  })
}