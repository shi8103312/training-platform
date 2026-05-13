<template>
  <div class="exam-editor">
    <el-button class="back-btn" :icon="ArrowLeft" @click="$router.back()">
      返回
    </el-button>

    <el-card>
      <template #header>
        <span>考试设置 - {{ project?.title }}</span>
      </template>

      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px" style="max-width: 600px">
        <el-form-item label="考试标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入考试标题" maxlength="100" show-word-limit />
        </el-form-item>

        <el-form-item label="考试说明" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入考试说明" />
        </el-form-item>

        <el-form-item label="考试时长" prop="duration_minutes">
          <el-input-number v-model="form.duration_minutes" :min="1" :max="180" />
          <span style="margin-left: 8px">分钟</span>
        </el-form-item>

        <el-form-item label="及格分数" prop="passing_score">
          <el-input-number v-model="form.passing_score" :min="0" :max="100" />
          <span style="margin-left: 8px">分</span>
        </el-form-item>

        <el-form-item label="允许考试次数" prop="attempt_limit">
          <el-input-number v-model="form.attempt_limit" :min="1" :max="10" />
        </el-form-item>

        <el-form-item label="题目随机顺序" prop="random_shuffle">
          <el-switch v-model="form.random_shuffle" />
        </el-form-item>

        <el-form-item label="考后显示答案" prop="show_answer">
          <el-switch v-model="form.show_answer" />
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="questions-card">
      <template #header>
        <div class="card-header">
          <span>题目列表 ({{ form.questions.length }}题)</span>
          <el-button type="primary" @click="handleAddQuestion">
            <el-icon><Plus /></el-icon>
            添加题目
          </el-button>
        </div>
      </template>

      <el-empty v-if="form.questions.length === 0" description="暂无题目" />

      <div v-else class="questions-list">
        <div v-for="(q, index) in form.questions" :key="index" class="question-item">
          <div class="question-header">
            <span class="index">{{ index + 1 }}</span>
            <el-tag size="small">{{ getQuestionTypeName(q.question_type) }}</el-tag>
            <span class="score">{{ q.score }}分</span>
            <el-button type="danger" link @click="handleRemoveQuestion(index)">删除</el-button>
          </div>

          <p class="question-text">{{ q.question_text }}</p>

          <div v-if="q.options" class="options-list">
            <div v-for="opt in q.options" :key="opt.key" class="option-item">
              <span class="option-key">{{ opt.key }}.</span>
              <span>{{ opt.text }}</span>
              <el-tag v-if="q.correct_answer?.includes(opt.key)" type="success" size="small">
                正确答案
              </el-tag>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <div class="actions">
      <el-button type="primary" :loading="saving" @click="handleSave">保存考试</el-button>
    </div>

    <el-dialog v-model="showQuestionDialog" title="添加题目" width="700px">
      <el-form ref="questionFormRef" :model="questionForm" :rules="questionRules" label-width="100px">
        <el-form-item label="题目类型" prop="question_type">
          <el-select v-model="questionForm.question_type">
            <el-option :value="1" label="单选题" />
            <el-option :value="2" label="多选题" />
            <el-option :value="3" label="判断题" />
            <el-option :value="4" label="简答题" />
          </el-select>
        </el-form-item>

        <el-form-item label="题目内容" prop="question_text">
          <el-input v-model="questionForm.question_text" type="textarea" :rows="2" />
        </el-form-item>

        <el-form-item label="分值" prop="score">
          <el-input-number v-model="questionForm.score" :min="1" :max="100" />
        </el-form-item>

        <el-form-item label="选项" v-if="questionForm.question_type !== 3 && questionForm.question_type !== 4">
          <div class="options-editor">
            <div v-for="(opt, idx) in questionForm.options" :key="idx" class="option-row">
              <el-input v-model="opt.key" style="width: 60px" placeholder="选项" />
              <el-input v-model="opt.text" style="flex: 1" placeholder="选项内容" />
              <el-button type="danger" link @click="handleRemoveOption(idx)">删除</el-button>
            </div>
            <el-button type="primary" link @click="handleAddOption">添加选项</el-button>
          </div>
        </el-form-item>

        <el-form-item label="正确答案" prop="correct_answer">
          <el-select v-if="questionForm.question_type === 1" v-model="questionForm.correct_answer">
            <el-option v-for="opt in questionForm.options" :key="opt.key" :value="opt.key" :label="opt.key" />
          </el-select>
          <el-checkbox-group v-else-if="questionForm.question_type === 2" v-model="questionForm.correct_answer">
            <el-checkbox v-for="opt in questionForm.options" :key="opt.key" :value="opt.key" />
          </el-checkbox-group>
          <el-radio-group v-else-if="questionForm.question_type === 3" v-model="questionForm.correct_answer">
            <el-radio value="true">正确</el-radio>
            <el-radio value="false">错误</el-radio>
          </el-radio-group>
          <el-input v-else-if="questionForm.question_type === 4" v-model="questionForm.correct_answer" type="textarea" :rows="3" placeholder="请输入正确答案" />
        </el-form-item>

        <el-form-item label="答案解析">
          <el-input v-model="questionForm.explanation" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showQuestionDialog = false">取消</el-button>
        <el-button type="primary" @click="handleAddQuestionConfirm">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTrainingStore } from '@/stores/training'
import { createExam, getExamDetail } from '@/api/exam'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Plus } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const trainingStore = useTrainingStore()

const loading = ref(false)
const saving = ref(false)
const project = ref(null)
const formRef = ref(null)
const questionFormRef = ref(null)
const showQuestionDialog = ref(false)

const form = reactive({
  title: '',
  description: '',
  duration_minutes: 60,
  passing_score: 60,
  attempt_limit: 1,
  random_shuffle: false,
  show_answer: false,
  questions: [],
})

const rules = {
  title: [{ required: true, message: '请输入考试标题', trigger: 'blur' }],
  duration_minutes: [{ required: true, message: '请设置考试时长', trigger: 'change' }],
  passing_score: [{ required: true, message: '请设置及格分数', trigger: 'change' }],
}

const questionForm = reactive({
  question_type: 1,
  question_text: '',
  score: 5,
  options: [
    { key: 'A', text: '' },
    { key: 'B', text: '' },
    { key: 'C', text: '' },
    { key: 'D', text: '' },
  ],
  correct_answer: '',
  explanation: '',
})

const questionRules = {
  question_text: [{ required: true, message: '请输入题目内容', trigger: 'blur' }],
  correct_answer: [{ required: true, message: '请设置正确答案', trigger: 'change' }],
}

function getQuestionTypeName(type) {
  const names = { 1: '单选题', 2: '多选题', 3: '判断题', 4: '简答题' }
  return names[type] || '未知'
}

function handleAddQuestion() {
  questionForm.question_type = 1
  questionForm.question_text = ''
  questionForm.score = 5
  questionForm.options = [
    { key: 'A', text: '' },
    { key: 'B', text: '' },
    { key: 'C', text: '' },
    { key: 'D', text: '' },
  ]
  questionForm.correct_answer = ''
  questionForm.explanation = ''
  showQuestionDialog.value = true
}

function handleAddOption() {
  const nextKey = String.fromCharCode(65 + questionForm.options.length)
  questionForm.options.push({ key: nextKey, text: '' })
}

function handleRemoveOption(index) {
  questionForm.options.splice(index, 1)
  // Re-index keys
  questionForm.options.forEach((opt, idx) => {
    opt.key = String.fromCharCode(65 + idx)
  })
}

function handleRemoveQuestion(index) {
  form.questions.splice(index, 1)
}

function handleAddQuestionConfirm() {
  if (!questionFormRef.value) return

  questionFormRef.value.validate((valid) => {
    if (!valid) return

    const q = {
      question_type: questionForm.question_type,
      question_text: questionForm.question_text,
      score: questionForm.score,
      explanation: questionForm.explanation,
    }

    if (questionForm.question_type === 4) {
      // 简答题
      q.options = null
      q.correct_answer = questionForm.correct_answer
    } else if (questionForm.question_type === 3) {
      // 判断题
      q.options = null
      q.correct_answer = questionForm.correct_answer
    } else {
      // 单选/多选
      q.options = questionForm.options.filter((o) => o.text)
      q.correct_answer = questionForm.question_type === 2
        ? JSON.stringify(questionForm.correct_answer)
        : questionForm.correct_answer
    }

    form.questions.push(q)
    showQuestionDialog.value = false
  })
}

async function handleSave() {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    if (form.questions.length === 0) {
      ElMessage.warning('请至少添加一道题目')
      return
    }

    saving.value = true
    try {
      const res = await createExam({
        project_id: route.params.id,
        ...form,
      })

      if (res.code === 0) {
        ElMessage.success('保存成功')
        router.push('/hr/training')
      } else {
        ElMessage.error(res.message || '保存失败')
      }
    } finally {
      saving.value = false
    }
  })
}

onMounted(async () => {
  await trainingStore.fetchProjectDetail(route.params.id)
  project.value = trainingStore.currentProject
  form.title = `${project.value?.title || ''} - 考试`
})
</script>

<style scoped>
.exam-editor {
  max-width: 900px;
}

.back-btn {
  margin-bottom: 20px;
}

.questions-card {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.questions-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.question-item {
  padding: 16px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
}

.question-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.question-header .index {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #409eff;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
}

.question-header .score {
  margin-left: auto;
  color: #f56c6c;
  font-size: 14px;
}

.question-text {
  font-size: 14px;
  color: #303133;
  margin: 0 0 12px;
  line-height: 1.6;
}

.options-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.option-key {
  font-weight: 600;
  color: #409eff;
}

.actions {
  margin-top: 20px;
  text-align: center;
}

.options-editor {
  width: 100%;
}

.option-row {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}
</style>