# 集团内部员工培训平台

基于 Vue 3 + FastAPI 的集团内部员工培训平台。

## 技术栈

### 前端
- Vue 3 + Composition API
- Vite 5
- Element Plus
- Pinia (状态管理)
- Vue Router

### 后端
- Python FastAPI
- SQLAlchemy 2.0
- MySQL 8.0
- Redis
- 限流 (slowapi)

## 项目结构

```
training-platform/
├── frontend/          # Vue 3 前端
├── backend/           # FastAPI 后端
├── docker-compose.yml
└── README.md
```

## 快速开始

### 前置要求
- Node.js >= 16
- Python >= 3.9
- MySQL 8.0
- Redis

### 后端启动

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或: venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 复制环境变量
cp .env.example .env
# 编辑 .env 配置数据库连接

# 启动服务
uvicorn app.main:app --reload --port 8000
```

### 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### Docker 启动 (推荐)

```bash
docker-compose up -d
```

## 测试账号

- HR管理员: admin / admin123
- 员工: zhangsan / user123

## 主要功能

### 用户认证
- [x] 用户登录/登出
- [x] JWT 令牌认证
- [x] 记住登录状态 (7天有效)
- [x] 多账号记忆登录
- [x] 忘记密码 / 重置密码
- [x] 登录失败锁定 (5次后锁定15分钟)
- [x] API 限流保护

### 培训管理
- [x] 培训项目管理 (创建/编辑/发布)
- [x] 视频/文档材料上传
- [x] 学习进度追踪
- [x] 部门/员工管理

### 考试系统
- [x] 在线考试 (选择题/多选题/判断题)
- [x] 考试计时器
- [x] 答题自动保存
- [x] 违规行为检测 (切换标签页记录)

### 互动功能
- [x] 评论系统 (支持嵌套回复)
- [x] @提及功能 (搜索用户)
- [x] 评论点赞/取消点赞
- [x] 表情包输入
- [x] 通知系统 (已读/未读)

### 安全加固
- [x] JWT 密钥安全生成
- [x] 登录限流 (5次/分钟)
- [x] 评论限流 (10次/分钟)
- [x] CORS 跨域配置
- [x] 密码安全存储 (bcrypt)

## API 文档

启动后端服务后访问: http://localhost:8000/docs
