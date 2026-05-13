<template>
  <div class="exam-page">
    <el-button class="back-btn" :icon="ArrowLeft" @click="handleBack">
      返回
    </el-button>

    <!-- 违规警告 -->
    <div v-if="showViolationWarning" class="violation-warning">
      <el-icon color="#f56c6c" :size="20"><Warning /></el-icon>
      <span>检测到切换标签页！违规次数 +1（当前：{{ violationCount }}次）</span>
    </div>

    <el-card v-if="examStarted" class="exam-card">
      <template #header>
        <div class="exam-header">
          <h2>{{ examInfo?.title }}</h2>
          <div class="timer">
            <el-icon><Clock /></el-icon>
            <span :class="{ 'time-warning': timeRemaining < 300 }">
              {{ formatTime(timeRemaining) }}
            </span>
          </div>
        </div>
      </template>

      <div class="questions-list">
        <div
          v-for="(question, index) in questions"
          :key="question.question_id"
          class="question-item"
          :class="{ 'answered': answers[question.question_id] }"
        >
          <div class="question-header">
            <span class="question-index">{{ index + 1 }}</span>
            <span class="question-type">{{ question.question_type_text }}</span>
            <span class="question-score">{{ question.score }}分</span>
          </div>

          <p class="question-text">{{ question.question_text }}</p>

          <!-- Single Choice -->
          <el-radio-group
            v-if="question.question_type === 1"
            :model-value="answers[question.question_id]"
            @update:model-value="setAnswer(question.question_id, $event)"
          >
            <el-radio
              v-for="option in question.options"
              :key="option.key"
              :value="option.key"
            >
              {{ option.key }}. {{ option.text }}
            </el-radio>
          </el-radio-group>

          <!-- Multiple Choice -->
          <el-checkbox-group
            v-else-if="question.question_type === 2"
            :model-value="parseMultipleAnswer(answers[question.question_id])"
            @update:model-value="setMultipleAnswer(question.question_id, $event)"
          >
            <el-checkbox
              v-for="option in question.options"
              :key="option.key"
              :value="option.key"
            >
              {{ option.key }}. {{ option.text }}
            </el-checkbox>
          </el-checkbox-group>

          <!-- True/False -->
          <el-radio-group
            v-else-if="question.question_type === 3"
            :model-value="answers[question.question_id]"
            @update:model-value="setAnswer(question.question_id, $event)"
          >
            <el-radio value="true">正确</el-radio>
            <el-radio value="false">错误</el-radio>
          </el-radio-group>

          <!-- Essay Question -->
          <el-input
            v-else-if="question.question_type === 4"
            type="textarea"
            :rows="4"
            :model-value="answers[question.question_id] || ''"
            @update:model-value="setAnswer(question.question_id, $event)"
            placeholder="请输入答案..."
          />
        </div>
      </div>

      <div class="exam-footer">
        <el-button @click="handleSave">保存答题进度</el-button>
        <el-button type="primary" @click="handleSubmit">提交试卷</el-button>
      </div>
    </el-card>

    <el-card v-else class="start-card">
      <div class="start-info">
        <h2>{{ examInfo?.title }}</h2>
        <p>{{ examInfo?.description || '考试说明' }}</p>

        <div class="exam-meta">
          <div class="meta-item">
            <span class="label">考试时长:</span>
            <span class="value">{{ examInfo?.duration_minutes }}分钟</span>
          </div>
          <div class="meta-item">
            <span class="label">及格分数:</span>
            <span class="value">{{ examInfo?.passing_score }}分</span>
          </div>
          <div class="meta-item">
            <span class="label">总分:</span>
            <span class="value">{{ examInfo?.total_score }}分</span>
          </div>
          <div class="meta-item">
            <span class="label">题目数量:</span>
            <span class="value">{{ examInfo?.question_count }}题</span>
          </div>
        </div>

        <el-alert
          title="考试规则"
          type="info"
          :closable="false"
          style="margin: 20px 0"
        >
          <ul class="rules-list">
            <li>考试过程中请勿切换浏览器标签页</li>
            <li>切换标签页会被记录为违规行为</li>
            <li>超时将自动提交试卷</li>
            <li>提交后将无法再次修改答案</li>
          </ul>
        </el-alert>

        <el-button type="primary" size="large" @click="handleStart">
          开始考试
        </el-button>
      </div>
    </el-card>

    <!-- Result Dialog -->
    <el-dialog v-model="showResult" title="考试结果" width="500px" :close-on-click-modal="false">
      <div v-if="result" class="result-content">
        <div class="result-score" :class="{ pass: result.passed }">
          {{ result.score }}分
        </div>
        <p class="result-status">
          {{ result.passed ? '恭喜！您已通过考试' : '很遗憾，您未通过本次考试' }}
        </p>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="正确题数">
            {{ result.correct_count }} / {{ result.total_count }}
          </el-descriptions-item>
          <el-descriptions-item label="用时">
            {{ formatDuration(result.time_spent) }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
      <template #footer>
        <el-button type="primary" @click="handleBack">返回</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getExamDetail, startExam, saveExamAttempt, submitExam } from '@/api/exam'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Clock, Warning } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

const examInfo = ref(null)
const examStarted = ref(false)
const attemptId = ref('')
const questions = ref([])
const answers = ref({})
const timeRemaining = ref(0)
const timer = ref(null)
const showResult = ref(false)
const result = ref(null)

// 违规检测
const violationCount = ref(0)
const showViolationWarning = ref(false)
let violationTimer = null

function formatTime(seconds) {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

function formatDuration(seconds) {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}分${s}秒`
}

function parseMultipleAnswer(answer) {
  if (!answer) return []
  try {
    return JSON.parse(answer)
  } catch {
    return []
  }
}

function setAnswer(questionId, value) {
  answers.value[questionId] = value
  debouncedSave()
}

function setMultipleAnswer(questionId, value) {
  answers.value[questionId] = JSON.stringify(value)
  debouncedSave()
}

// Simple debounce implementation
let saveTimer = null
const debouncedSave = async () => {
  if (saveTimer) clearTimeout(saveTimer)
  saveTimer = setTimeout(async () => {
    if (!attemptId.value) return
    try {
      await saveExamAttempt(attemptId.value, formatAnswers(), violationCount.value)
    } catch (error) {
      console.error('Failed to save:', error)
    }
  }, 3000)
}

// 标签页切换检测
function handleVisibilityChange() {
  if (document.hidden && examStarted.value) {
    // 用户切换走了
    violationCount.value++
    showViolationWarning.value = true

    // 3秒后自动隐藏警告
    if (violationTimer) clearTimeout(violationTimer)
    violationTimer = setTimeout(() => {
      showViolationWarning.value = false
    }, 3000)

    // 立即保存违规次数
    if (attemptId.value) {
      saveExamAttempt(attemptId.value, formatAnswers(), violationCount.value)
    }
  }
}

function formatAnswers() {
  return Object.entries(answers.value).map(([question_id, answer]) => ({
    question_id,
    answer,
  }))
}

async function handleStart() {
  try {
    const res = await startExam(route.params.id)
    if (res.code === 0) {
      examStarted.value = true
      attemptId.value = res.data.attempt_id
      questions.value = res.data.questions
      timeRemaining.value = Math.floor(
        (new Date(res.data.deadline) - new Date()) / 1000
      )

      startTimer()
    }
  } catch (error) {
    ElMessage.error(error.message || '开始考试失败')
  }
}

function startTimer() {
  timer.value = setInterval(() => {
    timeRemaining.value--

    if (timeRemaining.value <= 0) {
      handleSubmit()
    }
  }, 1000)
}

async function handleSave() {
  try {
    await saveExamAttempt(attemptId.value, formatAnswers())
    ElMessage.success('保存成功')
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

async function handleSubmit() {
  try {
    await ElMessageBox.confirm('确定要提交试卷吗？提交后将无法修改答案。', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }

  try {
    const res = await submitExam(attemptId.value, formatAnswers(), violationCount.value)
    if (res.code === 0) {
      result.value = res.data
      showResult.value = true
    }
  } catch (error) {
    ElMessage.error('提交失败')
  }
}

function handleBack() {
  if (examInfo.value?.project_id) {
    router.push(`/training/${examInfo.value.project_id}`)
  } else {
    router.push('/exam-history')
  }
}

onMounted(async () => {
  const res = await getExamDetail(route.params.id)
  if (res.code === 0) {
    examInfo.value = res.data
  } else {
    ElMessage.error('考试不存在或已删除')
    router.push('/exam-history')
  }

  // 注册标签页切换检测
  document.addEventListener('visibilitychange', handleVisibilityChange)
})

onUnmounted(() => {
  if (timer.value) clearInterval(timer.value)
  if (violationTimer) clearTimeout(violationTimer)
  document.removeEventListener('visibilitychange', handleVisibilityChange)
})
</script>

<style scoped>
.exam-page {
  max-width: 800px;
}

.back-btn {
  margin-bottom: 20px;
}

.violation-warning {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: #fff2f0;
  border: 1px solid #ffa39e;
  border-radius: 8px;
  padding: 12px 20px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #f56c6c;
  font-size: 14px;
  z-index: 9999;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  animation: slideDown 0.3s ease;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
}

.exam-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.exam-header h2 {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
}

.timer {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 20px;
  font-weight: 600;
  color: #409eff;
}

.time-warning {
  color: #f56c6c;
}

.questions-list {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.question-item {
  padding: 20px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
}

.question-item.answered {
  border-color: #67c23a;
  background: #f0f9eb;
}

.question-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.question-index {
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

.question-type {
  font-size: 12px;
  color: #909399;
}

.question-score {
  margin-left: auto;
  font-size: 12px;
  color: #f56c6c;
}

.question-text {
  font-size: 14px;
  color: #303133;
  margin: 0 0 16px;
  line-height: 1.6;
}

.exam-footer {
  margin-top: 24px;
  display: flex;
  justify-content: center;
  gap: 16px;
}

.start-card {
  text-align: center;
}

.start-info h2 {
  font-size: 24px;
  font-weight: 600;
  margin: 0 0 16px;
}

.start-info > p {
  color: #606266;
  margin: 0 0 20px;
}

.exam-meta {
  display: flex;
  justify-content: center;
  gap: 40px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.meta-item {
  text-align: center;
}

.meta-item .label {
  display: block;
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.meta-item .value {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.rules-list {
  margin: 0;
  padding-left: 20px;
  text-align: left;
}

.rules-list li {
  margin: 4px 0;
}

.result-content {
  text-align: center;
}

.result-score {
  font-size: 64px;
  font-weight: 700;
  color: #f56c6c;
  margin-bottom: 16px;
}

.result-score.pass {
  color: #67c23a;
}

.result-status {
  font-size: 18px;
  color: #606266;
  margin: 0 0 24px;
}
</style>