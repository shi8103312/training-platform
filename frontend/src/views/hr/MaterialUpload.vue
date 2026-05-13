<template>
  <div class="material-upload">
    <el-button class="back-btn" :icon="ArrowLeft" @click="$router.back()">
      返回
    </el-button>

    <el-card>
      <template #header>
        <div class="card-header">
          <span>培训材料 - {{ project?.title }}</span>
          <el-button type="primary" @click="showUploadDialog = true">
            <el-icon><Upload /></el-icon>
            上传材料
          </el-button>
        </div>
      </template>

      <el-table :data="materials" v-loading="loading" style="width: 100%">
        <el-table-column prop="title" label="材料名称" />
        <el-table-column prop="material_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="row.material_type === 1 ? 'primary' : 'success'">
              {{ row.material_type === 1 ? '视频' : '文档' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="时长" width="100">
          <template #default="{ row }">
            {{ row.duration ? formatDuration(row.duration) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="file_size" label="大小" width="100">
          <template #default="{ row }">
            {{ formatSize(row.file_size) }}
          </template>
        </el-table-column>
        <el-table-column prop="sort_order" label="排序" width="80" />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showUploadDialog" title="上传材料" width="500px">
      <el-form ref="uploadFormRef" :model="uploadForm" :rules="uploadRules" label-width="100px">
        <el-form-item label="材料标题" prop="title">
          <el-input v-model="uploadForm.title" placeholder="请输入材料标题" />
        </el-form-item>

        <el-form-item label="材料类型" prop="material_type">
          <el-radio-group v-model="uploadForm.material_type">
            <el-radio :value="1">视频</el-radio>
            <el-radio :value="2">文档</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="排序" prop="sort_order">
          <el-input-number v-model="uploadForm.sort_order" :min="0" />
        </el-form-item>

        <el-form-item label="上传文件" prop="file">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            :file-list="fileList"
            :disabled="uploading"
          >
            <el-button type="primary">选择文件</el-button>
            <template #tip>
              <div class="el-upload__tip">
                <p>视频：MP4/AVI，最大2GB</p>
                <p>文档：PDF/Word，最大100MB</p>
              </div>
            </template>
          </el-upload>
        </el-form-item>

        <el-form-item v-if="uploading" label="上传进度">
          <el-progress :percentage="uploadPercentage" :stroke-width="12" />
          <span class="upload-progress-text">{{ uploadProgressText }}</span>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showUploadDialog = false" :disabled="uploading">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="handleUpload">上传</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTrainingStore } from '@/stores/training'
import { uploadMaterial, uploadMaterialWithProgress, deleteMaterial } from '@/api/training'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Upload } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const trainingStore = useTrainingStore()

const loading = ref(false)
const uploading = ref(false)
const uploadPercentage = ref(0)
const uploadProgressText = ref('')
const project = ref(null)
const materials = ref([])
const showUploadDialog = ref(false)
const uploadFormRef = ref(null)
const uploadRef = ref(null)
const fileList = ref([])

const uploadForm = ref({
  title: '',
  material_type: 1,
  sort_order: 0,
  file: null,
})

const uploadRules = {
  title: [{ required: true, message: '请输入材料标题', trigger: 'blur' }],
  material_type: [{ required: true, message: '请选择材料类型', trigger: 'change' }],
  file: [{ required: true, message: '请选择文件', trigger: 'change' }],
}

function formatDuration(seconds) {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + 'B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + 'KB'
  if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + 'MB'
  return (bytes / (1024 * 1024 * 1024)).toFixed(1) + 'GB'
}

function handleFileChange(file) {
  uploadForm.value.file = file.raw
  if (!uploadForm.value.title) {
    uploadForm.value.title = file.name.replace(/\.[^/.]+$/, '')
  }
}

async function handleUpload() {
  if (!uploadFormRef.value) return

  await uploadFormRef.value.validate(async (valid) => {
    if (!valid) return

    uploading.value = true
    uploadPercentage.value = 0
    uploadProgressText.value = '准备上传...'

    try {
      const formData = new FormData()
      formData.append('project_id', route.params.id)
      formData.append('title', uploadForm.value.title)
      formData.append('material_type', uploadForm.value.material_type)
      formData.append('sort_order', uploadForm.value.sort_order)
      formData.append('file', uploadForm.value.file)

      const res = await uploadMaterialWithProgress(formData, (percent, text) => {
        uploadPercentage.value = percent
        uploadProgressText.value = text
      })

      if (res.code === 0) {
        ElMessage.success('上传成功')
        showUploadDialog.value = false
        fileList.value = []
        uploadForm.value = {
          title: '',
          material_type: 1,
          sort_order: 0,
          file: null,
        }
        await fetchMaterials()
      } else {
        ElMessage.error(res.message || '上传失败')
      }
    } finally {
      uploading.value = false
      uploadPercentage.value = 0
      uploadProgressText.value = ''
    }
  })
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm('确定要删除该材料吗？', '提示', {
      type: 'warning',
    })

    const res = await deleteMaterial(row.material_id)
    if (res.code === 0) {
      ElMessage.success('删除成功')
      await fetchMaterials()
    }
  } catch {
    // Cancelled
  }
}

async function fetchMaterials() {
  loading.value = true
  try {
    await trainingStore.fetchProjectDetail(route.params.id)
    project.value = trainingStore.currentProject
    materials.value = trainingStore.materials
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchMaterials()
})
</script>

<style scoped>
.material-upload {
  max-width: 1000px;
}

.back-btn {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.el-upload__tip {
  margin-top: 8px;
  color: #909399;
}

.el-upload__tip p {
  margin: 4px 0;
}

.upload-progress-text {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
}
</style>