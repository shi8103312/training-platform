<template>
  <div class="employee-manage">
    <div class="header-actions">
      <h2 class="page-title">员工管理</h2>
      <div class="header-buttons">
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>
          创建员工
        </el-button>
      </div>
    </div>

    <el-card>
      <!-- 筛选栏 -->
      <div class="filter-bar">
        <el-input
          v-model="filters.keyword"
          placeholder="搜索姓名"
          style="width: 200px"
          clearable
          @change="handleQuery"
        />
        <el-select v-model="filters.deptId" placeholder="选择部门" clearable style="width: 150px" @change="handleQuery">
          <el-option label="全部部门" value="" />
          <el-option
            v-for="dept in departmentList"
            :key="dept.dept_id"
            :label="dept.dept_name"
            :value="dept.dept_id"
          />
        </el-select>
        <el-select v-model="filters.status" placeholder="状态" clearable style="width: 120px" @change="handleQuery">
          <el-option label="全部" value="" />
          <el-option label="启用" value="1" />
          <el-option label="禁用" value="0" />
        </el-select>
        <el-button type="primary" @click="handleQuery">查询</el-button>
      </div>

      <!-- 用户列表 -->
      <el-table :data="userList" v-loading="loading" style="width: 100%">
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="real_name" label="姓名" width="120" />
        <el-table-column prop="dept_name" label="部门" width="150">
          <template #default="{ row }">
            {{ row.dept_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="email" label="邮箱" min-width="180" />
        <el-table-column prop="phone" label="手机号" width="130" />
        <el-table-column prop="role" label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="row.role === 1 ? 'danger' : 'primary'" size="small">
              {{ row.role === 1 ? '管理员' : '员工' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-switch
              v-model="row.status"
              :active-value="1"
              :inactive-value="0"
              @change="handleStatusChange(row)"
              :disabled="row.user_id === currentUserId"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
            <el-button type="danger" link @click="handleDelete(row)" :disabled="row.user_id === currentUserId">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-if="pagination.total > 0"
        class="pagination"
        layout="prev, pager, next"
        :total="pagination.total"
        :page-size="pagination.pageSize"
        :current-page="pagination.page"
        @current-change="handlePageChange"
      />
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog v-model="showCreateDialog" :title="isEdit ? '编辑员工' : '创建员工'" width="500px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="用户名" prop="username" v-if="!isEdit">
          <el-input v-model="form.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="!isEdit">
          <el-input v-model="form.password" type="password" placeholder="请输入密码（至少6位）" show-password />
        </el-form-item>
        <el-form-item label="姓名" prop="real_name">
          <el-input v-model="form.real_name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="部门">
          <el-select v-model="form.dept_id" placeholder="请选择部门" clearable style="width: 100%">
            <el-option
              v-for="dept in departmentList"
              :key="dept.dept_id"
              :label="dept.dept_name"
              :value="dept.dept_id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="form.phone" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item label="角色">
          <el-radio-group v-model="form.role">
            <el-radio :value="2">员工</el-radio>
            <el-radio :value="1">管理员</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio :value="1">启用</el-radio>
            <el-radio :value="0">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="handleCloseDialog">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">{{ isEdit ? '更新' : '创建' }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getUserList, createUser, updateUser, deleteUser } from '@/api/user'
import { getDepartmentList } from '@/api/department'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const currentUserId = userStore.userInfo?.user_id

const loading = ref(false)
const userList = ref([])
const departmentList = ref([])
const showCreateDialog = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref(null)
const editingUserId = ref(null)

const filters = reactive({
  keyword: '',
  deptId: '',
  status: '',
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

const form = reactive({
  username: '',
  password: '',
  real_name: '',
  dept_id: '',
  email: '',
  phone: '',
  role: 2,
  status: 1,
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度为3-50个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6个字符', trigger: 'blur' },
  ],
  real_name: [
    { required: true, message: '请输入姓名', trigger: 'blur' },
  ],
}

async function fetchUserList() {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
    }
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.deptId) params.dept_id = filters.deptId
    if (filters.status !== '') params.status = parseInt(filters.status)

    const res = await getUserList(params)
    if (res.code === 0) {
      userList.value = res.data || []
      pagination.total = res.pagination?.total || 0
    }
  } catch (error) {
    ElMessage.error('获取用户列表失败')
  } finally {
    loading.value = false
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

function handleQuery() {
  pagination.page = 1
  fetchUserList()
}

function handlePageChange(page) {
  pagination.page = page
  fetchUserList()
}

function handleEdit(row) {
  isEdit.value = true
  editingUserId.value = row.user_id
  form.username = row.username
  form.real_name = row.real_name
  form.dept_id = row.dept_id || ''
  form.email = row.email || ''
  form.phone = row.phone || ''
  form.role = row.role
  form.status = row.status
  form.password = ''
  showCreateDialog.value = true
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm('确定要删除该员工吗？', '提示', { type: 'warning' })
    const res = await deleteUser(row.user_id)
    if (res.code === 0) {
      ElMessage.success('删除成功')
      fetchUserList()
    } else {
      ElMessage.error(res.message || '删除失败')
    }
  } catch {
    // Cancelled
  }
}

async function handleStatusChange(row) {
  try {
    const res = await updateUser(row.user_id, { status: row.status })
    if (res.code === 0) {
      ElMessage.success(`员工已${row.status === 1 ? '启用' : '禁用'}`)
    } else {
      ElMessage.error(res.message || '状态更新失败')
      // Revert the change
      row.status = row.status === 1 ? 0 : 1
    }
  } catch {
    ElMessage.error('状态更新失败')
    // Revert the change
    row.status = row.status === 1 ? 0 : 1
  }
}

function handleCloseDialog() {
  showCreateDialog.value = false
  resetForm()
}

function resetForm() {
  form.username = ''
  form.password = ''
  form.real_name = ''
  form.dept_id = ''
  form.email = ''
  form.phone = ''
  form.role = 2
  form.status = 1
  isEdit.value = false
  editingUserId.value = null
}

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    let res
    if (isEdit.value) {
      // Update - don't send username and password
      const updateData = { ...form }
      delete updateData.username
      if (!updateData.password) delete updateData.password
      res = await updateUser(editingUserId.value, updateData)
    } else {
      res = await createUser(form)
    }

    if (res.code === 0) {
      ElMessage.success(isEdit.value ? '更新成功' : '创建成功')
      handleCloseDialog()
      fetchUserList()
    } else {
      ElMessage.error(res.message || (isEdit.value ? '更新失败' : '创建失败'))
    }
  } catch (error) {
    ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  fetchUserList()
  fetchDepartmentList()
})
</script>

<style scoped>
.employee-manage {
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

.header-buttons {
  display: flex;
  gap: 12px;
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  justify-content: center;
}
</style>
