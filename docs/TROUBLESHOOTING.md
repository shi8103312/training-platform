# 问题排查记录

## 1. 通知中心页面空白

**问题**: 访问 `/notifications` 页面无内容

**原因**:
- 路由路径错误，实际路径是 `/notification`（无 's'）
- 布局组件 `DefaultLayout.vue` 中的链接写的是 `/notifications`

**解决方案**:
- 修改 `frontend/src/layouts/DefaultLayout.vue`，将 `to="/notifications"` 改为 `to="/notification"`

---

## 2. 考试历史页面空白

**问题**: 访问 `/exam-history` 页面无内容

**原因**: 路由未注册

**解决方案**:
- 在 `frontend/src/router/index.js` 中添加路由：
```javascript
{
  path: 'exam-history',
  name: 'ExamHistory',
  component: () => import('@/views/employee/ExamHistory.vue'),
}
```

---

## 3. 铃铛图标无法点击

**问题**: 右上角通知铃铛无点击事件，显示未读数固定为 3

**原因**: 缺少点击事件处理和动态未读数

**解决方案**:
- 添加 `goToNotification` 函数跳转通知中心
- 调用 `getMyNotifications` API 获取真实未读数
- 仅在有未读消息时显示 badge

---

## 4. 标记已读功能报错"资源不存在"

**问题**: 点击通知的"标为已读"按钮报错

**原因**: 后端缺少 `PUT /v1/notification/{notif_id}/read` 接口

**解决方案**:
- 在 `backend/app/api/v1/notification.py` 添加接口：
```python
@router.put("/{notif_id}/read")
async def mark_notification_read(notif_id: str, ...):
    # 标记通知为已读
```

---

## 5. 学习报表页面空白

**问题**: 访问 `/hr/progress` 页面无内容

**原因**: 路由定义为 `progress/:id`，需要必填的项目 ID 参数

**解决方案**:
- 修改路由为 `progress`（不带 `:id`），项目 ID 作为可选筛选条件

---

## 6. 培训项目创建失败 (CORS Error)

**问题**: 点击"创建"按钮报 CORS 错误 `No 'Access-Control-Allow-Origin' header`

**原因**:
- `.env` 配置 `VITE_API_BASE_URL=http://localhost:8002/api` 指向错误端口
- 实际后端运行在 8000 端口

**解决方案**:
- 修改 `frontend/.env`：`VITE_API_BASE_URL=http://localhost:8000/api`
- 重启前端服务

---

## 7. 培训项目创建失败 (500 Error)

**问题**: API 返回 500 错误，后端日志显示 `TypeError: can't compare offset-naive and offset-aware datetimes`

**原因**: `deadline` 字段验证器中时区比较问题

**错误代码**:
```python
@field_validator("deadline")
@classmethod
def validate_deadline(cls, v):
    now = datetime.now()  # naive datetime
    if v.tzinfo is not None:
        v = v.replace(tzinfo=None)  # converted to naive
    if v <= now:  # 比较失败
        raise ValueError("截止日期必须晚于当前时间")
```

**解决方案**:
```python
from datetime import datetime, timezone

@field_validator("deadline")
@classmethod
def validate_deadline(cls, v):
    now = datetime.now(timezone.utc)
    if v.tzinfo is None:
        v = v.replace(tzinfo=timezone.utc)
    if v <= now:
        raise ValueError("截止日期必须晚于当前时间")
    return v
```

**注意**: 需要完整重启后端服务（杀死所有 uvicorn 进程后重新启动）

---

## 8. 文档材料无法标记完成

**问题**: 文档类材料无法像视频一样自动完成学习

**原因**:
- 视频通过 `saveProgress` 函数跟踪播放进度，95% 后自动完成
- 文档没有计时逻辑，`max_position` 不会更新

**解决方案**:
- 在文档播放器添加"我已阅读"按钮
- 点击后调用 `saveVideoProgress` 设置 `max_position=600`（10分钟）来标记完成

---

## 9. 培训详情页视频计数错误

**问题**: 视频和文档数量显示不正确

**原因**: 代码使用 `materials.length` 显示视频数量，但材料包含视频和文档两种类型

**解决方案**:
```javascript
const videoCount = computed(() => {
  return materials.value.filter(m => m.is_video).length
})

const docCount = computed(() => {
  return materials.value.filter(m => !m.is_video).length
})
```

---

## 10. 保存视频进度报错 422

**问题**: 视频播放时保存进度报 422 验证错误

**原因**: 页面卸载时 `onUnmounted` 调用 `saveProgress`，但此时视频元素已不存在，导致 `videoRef.value?.currentTime` 返回 `undefined`

**解决方案**:
```javascript
async function saveProgress() {
  if (!material.value) return
  // 仅对视频材料保存进度
  if (material.value.material_type !== 1) return

  const videoEl = videoRef.value
  if (!videoEl) return

  const position = Math.floor(videoEl.currentTime || 0)
  // ...
}
```

---

## 关键配置信息

### 测试账号
| 角色 | 用户名 | 密码 |
|------|--------|------|
| HR管理员 | admin | admin123 |
| 员工 | zhangsan | 123456 |
| 员工 | lisi | 123456 |

### 服务端口
| 服务 | 端口 |
|------|------|
| 前端 (Vite) | 5173 |
| 后端 (FastAPI) | 8000 |
| MySQL | 3306 |
| Redis | 6379 |

### API 基础路径
- 开发环境: `http://localhost:8000/api`
- 前端代理: `/api` -> `http://localhost:8000`

---

## 预防措施建议

1. **时区处理**: 所有 datetime 比较统一使用 UTC 时区
2. **端口配置**: 环境变量文件 `.env` 需版本控制或提供 `.env.example`
3. **路由注册**: 新增页面后及时注册路由
4. **空值检查**: 操作 DOM 元素前检查元素是否存在
5. **类型区分**: 不同类型材料使用不同处理逻辑
