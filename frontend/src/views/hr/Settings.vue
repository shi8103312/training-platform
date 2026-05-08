<template>
  <div class="hr-settings">
    <div class="settings-layout">
      <!-- 设置导航 -->
      <div class="settings-tabs">
        <div class="settings-tab" :class="{ active: activeTab === 'general' }" @click="activeTab = 'general'">
          <span class="icon">🏠</span>
          <span>常规设置</span>
        </div>
        <div class="settings-tab" :class="{ active: activeTab === 'email' }" @click="activeTab = 'email'">
          <span class="icon">✉️</span>
          <span>邮件设置</span>
        </div>
        <div class="settings-tab" :class="{ active: activeTab === 'security' }" @click="activeTab = 'security'">
          <span class="icon">🔒</span>
          <span>安全设置</span>
        </div>
        <div class="settings-tab" :class="{ active: activeTab === 'video' }" @click="activeTab = 'video'">
          <span class="icon">🎬</span>
          <span>视频设置</span>
        </div>
        <div class="settings-tab" :class="{ active: activeTab === 'notification' }" @click="activeTab = 'notification'">
          <span class="icon">🔔</span>
          <span>通知设置</span>
        </div>
      </div>

      <!-- 设置内容 -->
      <div class="settings-content">
        <!-- 常规设置 -->
        <div v-if="activeTab === 'general'">
          <div class="settings-title">🏠 常规设置</div>

          <div class="form-item">
            <label>平台名称</label>
            <input type="text" v-model="settings.platformName" placeholder="请输入平台名称" />
          </div>

          <div class="form-item">
            <label>平台Logo</label>
            <div style="display: flex; align-items: center; gap: 15px">
              <div class="logo-preview">🏢</div>
              <button class="btn btn-outline">上传Logo</button>
            </div>
            <div class="hint">建议尺寸 200x200，支持 JPG、PNG，建议白色背景</div>
          </div>

          <div class="form-item">
            <label>版权信息</label>
            <input type="text" v-model="settings.copyright" placeholder="请输入版权信息" />
          </div>

          <div class="form-item">
            <label>时区设置</label>
            <select v-model="settings.timezone">
              <option value="Asia/Shanghai">中国标准时间 (Asia/Shanghai)</option>
              <option value="UTC">UTC</option>
            </select>
          </div>
        </div>

        <!-- 邮件设置 -->
        <div v-if="activeTab === 'email'">
          <div class="settings-title">✉️ 邮件设置</div>

          <div class="info-box">
            <div class="title">💡 配置说明</div>
            <div class="content">
              配置集团自有邮箱服务器(SMTP)用于发送培训通知邮件。请确保SMTP服务已开启并正确配置。
            </div>
          </div>

          <div class="form-item">
            <label>SMTP服务器地址</label>
            <input type="text" v-model="settings.smtp.host" placeholder="smtp.company.com" />
          </div>

          <div class="form-item">
            <label>SMTP端口</label>
            <input type="text" v-model="settings.smtp.port" placeholder="465" />
            <div class="hint">SSL端口通常为465，非SSL端口为25</div>
          </div>

          <div class="form-item">
            <label>发件人邮箱</label>
            <input type="email" v-model="settings.smtp.from" placeholder="training@company.com" />
          </div>

          <div class="form-item">
            <label>邮箱账号</label>
            <input type="text" v-model="settings.smtp.username" placeholder="请输入邮箱账号" />
          </div>

          <div class="form-item">
            <label>邮箱密码 <span class="sub">（授权密码，非登录密码）</span></label>
            <input type="password" v-model="settings.smtp.password" placeholder="请输入授权密码" />
          </div>

          <div class="form-item">
            <label>测试收件人邮箱</label>
            <div class="input-group">
              <input type="email" v-model="settings.testEmail" placeholder="用于测试邮件配置" />
              <button class="test-btn" @click="handleTestEmailConfig">发送测试邮件</button>
            </div>
          </div>
        </div>

        <!-- 安全设置 -->
        <div v-if="activeTab === 'security'">
          <div class="settings-title">🔒 安全设置</div>

          <div class="switch-item">
            <div class="info">
              <div class="title">强制修改初始密码</div>
              <div class="desc">员工首次登录后必须修改初始密码</div>
            </div>
            <label class="switch">
              <input type="checkbox" v-model="settings.security.forcePasswordChange" />
              <span class="slider"></span>
            </label>
          </div>

          <div class="switch-item">
            <div class="info">
              <div class="title">登录失败锁定</div>
              <div class="desc">连续5次登录失败后锁定账号15分钟</div>
            </div>
            <label class="switch">
              <input type="checkbox" v-model="settings.security.loginLockout" />
              <span class="slider"></span>
            </label>
          </div>

          <div class="switch-item">
            <div class="info">
              <div class="title">密码复杂度要求</div>
              <div class="desc">密码必须包含大小写字母、数字和特殊字符</div>
            </div>
            <label class="switch">
              <input type="checkbox" v-model="settings.security.passwordComplexity" />
              <span class="slider"></span>
            </label>
          </div>

          <div class="switch-item">
            <div class="info">
              <div class="title">录屏检测</div>
              <div class="desc">启用后检测到录屏行为将弹出警告</div>
            </div>
            <label class="switch">
              <input type="checkbox" v-model="settings.security.screenRecordDetection" />
              <span class="slider"></span>
            </label>
          </div>

          <div class="form-item" style="margin-top: 20px">
            <label>JWT Token有效期</label>
            <div class="input-group">
              <input type="number" v-model="settings.security.tokenExpiry" style="width: 100px" />
              <span class="unit">分钟</span>
            </div>
            <div class="hint">建议设置为30分钟</div>
          </div>
        </div>

        <!-- 视频设置 -->
        <div v-if="activeTab === 'video'">
          <div class="settings-title">🎬 视频设置</div>

          <div class="form-item">
            <label>允许上传的视频格式</label>
            <input type="text" v-model="settings.video.allowedFormats" placeholder="mp4,avi,mov,wmv" />
            <div class="hint">多个格式用逗号分隔</div>
          </div>

          <div class="form-item">
            <label>单个视频最大大小</label>
            <div class="input-group">
              <input type="number" v-model="settings.video.maxSize" style="width: 100px" />
              <span class="unit">MB</span>
            </div>
            <div class="hint">建议不超过2GB</div>
          </div>

          <div class="form-item">
            <label>视频转码分辨率</label>
            <select v-model="settings.video.transcodeResolution">
              <option value="1080p">1080p (全高清)</option>
              <option value="720p">720p (高清)</option>
              <option value="480p">480p (标清)</option>
            </select>
          </div>

          <div class="switch-item">
            <div class="info">
              <div class="title">启用AES-128加密</div>
              <div class="desc">视频内容加密存储，防止直接下载</div>
            </div>
            <label class="switch">
              <input type="checkbox" v-model="settings.video.encryption" />
              <span class="slider"></span>
            </label>
          </div>

          <div class="switch-item">
            <div class="info">
              <div class="title">视频水印</div>
              <div class="desc">在视频右下角添加平台水印</div>
            </div>
            <label class="switch">
              <input type="checkbox" v-model="settings.video.watermark" />
              <span class="slider"></span>
            </label>
          </div>
        </div>

        <!-- 通知设置 -->
        <div v-if="activeTab === 'notification'">
          <div class="settings-title">🔔 通知设置</div>

          <div class="switch-item">
            <div class="info">
              <div class="title">培训开始提醒</div>
              <div class="desc">培训发布时自动发送邮件通知</div>
            </div>
            <label class="switch">
              <input type="checkbox" v-model="settings.notification.trainingStart" />
              <span class="slider"></span>
            </label>
          </div>

          <div class="switch-item">
            <div class="info">
              <div class="title">截止日期提醒</div>
              <div class="desc">培训截止前3天、1天，当天发送提醒</div>
            </div>
            <label class="switch">
              <input type="checkbox" v-model="settings.notification.deadlineReminder" />
              <span class="slider"></span>
            </label>
          </div>

          <div class="switch-item">
            <div class="info">
              <div class="title">培训完成提醒</div>
              <div class="desc">员工完成培训后发送确认邮件</div>
            </div>
            <label class="switch">
              <input type="checkbox" v-model="settings.notification.trainingComplete" />
              <span class="slider"></span>
            </label>
          </div>

          <div class="switch-item">
            <div class="info">
              <div class="title">考试结果通知</div>
              <div class="desc">员工考试结束后发送成绩通知</div>
            </div>
            <label class="switch">
              <input type="checkbox" v-model="settings.notification.examResult" />
              <span class="slider"></span>
            </label>
          </div>
        </div>

        <!-- 保存按钮 -->
        <div class="action-bar">
          <button class="btn btn-outline">恢复默认</button>
          <button class="btn btn-primary" @click="saveSettings">💾 保存设置</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getSettings, updateSettings, testEmailConfig as testEmailApi } from '@/api/settings'

const activeTab = ref('general')
const loading = ref(false)

const settings = reactive({
  platformName: '集团内部培训平台',
  copyright: '© 2026 某某集团 版权所有',
  timezone: 'Asia/Shanghai',
  testEmail: '',

  smtp: {
    host: 'smtp.company.com',
    port: '465',
    from: 'training@company.com',
    username: '',
    password: '',
  },

  security: {
    forcePasswordChange: true,
    loginLockout: true,
    passwordComplexity: true,
    screenRecordDetection: true,
    tokenExpiry: 30,
  },

  video: {
    allowedFormats: 'mp4,avi,mov,wmv',
    maxSize: 2048,
    transcodeResolution: '1080p',
    encryption: true,
    watermark: false,
  },

  notification: {
    trainingStart: true,
    deadlineReminder: true,
    trainingComplete: true,
    examResult: true,
  },
})

async function fetchSettings() {
  loading.value = true
  try {
    const res = await getSettings()
    if (res.code === 0) {
      const data = res.data || {}
      settings.platformName = data.platform_name || '集团内部培训平台'
      settings.copyright = data.copyright || '© 2026 某某集团 版权所有'
      settings.timezone = data.timezone || 'Asia/Shanghai'
      settings.smtp.host = data.smtp_host || 'smtp.company.com'
      settings.smtp.port = data.smtp_port || '465'
      settings.smtp.from = data.smtp_from || 'training@company.com'
      settings.smtp.username = data.smtp_username || ''
      settings.smtp.password = data.smtp_password || ''
      settings.security.forcePasswordChange = data.security_force_password_change ?? true
      settings.security.loginLockout = data.security_login_lockout ?? true
      settings.security.passwordComplexity = data.security_password_complexity ?? true
      settings.security.screenRecordDetection = data.security_screen_record_detection ?? true
      settings.security.tokenExpiry = data.security_token_expiry || 30
      settings.video.allowedFormats = data.video_allowed_formats || 'mp4,avi,mov,wmv'
      settings.video.maxSize = data.video_max_size || 2048
      settings.video.transcodeResolution = data.video_transcode_resolution || '1080p'
      settings.video.encryption = data.video_encryption ?? true
      settings.video.watermark = data.video_watermark ?? false
      settings.notification.trainingStart = data.notif_training_start ?? true
      settings.notification.deadlineReminder = data.notif_deadline_reminder ?? true
      settings.notification.trainingComplete = data.notif_training_complete ?? true
      settings.notification.examResult = data.notif_exam_result ?? true
    }
  } catch (error) {
    console.error('Failed to fetch settings:', error)
  } finally {
    loading.value = false
  }
}

async function saveSettings() {
  try {
    const data = {
      platform_name: settings.platformName,
      copyright: settings.copyright,
      timezone: settings.timezone,
      smtp_host: settings.smtp.host,
      smtp_port: settings.smtp.port,
      smtp_from: settings.smtp.from,
      smtp_username: settings.smtp.username,
      smtp_password: settings.smtp.password,
      security_force_password_change: settings.security.forcePasswordChange,
      security_login_lockout: settings.security.loginLockout,
      security_password_complexity: settings.security.passwordComplexity,
      security_screen_record_detection: settings.security.screenRecordDetection,
      security_token_expiry: settings.security.tokenExpiry,
      video_allowed_formats: settings.video.allowedFormats,
      video_max_size: settings.video.maxSize,
      video_transcode_resolution: settings.video.transcodeResolution,
      video_encryption: settings.video.encryption,
      video_watermark: settings.video.watermark,
      notif_training_start: settings.notification.trainingStart,
      notif_deadline_reminder: settings.notification.deadlineReminder,
      notif_training_complete: settings.notification.trainingComplete,
      notif_exam_result: settings.notification.examResult,
    }

    const res = await updateSettings(data)
    if (res.code === 0) {
      ElMessage.success('设置保存成功！')
    } else {
      ElMessage.error(res.message || '保存失败')
    }
  } catch (error) {
    ElMessage.error('保存失败')
    console.error('Failed to save settings:', error)
  }
}

async function handleTestEmailConfig() {
  if (!settings.testEmail) {
    ElMessage.warning('请输入测试收件人邮箱')
    return
  }
  try {
    const res = await testEmailApi(settings.testEmail)
    if (res.code === 0) {
      ElMessage.success(res.message || '测试邮件已发送，请查收！')
    } else {
      ElMessage.error(res.message || '发送失败')
    }
  } catch (error) {
    ElMessage.error('发送失败')
    console.error('Failed to send test email:', error)
  }
}

onMounted(() => {
  fetchSettings()
})
</script>

<style scoped>
.hr-settings {
  font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
}

.settings-layout {
  display: grid;
  grid-template-columns: 220px 1fr;
  gap: 25px;
}

.settings-tabs {
  background: #fff;
  border-radius: 10px;
  padding: 15px 0;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.settings-tab {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 14px;
  color: #666;
}

.settings-tab:hover {
  background: #f5f7fa;
  color: #333;
}

.settings-tab.active {
  background: #e6f0ff;
  color: #667eea;
  border-left: 3px solid #667eea;
}

.settings-tab .icon {
  font-size: 16px;
}

.settings-content {
  background: #fff;
  border-radius: 10px;
  padding: 30px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.settings-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin-bottom: 25px;
  padding-bottom: 15px;
  border-bottom: 1px solid #f0f0f0;
}

.form-item {
  margin-bottom: 25px;
}

.form-item label {
  display: block;
  font-size: 14px;
  color: #333;
  margin-bottom: 8px;
  font-weight: 500;
}

.form-item label .sub {
  font-weight: normal;
  color: #999;
  font-size: 12px;
  margin-left: 8px;
}

.form-item input,
.form-item select,
.form-item textarea {
  width: 100%;
  max-width: 500px;
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
  border-color: #667eea;
}

.form-item .hint {
  font-size: 12px;
  color: #999;
  margin-top: 6px;
}

.logo-preview {
  width: 80px;
  height: 80px;
  background: #f5f7fa;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
}

.input-group {
  display: flex;
  gap: 10px;
  align-items: center;
}

.input-group input {
  flex: 1;
}

.input-group .unit {
  font-size: 14px;
  color: #666;
}

.switch-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 15px 0;
  border-bottom: 1px solid #f5f7fa;
}

.switch-item:last-child {
  border-bottom: none;
}

.switch-item .info .title {
  font-size: 14px;
  color: #333;
  margin-bottom: 4px;
}

.switch-item .info .desc {
  font-size: 12px;
  color: #999;
}

/* 开关样式 */
.switch {
  position: relative;
  width: 48px;
  height: 24px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: 0.3s;
  border-radius: 24px;
}

.slider:before {
  position: absolute;
  content: '';
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: 0.3s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: #667eea;
}

input:checked + .slider:before {
  transform: translateX(24px);
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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.btn-outline {
  background: #fff;
  color: #667eea;
  border: 1px solid #667eea;
}

.btn-outline:hover {
  background: #f5f7ff;
}

.action-bar {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  gap: 15px;
}

.info-box {
  background: #f8f8ff;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 20px;
}

.info-box .title {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 8px;
}

.info-box .content {
  font-size: 13px;
  color: #666;
  line-height: 1.6;
}

.test-btn {
  background: #f5f7fa;
  color: #667eea;
  border: 1px solid #dcdfe6;
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
}

.test-btn:hover {
  background: #e6f0ff;
}
</style>
