<template>
  <div class="department-manage">
    <div class="header-actions">
      <h2 class="page-title">部门管理</h2>
      <el-button type="primary" @click="showImportDialog = true">
        <el-icon><Upload /></el-icon>
        Excel导入
      </el-button>
    </div>

    <el-card>
      <el-tree
        :data="departmentTree"
        :props="treeProps"
        default-expand-all
        node-key="dept_id"
        class="department-tree"
      >
        <template #default="{ node, data }">
          <span class="tree-node">
            <span class="node-name">{{ data.dept_name }}</span>
            <span class="node-code">{{ data.dept_code }}</span>
            <el-tag size="small" :type="data.status === 1 ? 'success' : 'info'">
              {{ data.status === 1 ? '启用' : '禁用' }}
            </el-tag>
          </span>
        </template>
      </el-tree>
    </el-card>

    <el-dialog v-model="showImportDialog" title="导入部门" width="500px">
      <el-form label-width="100px">
        <el-form-item label="导入模式">
          <el-radio-group v-model="importMode">
            <el-radio value="simulate">试运行</el-radio>
            <el-radio value="create">创建</el-radio>
            <el-radio value="update">更新</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="上传文件">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            accept=".xlsx,.xls"
            :on-change="handleFileChange"
          >
            <el-button type="primary">选择Excel文件</el-button>
          </el-upload>
        </el-form-item>

        <el-alert type="info" :closable="false" style="margin-top: 12px">
          <p>Excel格式要求：</p>
          <p>第一行为表头：部门编码|部门名称|上级部门编码|排序|状态</p>
          <p>示例：DEPT001|技术部|GROUP|1|1</p>
        </el-alert>
      </el-form>

      <template #footer>
        <el-button @click="showImportDialog = false">取消</el-button>
        <el-button type="primary" :loading="importing" @click="handleImport">导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getDepartmentTree, importDepartments } from '@/api/department'
import { ElMessage } from 'element-plus'
import { Upload } from '@element-plus/icons-vue'

const departmentTree = ref([])
const showImportDialog = ref(false)
const importMode = ref('simulate')
const importing = ref(false)
const uploadRef = ref(null)
const selectedFile = ref(null)

const treeProps = {
  label: 'dept_name',
  children: 'children',
}

function handleFileChange(file) {
  selectedFile.value = file.raw
}

async function fetchDepartmentTree() {
  try {
    const res = await getDepartmentTree()
    if (res.code === 0) {
      departmentTree.value = res.data
    }
  } catch (error) {
    ElMessage.error('获取部门列表失败')
  }
}

async function handleImport() {
  if (!selectedFile.value) {
    ElMessage.warning('请选择文件')
    return
  }

  importing.value = true
  try {
    const res = await importDepartments(selectedFile.value, importMode.value)

    if (res.code === 0) {
      const { mode, total, success, failed, errors } = res.data

      if (mode === 'simulate') {
        ElMessage.success(`试运行完成：共${total}条，${success}条可导入，${failed}条有错误`)
      } else {
        ElMessage.success(`导入完成：共${total}条，${success}条成功，${failed}条失败`)
      }

      if (errors && errors.length > 0) {
        console.error('Import errors:', errors)
      }

      showImportDialog.value = false
      await fetchDepartmentTree()
    } else {
      ElMessage.error(res.message || '导入失败')
    }
  } finally {
    importing.value = false
  }
}

onMounted(() => {
  fetchDepartmentTree()
})
</script>

<style scoped>
.department-manage {
  max-width: 800px;
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

.department-tree {
  padding: 12px 0;
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.node-name {
  font-weight: 500;
  color: #303133;
}

.node-code {
  font-size: 12px;
  color: #909399;
  font-family: monospace;
}
</style>