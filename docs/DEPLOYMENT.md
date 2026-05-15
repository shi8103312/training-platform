# 集团内部员工培训平台 - 部署手册

**版本**：v1.0
**日期**：2026-05-08

---

## 1. 系统要求

### 1.1 硬件要求

| 组件 | 最低配置 | 推荐配置 |
|------|----------|----------|
| CPU | 2核 | 4核+ |
| 内存 | 4GB | 8GB+ |
| 硬盘 | 50GB | 100GB+ SSD |
| 网络 | 带宽5Mbps | 带宽10Mbps+ |

### 1.2 软件要求

| 软件 | 版本要求 |
|------|----------|
| Docker | 20.10+ |
| Docker Compose | 2.0+ |
| MySQL | 8.0+ |
| Redis | 6.0+ |

### 1.3 网络要求

- 服务器需要开放以下端口：
  - 80 (HTTP)
  - 443 (HTTPS)
  - 5173 (前端开发服务器)
  - 8003 (后端API)

---

## 2. 部署方式

### 2.1 Docker Compose 部署（推荐）

#### 2.1.1 服务器准备

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Docker
curl -fsSL https://get.docker.com | sudo sh
sudo systemctl enable docker
sudo systemctl start docker

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### 2.1.2 项目部署

```bash
# 克隆项目
git clone https://github.com/shi8103312/training-platform.git
cd training-platform

# 配置环境变量
cp backend/.env.example backend/.env
nano backend/.env  # 编辑配置文件

# 启动服务
docker-compose up -d
```

#### 2.1.3 环境变量配置

编辑 `backend/.env` 文件：

```env
# 应用配置
APP_NAME=Training Platform
DEBUG=false

# 数据库配置
DB_HOST=mysql
DB_PORT=3306
DB_NAME=training_platform
DB_USER=root
DB_PASSWORD=your_secure_password

# Redis配置
REDIS_HOST=redis
REDIS_PORT=6379

# JWT配置（必须修改！）
JWT_SECRET_KEY=your-very-long-and-secure-secret-key-min-32-chars

# OSS配置（可选）
OSS_ENDPOINT=
OSS_ACCESS_KEY=
OSS_SECRET_KEY=
OSS_BUCKET=

# SMTP配置（可选）
SMTP_HOST=smtp.company.com
SMTP_PORT=465
SMTP_USER=notifications@company.com
SMTP_PASSWORD=your_smtp_password
SMTP_FROM=notifications@company.com
```

### 2.2 传统部署

#### 2.2.1 后端部署

```bash
# 安装 Python 3.9+
sudo apt install python3.9 python3.9-venv python3-pip

# 创建虚拟环境
cd backend
python3.9 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python -c "from app.database import init_db; init_db()"

# 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8003 --workers 4
```

#### 2.2.2 前端部署

```bash
# 安装 Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# 安装依赖
cd frontend
npm install

# 构建生产版本
npm run build

# 使用 Nginx 部署
sudo cp -r dist /var/www/training-platform
sudo nano /etc/nginx/sites-available/training-platform
```

#### 2.2.3 Nginx 配置

```nginx
server {
    listen 80;
    server_name training.company.com;

    root /var/www/training-platform;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://127.0.0.1:8003;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 3. HTTPS 配置

### 3.1 Let's Encrypt 免费证书

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d training.company.com

# 自动续期测试
sudo certbot renew --dry-run
```

### 3.2 Nginx HTTPS 配置

```nginx
server {
    listen 443 ssl http2;
    server_name training.company.com;

    ssl_certificate /etc/letsencrypt/live/training.company.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/training.company.com/privkey.pem;

    # SSL 安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # 其他配置...
}
```

---

## 4. 数据库初始化

### 4.1 创建数据库

```sql
CREATE DATABASE IF NOT EXISTS training_platform
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;
```

### 4.2 导入初始数据

项目已包含完整的数据库初始化脚本在 `for-claude-code/02-database/schema.sql`。

```bash
mysql -u root -p training_platform < for-claude-code/02-database/schema.sql
```

### 4.3 初始化管理员账户

默认管理员账号：
- 用户名：`admin`
- 密码：`admin123`

**重要**：首次登录后请立即修改密码！

---

## 5. 运维监控

### 5.1 日志管理

```bash
# 查看后端日志
docker-compose logs -f backend

# 查看前端日志
docker-compose logs -f frontend

# 查看所有日志
docker-compose logs -f
```

### 5.2 数据备份

```bash
# 数据库备份脚本
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
mysqldump -u root -p training_platform > backup_$DATE.sql
gzip backup_$DATE.sql
```

### 5.3 监控建议

- 使用 Prometheus + Grafana 监控服务器资源
- 使用 Sentry 监控前端错误
- 配置日志收集（ELK 或 Loki）

---

## 6. 安全配置

### 6.1 服务器安全

```bash
# 配置防火墙
sudo ufw allow 22    # SSH
sudo ufw allow 80     # HTTP
sudo ufw allow 443    # HTTPS
sudo ufw enable

# 安装 Fail2Ban
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

### 6.2 环境变量安全

- 所有敏感信息必须通过环境变量配置
- 不要将 `.env` 文件提交到代码仓库
- 生产环境定期轮换密钥

### 6.3 CORS 配置

确保 `backend/.env` 中的 `CORS_ORIGINS` 只包含信任的域名：

```env
CORS_ORIGINS=https://training.company.com,https://www.training.company.com
```

---

## 7. 故障排查

### 7.1 常见问题

| 问题 | 解决方案 |
|------|----------|
| 数据库连接失败 | 检查 DB_HOST 和 DB_PASSWORD |
| Redis 连接失败 | 检查 REDIS_HOST 和 REDIS_PORT |
| 前端无法访问API | 检查 Nginx 反向代理配置 |
| 登录失败 | 检查 JWT_SECRET_KEY 是否正确 |

### 7.2 日志查看

```bash
# 后端详细日志
docker-compose logs backend --tail=100

# 检查服务状态
docker-compose ps

# 重启服务
docker-compose restart
```

---

## 8. 联系支持

如有问题，请联系技术支持团队。

---

**文档版本历史**：

| 版本 | 日期 | 修改内容 |
|------|------|----------|
| v1.0 | 2026-05-08 | 初始版本 |
