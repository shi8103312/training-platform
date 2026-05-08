<template>
  <div class="training-create">
    <el-button class="back-btn" :icon="ArrowLeft" @click="$router.back()">
      {{ isEdit ? '返回编辑' : '返回' }}
    </el-button>

    <el-card>
      <template #header>
        <span>{{ isEdit ? '编辑培训项目' : '创建培训项目' }}</span>
      </template>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
        style="max-width: 600px"
      >
        <el-form-item label="项目名称" prop="title">
          <el-input v-model="form.title" placeholder="请输入项目名称" maxlength="50" show-word-limit />
        </el-form-item>

        <el-form-item label="项目描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="4"
            placeholder="请输入项目描述"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="封面图片" prop="cover_image">
          <el-input v-model="form.cover_image" placeholder="请输入封面图片URL" />
        </el-form-item>

        <el-form-item label="截止日期" prop="deadline">
          <el-date-picker
            v-model="form.deadline"
            type="datetime"
            placeholder="选择截止日期"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="是否必修" prop="is_required">
          <el-switch v-model="form.is_required" />
        </el-form-item>

        <el-form-item label="推送范围" prop="push_scope">
          <el-radio-group v-model="form.push_scope.type" @change="handleScopeTypeChange">
            <el-radio value="all">全员</el-radio>
            <el-radio value="departments">指定部门</el-radio>
            <el-radio value="users">指定人员</el-radio>
          </el-radio-group>

          <div v-if="form.push_scope.type === 'departments'" class="scope-select">
            <el-tree-select
              v-model="form.push_scope.departments"
              :data="departmentTree"
              :props="{ label: 'dept_name', value: 'dept_id', children: 'children' }"
              placeholder="选择部门"
              multiple
              check-strictly
              :render-after-expand="false"
            />
          </div>

          <div v-if="form.push_scope.type === 'users'" class="scope-select">
            <el-select
              v-model="form.push_scope.users"
              multiple
              filterable
              placeholder="选择人员"
              style="width: 100%"
            >
              <el-option
                v-for="user in userList"
                :key="user.user_id"
                :label="user.real_name"
                :value="user.user_id"
              />
            </el-select>
          </div>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleSubmit">
            {{ isEdit ? '保存' : '创建' }}
          </el-button>
          <el-button @click="$router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTrainingStore } from '@/stores/training'
import { getDepartmentTree } from '@/api/department'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const trainingStore = useTrainingStore()

const formRef = ref(null)
const loading = ref(false)
const isEdit = computed(() => !!route.params.id)

const departmentTree = ref([])
const userList = ref([])

const form = reactive({
  title: '',
  description: '',
  cover_image: '',
  deadline: null,
  is_required: true,
  push_scope: {
    type: 'all',
    departments: [],
    users: [],
  },
})

const rules = {
  title: [
    { required: true, message: '请输入项目名称', trigger: 'blur' },
    { max: 50, message: '项目名称不能超过50个字符', trigger: 'blur' },
  ],
  deadline: [
    { required: true, message: '请选择截止日期', trigger: 'change' },
  ],
  push_scope: [
    {
      validator: (rule, value, callback) => {
        if (value.type === 'departments' && (!value.departments || value.departments.length === 0)) {
          callback(new Error('请选择部门'))
        } else if (value.type === 'users' && (!value.users || value.users.length === 0)) {
          callback(new Error('请选择人员'))
        } else {
          callback()
        }
      },
      trigger: 'change',
    },
  ],
}

function handleScopeTypeChange() {
  if (form.push_scope.type === 'all') {
    form.push_scope.departments = []
    form.push_scope.users = []
  }
}

async function handleSubmit() {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    try {
      const projectData = {
        ...form,
        deadline: form.deadline,
      }

      let res
      if (isEdit.value) {
        res = await trainingStore.update(route.params.id, projectData)
      } else {
        res = await trainingStore.create(projectData)
      }

      if (res.code === 0) {
        ElMessage.success(isEdit.value ? '保存成功' : '创建成功')
        router.push('/hr/training')
      } else {
        ElMessage.error(res.message || '操作失败')
      }
    } finally {
      loading.value = false
    }
  })
}

async function fetchDepartmentTree() {
  try {
    const res = await getDepartmentTree()
    if (res.code === 0) {
      departmentTree.value = res.data
    }
  } catch (error) {
    console.error('Failed to fetch department tree:', error)
  }
}

async function fetchProjectDetail() {
  if (!isEdit.value) return

  await trainingStore.fetchProjectDetail(route.params.id)
  const project = trainingStore.currentProject

  if (project) {
    form.title = project.title
    form.description = project.description || ''
    form.cover_image = project.cover_image || ''
    form.deadline = new Date(project.deadline)
    form.is_required = project.is_required

    const scope = typeof project.push_scope === 'string'
      ? JSON.parse(project.push_scope)
      : project.push_scope
    form.push_scope = {
      type: scope.type || 'all',
      departments: scope.departments || [],
      users: scope.users || [],
    }
  }
}

onMounted(async () => {
  await Promise.all([fetchDepartmentTree(), fetchProjectDetail()])
})
</script>

<style scoped>
.training-create {
  max-width: 800px;
}

.back-btn {
  margin-bottom: 20px;
}

.scope-select {
  margin-top: 12px;
}
</style>