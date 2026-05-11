<template>
  <div class="training-manage">
    <div class="header-actions">
      <h2 class="page-title">培训项目管理</h2>
      <el-button type="primary" @click="handleExport">
        导出项目
      </el-button>
    </div>

    <el-card>
      <el-tabs v-model="activeTab">
        <el-tab-pane label="全部" name="all" />
        <el-tab-pane label="草稿" name="0" />
        <el-tab-pane label="已发布" name="1" />
        <el-tab-pane label="已下架" name="2" />
      </el-tabs>

      <el-table :data="projectList" v-loading="loading" style="width: 100%">
        <el-table-column prop="title" label="项目名称" min-width="200">
          <template #default="{ row }">
            <div class="project-cell">
              <img v-if="row.cover_image" :src="row.cover_image" class="cover" />
              <div v-else class="cover-placeholder">
                <el-icon><Reading /></el-icon>
              </div>
              <div class="info">
                <span class="title">{{ row.title }}</span>
                <el-tag v-if="row.is_required" type="danger" size="small">必修</el-tag>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="status_text" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ row.status_text }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="deadline" label="截止日期" width="120">
          <template #default="{ row }">
            {{ formatDate(row.deadline) }}
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="创建时间" width="120">
          <template #default="{ row }">
            {{ formatDate(row.create_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
            <el-button type="primary" link @click="handleMaterials(row)">材料</el-button>
            <el-button type="primary" link @click="handleExam(row)">考试</el-button>
            <el-button
              v-if="row.status === 0"
              type="success"
              link
              @click="handlePublish(row)"
            >
              发布
            </el-button>
            <el-button
              v-if="row.status === 1"
              type="warning"
              link
              @click="handleUnpublish(row)"
            >
              下架
            </el-button>
            <el-button
              v-if="row.status === 0"
              type="danger"
              link
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-if="pagination.total > pagination.pageSize"
        class="pagination"
        layout="prev, pager, next"
        :total="pagination.total"
        :page-size="pagination.pageSize"
        :current-page="pagination.page"
        @current-change="handlePageChange"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useTrainingStore } from '@/stores/training'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Reading } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import * as XLSX from 'xlsx'

const router = useRouter()
const trainingStore = useTrainingStore()

const activeTab = ref('all')
const loading = ref(false)
const projectList = ref([])
const pagination = ref({ page: 1, pageSize: 20, total: 0 })

function getStatusType(status) {
  const types = { 0: 'info', 1: 'success', 2: 'warning', 3: 'info' }
  return types[status] || 'info'
}

function formatDate(date) {
  return dayjs(date).format('YYYY-MM-DD')
}

function handleEdit(row) {
  router.push(`/hr/training/${row.project_id}/edit`)
}

function handleMaterials(row) {
  router.push(`/hr/training/${row.project_id}/material`)
}

function handleExam(row) {
  router.push(`/hr/training/${row.project_id}/exam`)
}

async function handlePublish(row) {
  try {
    const res = await trainingStore.publish(row.project_id)
    if (res.code === 0) {
      ElMessage.success('发布成功')
      fetchProjects()
    } else {
      ElMessage.error(res.message || '发布失败')
    }
  } catch (error) {
    ElMessage.error('发布失败')
  }
}

async function handleUnpublish(row) {
  try {
    const res = await trainingStore.unpublish(row.project_id)
    if (res.code === 0) {
      ElMessage.success('下架成功')
      fetchProjects()
    }
  } catch (error) {
    ElMessage.error('下架失败')
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm('确定要删除该项目吗？', '提示', {
      type: 'warning',
    })

    const res = await trainingStore.remove(row.project_id)
    if (res.code === 0) {
      ElMessage.success('删除成功')
      fetchProjects()
    } else {
      ElMessage.error(res.message || '删除失败')
    }
  } catch {
    // Cancelled
  }
}

function handlePageChange(page) {
  pagination.value.page = page
  fetchProjects()
}

function handleExport() {
  if (projectList.value.length === 0) {
    ElMessage.warning('暂无数据可导出')
    return
  }

  try {
    const exportData = projectList.value.map(item => ({
      '项目名称': item.title,
      '状态': item.status_text,
      '是否必修': item.is_required ? '是' : '否',
      '截止日期': formatDate(item.deadline),
      '创建时间': formatDate(item.create_time),
    }))

    const ws = XLSX.utils.json_to_sheet(exportData)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, '培训项目')

    ws['!cols'] = [
      { wch: 30 }, // 项目名称
      { wch: 10 }, // 状态
      { wch: 10 }, // 是否必修
      { wch: 15 }, // 截止日期
      { wch: 15 }, // 创建时间
    ]

    const filename = `培训项目_${dayjs().format('YYYY-MM-DD')}.xlsx`
    XLSX.writeFile(wb, filename)
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('Export error:', error)
    ElMessage.error('导出失败')
  }
}

async function fetchProjects() {
  loading.value = true
  try {
    const params = { page: pagination.value.page, page_size: pagination.value.pageSize }
    if (activeTab.value !== 'all') {
      params.status = parseInt(activeTab.value)
    }

    await trainingStore.fetchProjectList(params)
    projectList.value = trainingStore.projectList
    pagination.value = trainingStore.pagination
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchProjects()
})

watch(activeTab, () => {
  pagination.value.page = 1
  fetchProjects()
})
</script>

<style scoped>
.training-manage {
  max-width: 1200px;
}

.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.project-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.cover {
  width: 60px;
  height: 40px;
  border-radius: 4px;
  object-fit: cover;
}

.cover-placeholder {
  width: 60px;
  height: 40px;
  border-radius: 4px;
  background: #f5f7fa;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #c0c4cc;
}

.info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info .title {
  font-weight: 500;
  color: #303133;
}

.pagination {
  margin-top: 20px;
  justify-content: center;
}
</style>