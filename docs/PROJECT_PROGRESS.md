# 企业内部员工培训平台 - 项目进度说明

## 一、项目概述

**项目名称**：企业内部员工培训平台
**技术栈**：Vue 3 + FastAPI + MySQL
**版本**：v1.0

---

## 二、已完成的功能模块

### 2.1 认证与权限

| 功能 | 状态 | 说明 |
|------|------|------|
| 用户登录 | ✅ 完成 | JWT Token 认证，支持刷新令牌 |
| 用户登出 | ✅ 完成 | 清除本地 Token |
| Token 自动刷新 | ✅ 完成 | 请求拦截器自动处理 |
| 登录过期处理 | ✅ 完成 | 401 时跳转登录页 |

**API 端点**：
- `POST /v1/auth/login` - 用户登录
- `POST /v1/auth/logout` - 用户登出
- `POST /v1/auth/refresh` - 刷新 Token

---

### 2.2 员工端功能

#### 2.2.1 培训列表
| 功能 | 状态 | 说明 |
|------|------|------|
| 培训项目列表 | ✅ 完成 | 展示所有已发布的培训项目 |
| 搜索培训 | ✅ 完成 | 按标题关键字搜索 |
| 状态筛选 | ✅ 完成 | 按状态筛选（全部/必修/选修） |

**页面**：`/training` → `TrainingList.vue`

#### 2.2.2 培训详情
| 功能 | 状态 | 说明 |
|------|------|------|
| 项目信息展示 | ✅ 完成 | 标题、描述、封面、截止日期等 |
| 材料列表展示 | ✅ 完成 | 视频/文档分类显示 |
| 学习进度显示 | ✅ 完成 | 百分比 + 状态 |
| 考试入口 | ✅ 完成 | 完所有材料后解锁 |
| 学员讨论区 | 🔄 开发中 | 评论发表功能 |

**页面**：`/training/:id` → `TrainingDetail.vue`

#### 2.2.3 视频学习
| 功能 | 状态 | 说明 |
|------|------|------|
| 视频播放 | ✅ 完成 | 支持 mp4/avi/mov/wmv |
| 断点续播 | ✅ 完成 | 暂停后保存进度 |
| 播放进度保存 | ✅ 完成 | 自动保存 + 手动保存 |
| 防作弊机制 | ✅ 完成 | 禁止快进、禁止跳过 |
| 全屏播放 | ✅ 完成 | 支持全屏模式 |
| 视频时长更新 | ✅ 完成 | 自动提取并更新时长 |

**学习规则**：
- 未看完的视频：必须从上次位置继续观看，不能从头开始
- 已看完的视频：可以重新观看（不占学习时长）
- 视频播放完毕（95%+）标记为已完成

**页面**：`/training/:id/material/:materialId` → `MaterialPlayer.vue`

#### 2.2.4 文档学习
| 功能 | 状态 | 说明 |
|------|------|------|
| PDF 预览 | ✅ 完成 | iframe 内嵌显示 |
| 水印功能 | ✅ 完成 | 显示用户名+日期防泄密 |
| 完成标记 | ✅ 完成 | "我已阅读"按钮标记完成 |

#### 2.2.5 考试功能
| 功能 | 状态 | 说明 |
|------|------|------|
| 考试答题 | ✅ 完成 | 单选/多选/判断题 |
| 答题自动保存 | ✅ 完成 | 每题自动保存 |
| 考试提交 | ✅ 完成 | 交卷后显示成绩 |
| 考试历史 | ✅ 完成 | 查看历史成绩 |

**页面**：`/exam/:projectId` → `ExamPage.vue`
**历史页面**：`/exam/history` → `ExamHistory.vue`

#### 2.2.6 消息通知
| 功能 | 状态 | 说明 |
|------|------|------|
| 通知列表 | ✅ 完成 | 展示系统通知 |
| 通知详情 | ✅ 完成 | 查看通知内容 |
| 已读标记 | ✅ 完成 | 标记单条/全部已读 |

**页面**：`/notification` → `Notification.vue`

#### 2.2.7 个人中心
| 功能 | 状态 | 说明 |
|------|------|------|
| 个人信息 | ✅ 完成 | 显示用户信息 |
| 学习统计 | ✅ 完成 | 培训数量、时长统计 |

**页面**：`/dashboard` → `Dashboard.vue`

---

### 2.3 HR 管理端功能

#### 2.3.1 培训项目管理
| 功能 | 状态 | 说明 |
|------|------|------|
| 项目列表 | ✅ 完成 | 查看所有项目（含草稿） |
| 创建项目 | ✅ 完成 | 填写基本信息 |
| 编辑项目 | ✅ 完成 | 修改草稿项目 |
| 发布项目 | ✅ 完成 | 发布前检查材料数量 |
| 下架项目 | ✅ 完成 | 已发布项目可下架 |
| 删除项目 | ✅ 完成 | 仅可删除草稿项目 |

**页面**：`/hr/training` → `TrainingManage.vue`
**创建页面**：`/hr/training/create` → `TrainingCreate.vue`

#### 2.3.2 教材上传
| 功能 | 状态 | 说明 |
|------|------|------|
| 上传视频 | ✅ 完成 | 支持 mp4/avi/mov/wmv，最大 2GB |
| 上传文档 | ✅ 完成 | 支持 pdf/doc/docx，最大 100MB |
| 视频时长提取 | ✅ 完成 | 使用 ffprobe 自动提取 |
| 文件大小验证 | ✅ 完成 | 前端+后端双重验证 |

**页面**：`/hr/training/:id/material/upload` → `MaterialUpload.vue`

#### 2.3.3 学习进度管理
| 功能 | 状态 | 说明 |
|------|------|------|
| 部门进度统计 | ✅ 完成 | 按部门查看学习进度 |
| 导出进度报告 | ✅ 完成 | Excel 格式导出 |
| 图表统计 | ✅ 完成 | 完成率、趋势图 |

**页面**：`/hr/progress/:projectId` → `ProgressReport.vue`

#### 2.3.4 部门管理
| 功能 | 状态 | 说明 |
|------|------|------|
| 部门列表 | ✅ 完成 | 树形结构展示 |
| 添加部门 | ✅ 完成 | 支持子部门 |
| 编辑部门 | ✅ 完成 | 修改部门信息 |
| 删除部门 | ✅ 完成 | 需确认无员工 |
| 导入部门 | 🔄 开发中 | Excel 批量导入 |

**页面**：`/hr/department` → `DepartmentManage.vue`

#### 2.3.5 考试管理
| 功能 | 状态 | 说明 |
|------|------|------|
| 创建考试 | ✅ 完成 | 关联培训项目 |
| 编辑题目 | ✅ 完成 | 单选/多选/判断 |
| 题目管理 | ✅ 完成 | 增删改题目 |

**页面**：`/hr/exam/:examId` → `ExamEditor.vue`

#### 2.3.6 通知管理
| 功能 | 状态 | 说明 |
|------|------|------|
| 发送通知 | ✅ 完成 | 选择发送对象 |
| 通知历史 | ✅ 完成 | 查看已发送通知 |

**页面**：`/hr/notification` → `Notification.vue`

#### 2.3.7 系统设置
| 功能 | 状态 | 说明 |
|------|------|------|
| 基本设置 | ✅ 完成 | 平台名称、Logo 等 |
| 邮件测试 | 🔄 待接入 | 邮件发送测试 |

**页面**：`/hr/settings` → `Settings.vue`

---

## 三、数据统计

### 3.1 后端 API 统计

| 模块 | 端点数量 | 说明 |
|------|---------|------|
| 认证 auth | 3 | 登录/登出/刷新 |
| 用户 user | 3 | 个人信息/统计/列表 |
| 部门 department | 7 | CRUD + 导入 |
| 培训 training | 7 | 项目管理 + 发布 |
| 材料 material | 4 | 上传/播放/删除/时长 |
| 进度 progress | 4 | 学习进度/导出/统计 |
| 考试 exam | 7 | 考试/答题/历史 |
| 评论 comment | 3 | 查看/发表/删除 |
| 通知 notification | 5 | 发送/列表/已读 |
| 系统设置 | 3 | 获取/更新/测试 |

**总计**：46 个 API 端点

---

## 四、数据库模型

### 4.1 核心表结构

| 表名 | 说明 | 主要字段 |
|------|------|---------|
| sys_user | 用户表 | user_id, username, real_name, role, dept_id |
| sys_department | 部门表 | dept_id, dept_name, parent_id |
| tra_project | 培训项目表 | project_id, title, status, deadline, is_required |
| tra_material | 教材表 | material_id, project_id, title, type, duration, storage_path |
| tra_watch_progress | 观看进度表 | record_id, user_id, material_id, max_position, total_watched_seconds |
| tra_exam | 考试表 | exam_id, project_id, title, passing_score |
| tra_exam_question | 考题表 | question_id, exam_id, type, content, options |
| tra_exam_attempt | 考试记录表 | attempt_id, exam_id, user_id, score, status |
| tra_progress | 项目进度表 | progress_id, user_id, project_id, overall_status |
| tra_comment | 评论表 | comment_id, project_id, user_id, content |
| tra_notification | 通知表 | notif_id, user_id, title, content, is_read |

---

## 五、前端页面结构

```
src/views/
├── auth/
│   └── Login.vue              # 登录页
├── employee/                 # 员工端
│   ├── Dashboard.vue         # 个人中心
│   ├── TrainingList.vue      # 培训列表
│   ├── TrainingDetail.vue     # 培训详情
│   ├── MaterialPlayer.vue     # 视频/文档播放器
│   ├── ExamPage.vue          # 考试页面
│   ├── ExamHistory.vue       # 考试历史
│   └── Notification.vue     # 消息通知
└── hr/                      # HR管理端
    ├── DefaultLayout.vue     # 管理后台布局
    ├── Dashboard.vue         # 数据统计
    ├── TrainingManage.vue    # 培训项目管理
    ├── TrainingCreate.vue    # 创建培训项目
    ├── MaterialUpload.vue    # 教材上传
    ├── ProgressReport.vue    # 进度报表
    ├── DepartmentManage.vue  # 部门管理
    ├── ExamEditor.vue       # 考试编辑器
    ├── Notification.vue      # 通知管理
    └── Settings.vue          # 系统设置
```

---

## 六、待优化功能

| 功能 | 优先级 | 说明 |
|------|--------|------|
| 评论功能 | 中 | 员工端评论显示/发表 |
| 部门导入 | 低 | Excel 批量导入部门 |
| 邮件通知 | 低 | 培训发布/截止提醒 |
| 视频加密 | 中 | DRM 数字版权管理 |
| 播放记录导出 | 低 | 员工观看的详细记录 |

---

## 七、已知问题

1. **视频时长**：已上传的视频需重新播放才能更新时长
2. **评论功能**：HR 管理端评论管理未完成
3. **多标签页**：同一视频在多标签页同时播放可能冲突

---

## 八、测试账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| HR 管理员 | admin | admin123 |
| 员工 | employee1 | emp123 |

---

*文档更新时间：2026-05-11*
