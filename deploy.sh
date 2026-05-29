#!/bin/bash
# 华为云部署脚本

echo "=========================================="
echo "  电影推荐系统 - 华为云部署脚本"
echo "=========================================="

# 1. 检查 Docker 是否安装
echo "[1/6] 检查 Docker 环境..."
if ! command -v docker &> /dev/null; then
    echo "错误: Docker 未安装，请先安装 Docker"
    exit 1
fi
echo "  Docker 已安装: $(docker --version)"

# 2. 检查 Docker Compose 是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "错误: Docker Compose 未安装"
    exit 1
fi
echo "  Docker Compose 已安装"

# 3. 停止旧容器
echo "[2/6] 停止旧容器..."
docker-compose -f docker-compose.prod.yml down 2>/dev/null

# 4. 启动 GaussDB
echo "[3/6] 启动 GaussDB 数据库..."
docker-compose -f docker-compose.prod.yml up -d gaussdb

# 5. 等待 GaussDB 就绪
echo "[4/6] 等待 GaussDB 启动..."
sleep 30

# 检查 GaussDB 是否健康
for i in {1..30}; do
    if docker exec gaussdb pg_isready -U gaussdb -d movie_db &>/dev/null; then
        echo "  GaussDB 已就绪"
        break
    fi
    echo "  等待中... ($i/30)"
    sleep 2
done

# 6. 初始化数据库
echo "[5/6] 初始化数据库..."
docker exec gaussdb psql -U gaussdb -d movie_db -c "
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    avatar VARCHAR(256) DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS movies (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    genres VARCHAR(200) DEFAULT '',
    director VARCHAR(100) DEFAULT '',
    actors VARCHAR(300) DEFAULT '',
    year INTEGER,
    poster_url VARCHAR(500) DEFAULT '',
    description TEXT DEFAULT '',
    avg_rating FLOAT DEFAULT 0.0,
    rating_count INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS ratings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    movie_id INTEGER REFERENCES movies(id) NOT NULL,
    score FLOAT NOT NULL,
    review TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, movie_id)
);

CREATE TABLE IF NOT EXISTS recommendations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    movie_id INTEGER REFERENCES movies(id) NOT NULL,
    score FLOAT NOT NULL,
    algorithm VARCHAR(50) DEFAULT 'als',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"
echo "  数据库表创建完成"

# 7. 构建并启动所有服务
echo "[6/6] 构建并启动所有服务..."
docker-compose -f docker-compose.prod.yml up -d --build

echo ""
echo "=========================================="
echo "  部署完成！"
echo "=========================================="
echo ""
echo "访问地址:"
echo "  前端: http://$(hostname -I | awk '{print $1}'):80"
echo "  后端 API: http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "测试账号:"
echo "  需要运行 seed_data.py 初始化测试数据"
echo ""
echo "查看日志:"
echo "  docker-compose -f docker-compose.prod.yml logs -f"
echo ""
