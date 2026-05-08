import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/Login.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/',
    component: () => import('@/layouts/DefaultLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('@/views/employee/Dashboard.vue'),
      },
      {
        path: 'training',
        name: 'TrainingList',
        component: () => import('@/views/employee/TrainingList.vue'),
      },
      {
        path: 'training/:id',
        name: 'TrainingDetail',
        component: () => import('@/views/employee/TrainingDetail.vue'),
      },
      {
        path: 'training/:id/material/:materialId',
        name: 'MaterialPlayer',
        component: () => import('@/views/employee/MaterialPlayer.vue'),
      },
      {
        path: 'exam/:id',
        name: 'ExamPage',
        component: () => import('@/views/employee/ExamPage.vue'),
      },
      {
        path: 'notification',
        name: 'EmployeeNotification',
        component: () => import('@/views/employee/Notification.vue'),
      },
      {
        path: 'exam-history',
        name: 'ExamHistory',
        component: () => import('@/views/employee/ExamHistory.vue'),
      },
    ],
  },
  {
    path: '/hr',
    component: () => import('@/layouts/HrLayout.vue'),
    meta: { requiresAuth: true, requiresHr: true },
    children: [
      {
        path: '',
        name: 'HrDashboard',
        component: () => import('@/views/hr/Dashboard.vue'),
      },
      {
        path: 'training',
        name: 'TrainingManage',
        component: () => import('@/views/hr/TrainingManage.vue'),
      },
      {
        path: 'training/create',
        name: 'TrainingCreate',
        component: () => import('@/views/hr/TrainingCreate.vue'),
      },
      {
        path: 'training/:id/edit',
        name: 'TrainingEdit',
        component: () => import('@/views/hr/TrainingCreate.vue'),
      },
      {
        path: 'training/:id/material',
        name: 'MaterialUpload',
        component: () => import('@/views/hr/MaterialUpload.vue'),
      },
      {
        path: 'training/:id/exam',
        name: 'ExamEditor',
        component: () => import('@/views/hr/ExamEditor.vue'),
      },
      {
        path: 'department',
        name: 'DepartmentManage',
        component: () => import('@/views/hr/DepartmentManage.vue'),
      },
      {
        path: 'progress',
        name: 'ProgressReport',
        component: () => import('@/views/hr/ProgressReport.vue'),
      },
      {
        path: 'notification',
        name: 'HrNotification',
        component: () => import('@/views/hr/Notification.vue'),
      },
      {
        path: 'settings',
        name: 'HrSettings',
        component: () => import('@/views/hr/Settings.vue'),
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Navigation guard
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()

  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
    return
  }

  if (to.meta.requiresHr && !userStore.isHrAdmin) {
    next({ name: 'Dashboard' })
    return
  }

  if (to.name === 'Login' && userStore.isLoggedIn) {
    next(userStore.isHrAdmin ? '/hr' : '/')
    return
  }

  next()
})

export default router