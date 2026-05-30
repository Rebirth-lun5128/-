#!/bin/bash
# ============================================
# 社区夜市外卖平台 — 服务器一键部署脚本
# 适用于 Ubuntu 20.04+ / CentOS 7+
# 用法: chmod +x deploy.sh && sudo ./deploy.sh
# ============================================
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +%H:%M:%S)]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
err() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# ---- 配置变量（按需修改） ----
APP_DIR="/opt/cc"
DOMAIN="${DOMAIN:-your-domain.com}"          # 改为你的域名
APP_PORT=8000
MYSQL_PASSWORD="${MYSQL_PASSWORD:-CcDb@2026}"  # 改为你的MySQL密码
SECRET_KEY="${SECRET_KEY:-}"                   # 留空自动生成

# ---- 检查root ----
if [ "$(id -u)" != "0" ]; then
    err "请用 root 运行: sudo ./deploy.sh"
fi

# ============================================
# 1. 系统基础环境
# ============================================
log "===== 安装系统依赖 ====="

if command -v apt-get &>/dev/null; then
    apt-get update -qq
    apt-get install -y -qq python3 python3-pip python3-venv \
        nginx git curl unzip mysql-server \
        build-essential libmysqlclient-dev redis-server 2>&1 | tail -1
elif command -v yum &>/dev/null; then
    yum install -y -q epel-release
    yum install -y -q python3 python3-pip python3-devel \
        nginx git curl unzip mysql-server redis \
        gcc mysql-devel 2>&1 | tail -1
fi

# ---- 生成 SECRET_KEY ----
if [ -z "$SECRET_KEY" ]; then
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    log "SECRET_KEY 已自动生成"
fi

# ============================================
# 2. 拉取代码
# ============================================
log "===== 拉取代码 ====="

if [ -d "$APP_DIR" ]; then
    cd "$APP_DIR"
    git pull origin main
else
    git clone https://github.com/Rebirth-lun5128/-.git "$APP_DIR"
    cd "$APP_DIR"
fi

# ============================================
# 3. 后端部署
# ============================================
log "===== 部署后端 ====="
cd "$APP_DIR/server"

# 安装 Python 依赖
pip3 install -r requirements.txt --quiet 2>&1 | tail -1

# 创建 .env
cat > .env <<EOF
DEBUG=false
SECRET_KEY=${SECRET_KEY}
DATABASE_URL=mysql+pymysql://root:${MYSQL_PASSWORD}@localhost:3306/cc_food?charset=utf8mb4
REDIS_URL=redis://localhost:6379/0
CORS_ORIGINS=https://${DOMAIN},https://admin.${DOMAIN}
UPLOAD_DIR=./uploads
EOF
log ".env 配置完成"

# MySQL 配置
log "配置 MySQL..."
mysql -u root -p"${MYSQL_PASSWORD}" --connect-expired-password -e "SELECT 1" 2>/dev/null || {
    warn "MySQL 密码可能不正确，请手动设置后重新运行"
}
mysql -u root -p"${MYSQL_PASSWORD}" -e "CREATE DATABASE IF NOT EXISTS cc_food CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/dev/null || true

# Systemd 服务
cat > /etc/systemd/system/cc-server.service <<EOF
[Unit]
Description=CC Food Delivery Backend
After=network.target mysql.service redis.service

[Service]
Type=simple
User=root
WorkingDirectory=${APP_DIR}/server
ExecStart=python3 -m uvicorn main:app --host 0.0.0.0 --port ${APP_PORT} --workers 2
Restart=always
RestartSec=5
Environment=PATH=/usr/bin:/usr/local/bin

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable cc-server
systemctl restart cc-server
log "后端服务已启动 (端口 ${APP_PORT})"

# ============================================
# 4. Nginx 配置
# ============================================
log "===== 配置 Nginx ====="

cat > /etc/nginx/sites-available/cc <<EOF
server {
    listen 80;
    server_name ${DOMAIN} admin.${DOMAIN};

    # 上传文件
    location /uploads/ {
        alias ${APP_DIR}/server/uploads/;
        expires 30d;
    }

    # API 反代
    location /api/ {
        proxy_pass http://127.0.0.1:${APP_PORT}/api/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_read_timeout 60s;
    }

    # WebSocket
    location /ws {
        proxy_pass http://127.0.0.1:${APP_PORT}/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }

    # 管理后台（静态）
    root ${APP_DIR}/admin-web/dist;
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }
}
EOF

ln -sf /etc/nginx/sites-available/cc /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx
log "Nginx 配置完成"

# ============================================
# 5. 构建前端
# ============================================
log "===== 构建管理后台 ====="
cd "$APP_DIR/admin-web"
if ! command -v npm &>/dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
fi
npm install --silent
npm run build 2>&1 | tail -3
log "管理后台构建完成 → admin-web/dist/"

log "===== 构建 H5 用户端 ====="
cd "$APP_DIR/h5-user"
npm install --silent
npm run build 2>&1 | tail -3
log "H5用户端构建完成 → h5-user/dist/"

# ============================================
# 6. SSL证书（Certbot可选）
# ============================================
if [ "$DOMAIN" != "your-domain.com" ] && command -v certbot &>/dev/null; then
    log "===== 配置 HTTPS ====="
    certbot --nginx -d "${DOMAIN}" -d "admin.${DOMAIN}" --non-interactive --agree-tos --email "admin@${DOMAIN}" || warn "证书申请失败，请手动执行 certbot"
fi

# ============================================
# 7. 定时备份 (crontab)
# ============================================
log "===== 配置自动备份 ====="
(crontab -l 2>/dev/null; echo "0 3 * * * cd ${APP_DIR}/server && python3 backup.py >> ${APP_DIR}/server/logs/backup.log 2>&1") | crontab -
log "每日凌晨3点自动备份已配置"

# ============================================
# 8. 完成
# ============================================
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  部署完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "后端API:     http://${DOMAIN}/api"
echo -e "API文档:     http://${DOMAIN}/docs"
echo -e "管理后台:     http://${DOMAIN}/"
echo -e "H5用户端:     http://${DOMAIN}/h5/"
echo -e "健康检查:     http://${DOMAIN}/api/health"
echo ""
echo -e "服务管理:"
echo -e "  查看状态:   systemctl status cc-server"
echo -e "  查看日志:   journalctl -u cc-server -f"
echo -e "  重启服务:   systemctl restart cc-server"
echo ""
echo -e "数据库备份:   cd ${APP_DIR}/server && python3 backup.py"
echo -e "SECRET_KEY:   ${SECRET_KEY}"
echo ""
echo -e "${YELLOW}注意事项:${NC}"
echo -e "1. 确保域名 ${DOMAIN} DNS已解析到本服务器"
echo -e "2. 手动执行 certbot 获取SSL证书: sudo certbot --nginx"
echo -e "3. 在微信小程序后台配置服务器域名白名单"
echo -e "4. 修改 MySQL root密码后同步更新 .env"
