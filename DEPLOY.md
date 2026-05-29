# 华为云部署指南

## 前置条件

1. 注册华为云账号: https://www.huaweicloud.com
2. 开通开发者空间: https://devcloud.huawei.com
3. 安装 Docker 和 Docker Compose

## 部署步骤

### 1. 登录华为云开发者空间

通过 SSH 或 Web Terminal 连接到开发者空间。

### 2. 克隆项目

```bash
git clone https://github.com/Calmer2024/movie-recommender.git
cd movie-recommender
```

### 3. 一键部署

```bash
# 添加执行权限
chmod +x deploy.sh

# 运行部署脚本
./deploy.sh
```

### 4. 初始化测试数据

```bash
# 安装 Python 依赖
pip install psycopg werkzeug

# 运行种子数据脚本
cd backend
python seed_data.py
```

### 5. 访问应用

- 前端: http://<服务器IP>:80
- 后端 API: http://<服务器IP>:5000

## 测试账号

| 用户名 | 密码 |
|--------|------|
| alice | 123456 |
| bob | 123456 |
| charlie | 123456 |
| diana | 123456 |
| eve | 123456 |

## 常用命令

```bash
# 查看容器状态
docker-compose -f docker-compose.prod.yml ps

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f

# 重启服务
docker-compose -f docker-compose.prod.yml restart

# 停止服务
docker-compose -f docker-compose.prod.yml down

# 重新构建并启动
docker-compose -f docker-compose.prod.yml up -d --build
```

## 问题排查

### GaussDB 启动失败

```bash
# 查看 GaussDB 日志
docker logs gaussdb

# 检查端口是否被占用
netstat -tlnp | grep 5432
```

### 后端连接数据库失败

```bash
# 检查 GaussDB 是否健康
docker exec gaussdb pg_isready -U gaussdb -d movie_db

# 测试数据库连接
docker exec gaussdb psql -U gaussdb -d movie_db -c "SELECT 1;"
```

### 前端无法访问

```bash
# 检查 nginx 配置
docker exec movie-frontend cat /etc/nginx/conf.d/default.conf

# 查看前端日志
docker logs movie-frontend
```

## 端口说明

| 服务 | 端口 | 说明 |
|------|------|------|
| GaussDB | 5432 | 数据库服务 |
| Flask 后端 | 5000 | API 服务 |
| Vue 前端 | 80 | Web 界面 |
