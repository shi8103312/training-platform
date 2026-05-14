<template>
  <div class="hr-notification">
    <div class="form-card">
      <div class="form-title">📧 通知内容</div>

      <div class="form-item">
        <label>选择培训项目 <span class="required">*</span></label>
        <select v-model="form.projectId">
          <option value="">请选择培训项目</option>
          <option v-for="p in projectList" :key="p.project_id" :value="p.project_id">
            {{ p.title }}
          </option>
        </select>
      </div>

      <div class="form-item">
        <label>通知标题 <span class="required">*</span></label>
        <input type="text" v-model="form.title" placeholder="请输入通知标题" />
      </div>

      <div class="form-item">
        <label>通知内容 <span class="required">*</span></label>
        <textarea v-model="form.content" placeholder="请输入通知内容..."></textarea>
      </div>
    </div>

    <!-- 推送范围 -->
    <div class="form-card">
      <div class="form-title">👥 推送范围</div>

      <div class="scope-selector">
        <label class="scope-option">
          <input type="radio" v-model="form.pushScope" value="all" />
          <span>全员 ({{ stats.total }}人)</span>
        </label>
        <label class="scope-option">
          <input type="radio" v-model="form.pushScope" value="departments" />
          <span>指定部门</span>
        </label>
        <div class="dept-tree" v-if="form.pushScope === 'departments'">
          <label class="dept-item" v-for="dept in departmentList" :key="dept.dept_id">
            <input type="checkbox" v-model="selectedDepts" :value="dept.dept_id" />
            {{ dept.dept_name }}
          </label>
        </div>
        <label class="scope-option">
          <input type="radio" v-model="form.pushScope" value="users" />
          <span>指定人员</span>
        </label>
        <div class="dept-tree" v-if="form.pushScope === 'users'">
          <div class="user-list">
            <div class="user-item" v-for="user in userList" :key="user.user_id">
              <input type="checkbox" v-model="selectedUsers" :value="user.user_id" />
              <span class="name">{{ user.real_name }}</span>
              <span class="dept">{{ user.dept_name }}</span>
            </div>
          </div>
          <div class="selected-count">已选择 {{ selectedUsers.length }} 人</div>
        </div>
      </div>

      <div class="selected-count">预计发送人数：{{ estimatedRecipients }} 人</div>
    </div>

    <!-- 发送时间 -->
    <div class="form-card">
      <div class="form-title">⏰ 发送时间</div>

      <div class="schedule-options">
        <label class="schedule-option" :class="{ selected: form.sendType === 'now' }">
          <input type="radio" v-model="form.sendType" value="now" />
          <div class="title">🚀 立即发送</div>
          <div class="desc">通知将立即发送到所有接收者邮箱</div>
        </label>
        <label class="schedule-option" :class="{ selected: form.sendType === 'scheduled' }">
          <input type="radio" v-model="form.sendType" value="scheduled" />
          <div class="title">⏰ 定时发送</div>
          <div class="desc">设置具体发送时间</div>
        </label>
      </div>

      <div class="form-item" v-if="form.sendType === 'scheduled'" style="margin-top: 20px">
        <label>发送时间</label>
        <input type="datetime-local" v-model="form.scheduleTime" />
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="action-bar">
      <button class="btn btn-outline" @click="handleReset">取消</button>
      <button class="btn btn-primary" @click="handleSend">
        {{ form.sendType === 'now' ? '✉️ 发送通知' : '⏰ 设置定时发送' }}
      </button>
    </div>

    <!-- 发送历史 -->
    <div class="recent-history">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px">
        <h3 style="font-size: 16px; font-weight: 600; color: #333; margin: 0">📋 最近发送记录</h3>
        <el-button size="small" @click="handleExportHistory">导出记录</el-button>
      </div>
      <div class="form-card" style="padding: 0">
        <table class="history-table">
          <thead>
            <tr>
              <th>通知标题</th>
              <th>培训项目</th>
              <th>发送范围</th>
              <th>发送时间</th>
              <th>发送人数</th>
              <th>状态</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in history" :key="item.id">
              <td>{{ item.title }}</td>
              <td>{{ item.project }}</td>
              <td>{{ item.scope }}</td>
              <td>{{ item.sendTime }}</td>
              <td>{{ item.count }}人</td>
              <td>
                <span class="status-badge" :class="item.statusClass">{{ item.statusText }}</span>
              </td>
            </tr>
            <tr v-if="history.length === 0">
              <td colspan="6" style="text-align: center; color: #999; padding: 40px">暂无发送记录</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useTrainingStore } from '@/stores/training'
import { getDepartmentList } from '@/api/department'
import { getUserList } from '@/api/auth'
import { sendNotification, getNotificationHistory } from '@/api/notification'
import dayjs from 'dayjs'
import * as XLSX from 'xlsx'

const trainingStore = useTrainingStore()

const projectList = ref([])
const departmentList = ref([])
const userList = ref([])
const history = ref([])

const selectedDepts = ref([])
const selectedUsers = ref([])

const stats = reactive({
  total: 0,
})

const form = reactive({
  projectId: '',
  title: '',
  content: '',
  pushScope: 'all',
  sendType: 'now',
  scheduleTime: '',
})

const estimatedRecipients = computed(() => {
  if (form.pushScope === 'all') return stats.total
  if (form.pushScope === 'departments') return selectedDepts.value.length * 50
  return selectedUsers.value.length
})

async function fetchProjectList() {
  try {
    await trainingStore.fetchProjectList({ page: 1, page_size: 100 })
    projectList.value = trainingStore.projectList || []
  } catch (error) {
    console.error('Failed to fetch project list:', error)
  }
}

async function fetchDepartmentList() {
  try {
    const res = await getDepartmentList()
    if (res.code === 0) {
      departmentList.value = res.data || []
    }
  } catch (error) {
    console.error('Failed to fetch department list:', error)
  }
}

async function fetchUserList() {
  try {
    const res = await getUserList()
    if (res.code === 0) {
      userList.value = res.data || []
      stats.total = userList.value.length
    }
  } catch (error) {
    console.error('Failed to fetch user list:', error)
  }
}

async function fetchHistory() {
  try {
    const res = await getNotificationHistory()
    if (res.code === 0) {
      history.value = res.data || []
    }
  } catch (error) {
    console.error('Failed to fetch notification history:', error)
  }
}

function handleReset() {
  form.projectId = ''
  form.title = ''
  form.content = ''
  form.pushScope = 'all'
  form.sendType = 'now'
  form.scheduleTime = ''
  selectedDepts.value = []
  selectedUsers.value = []
}

async function handleSend() {
  if (!form.projectId) {
    ElMessage.warning('请选择培训项目')
    return
  }
  if (!form.title) {
    ElMessage.warning('请输入通知标题')
    return
  }
  if (!form.content) {
    ElMessage.warning('请输入通知内容')
    return
  }

  try {
    const data = {
      project_id: form.projectId,
      title: form.title,
      content: form.content,
      push_scope: form.pushScope,
      ...(form.pushScope === 'departments' && { dept_ids: selectedDepts.value }),
      ...(form.pushScope === 'users' && { user_ids: selectedUsers.value }),
      ...(form.sendType === 'scheduled' && { schedule_time: form.scheduleTime }),
    }

    const res = await sendNotification(data)
    if (res.code === 0) {
      ElMessage.success(form.sendType === 'now' ? '通知发送成功！' : '定时发送设置成功！')
      handleReset()
      fetchHistory()
    } else {
      ElMessage.error(res.message || '发送失败')
    }
  } catch (error) {
    ElMessage.error('发送失败')
    console.error('Failed to send notification:', error)
  }
}

function handleExportHistory() {
  if (history.value.length === 0) {
    ElMessage.warning('暂无数据可导出')
    return
  }

  try {
    const exportData = history.value.map(item => ({
      '通知标题': item.title,
      '培训项目': item.project,
      '发送范围': item.scope,
      '发送时间': item.sendTime,
      '发送人数': item.count + '人',
      '状态': item.statusText,
    }))

    const ws = XLSX.utils.json_to_sheet(exportData)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, '通知发送记录')

    ws['!cols'] = [
      { wch: 25 }, // 通知标题
      { wch: 20 }, // 培训项目
      { wch: 15 }, // 发送范围
      { wch: 20 }, // 发送时间
      { wch: 10 }, // 发送人数
      { wch: 10 }, // 状态
    ]

    const filename = `通知发送记录_${dayjs().format('YYYY-MM-DD')}.xlsx`
    XLSX.writeFile(wb, filename)
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('Export error:', error)
    ElMessage.error('导出失败')
  }
}

onMounted(async () => {
  await Promise.all([
    fetchProjectList(),
    fetchDepartmentList(),
    fetchUserList(),
    fetchHistory(),
  ])
})
</script>

<style scoped>
.hr-notification {
  font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
  max-width: 900px;
}

.form-card {
  background: #fff;
  border-radius: 10px;
  padding: 30px;
  margin-bottom: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.form-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 25px;
  padding-bottom: 15px;
  border-bottom: 1px solid #f0f0f0;
}

.form-item {
  margin-bottom: 20px;
}

.form-item label {
  display: block;
  font-size: 14px;
  color: #333;
  margin-bottom: 8px;
  font-weight: 500;
}

.form-item label .required {
  color: #ff4d4f;
  margin-left: 4px;
}

.form-item input,
.form-item select,
.form-item textarea {
  width: 100%;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  padding: 10px 15px;
  font-size: 14px;
  transition: border-color 0.3s;
  font-family: inherit;
}

.form-item input:focus,
.form-item select:focus,
.form-item textarea:focus {
  outline: none;
  border-color: var(--theme-primary);
}

.form-item textarea {
  resize: vertical;
  min-height: 100px;
}

.form-item .hint {
  font-size: 12px;
  color: #999;
  margin-top: 6px;
}

.scope-selector {
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  padding: 15px;
}

.scope-option {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
  cursor: pointer;
}

.scope-option:last-child {
  margin-bottom: 0;
}

.scope-option input[type='radio'] {
  width: 18px;
  height: 18px;
}

.dept-tree {
  margin-left: 26px;
  margin-top: 10px;
  padding: 10px;
  background: #f8f8ff;
  border-radius: 6px;
  max-height: 200px;
  overflow-y: auto;
}

.dept-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  cursor: pointer;
}

.dept-item input[type='checkbox'] {
  width: 16px;
  height: 16px;
}

.user-list {
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  max-height: 200px;
  overflow-y: auto;
}

.user-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 15px;
  border-bottom: 1px solid #f5f7fa;
  cursor: pointer;
}

.user-item:last-child {
  border-bottom: none;
}

.user-item:hover {
  background: #f8f8ff;
}

.user-item input[type='checkbox'] {
  width: 16px;
  height: 16px;
}

.user-item .name {
  flex: 1;
  font-size: 14px;
  color: #333;
}

.user-item .dept {
  font-size: 12px;
  color: #999;
}

.selected-count {
  margin-top: 10px;
  font-size: 13px;
  color: var(--theme-primary);
}

.schedule-options {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
  margin-top: 15px;
}

.schedule-option {
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  padding: 15px;
  cursor: pointer;
  transition: all 0.3s;
}

.schedule-option:hover {
  border-color: var(--theme-primary);
}

.schedule-option.selected {
  border-color: var(--theme-primary);
  background: #e6f0ff;
}

.schedule-option input[type='radio'] {
  display: none;
}

.schedule-option .title {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
}

.schedule-option .desc {
  font-size: 12px;
  color: #999;
}

.action-bar {
  background: #fff;
  border-radius: 10px;
  padding: 20px;
  display: flex;
  justify-content: center;
  gap: 15px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.btn {
  height: 36px;
  padding: 0 20px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  border: none;
  transition: all 0.3s;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.btn-primary {
  background: var(--theme-gradient);
  color: #fff;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.btn-outline {
  background: #fff;
  color: var(--theme-primary);
  border: 1px solid var(--theme-primary);
}

.btn-outline:hover {
  background: #f5f7ff;
}

.recent-history {
  margin-top: 30px;
}

.history-table {
  width: 100%;
  border-collapse: collapse;
}

.history-table th {
  text-align: left;
  padding: 12px;
  background: #fafafa;
  font-size: 13px;
  color: #999;
  font-weight: 500;
  border-bottom: 1px solid #f0f0f0;
}

.history-table td {
  padding: 14px 12px;
  border-bottom: 1px solid #f5f7fa;
  font-size: 14px;
  color: #333;
}

.history-table tr:hover {
  background: #f8f8ff;
}

.status-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
}

.status-badge.sent {
  background: #f6ffed;
  color: #52c41a;
}

.status-badge.pending {
  background: #fff7e6;
  color: #fa8c16;
}

.status-badge.failed {
  background: #fff1f0;
  color: #ff4d4f;
}
</style>