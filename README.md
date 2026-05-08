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

## 项目结构

```
training-platform/
├── frontend/          # Vue 3 前端
├── backend/          # FastAPI 后端
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

- 用户认证 (JWT)
- 培训项目管理
- 视频/文档材料上传
- 学习进度追踪
- 在线考试
- 部门管理
- 培训通知

## API 文档

启动后端服务后访问: http://localhost:8000/docs