#!/bin/bash
# Docker 环境下的 WordPress 自动初始化脚本
# 在 WordPress 容器内部运行

set -e

# 配置
WP_URL="${WP_URL:-http://localhost:8082}"
WP_INTERNAL_URL="${WP_INTERNAL_URL:-http://wordpress:80}"
WP_TITLE="AI Article Test Site"
WP_ADMIN_USER="admin"
WP_ADMIN_PASSWORD="admin123"
WP_ADMIN_EMAIL="admin@example.com"
APP_PASSWORD_NAME="ai-article-api"
BACKEND_URL="${BACKEND_URL:-http://backend:8000}"

echo "========================================"
echo "  WordPress 自动初始化"
echo "========================================"

# 等待 MySQL 就绪
echo "[1/6] 等待数据库就绪..."
while ! mysqladmin ping -h"wordpress-db" -u"wordpress" -p"wordpress123" --silent 2>/dev/null; do
    sleep 2
    echo "  等待数据库..."
done
echo "✓ 数据库已就绪"

# 安装 WP-CLI
echo "[2/6] 安装 WP-CLI..."
if [ ! -f /usr/local/bin/wp ]; then
    curl -sO https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar
    chmod +x wp-cli.phar
    mv wp-cli.phar /usr/local/bin/wp
fi
echo "✓ WP-CLI 已安装"

# 等待 WordPress 文件就绪
echo "[3/6] 等待 WordPress 文件..."
while [ ! -f /var/www/html/wp-config.php ]; do
    sleep 2
done
echo "✓ WordPress 文件已就绪"

# 检查是否已安装
echo "[4/6] 检查/执行 WordPress 安装..."
if ! wp core is-installed --allow-root 2>/dev/null; then
    wp core install \
        --url="$WP_URL" \
        --title="$WP_TITLE" \
        --admin_user="$WP_ADMIN_USER" \
        --admin_password="$WP_ADMIN_PASSWORD" \
        --admin_email="$WP_ADMIN_EMAIL" \
        --skip-email \
        --allow-root
    echo "✓ WordPress 安装完成"
else
    echo "✓ WordPress 已安装"
fi

# 启用 HTTP 环境下的应用密码
echo "[5/6] 配置应用密码..."
if ! grep -q 'WP_ENVIRONMENT_TYPE' /var/www/html/wp-config.php; then
    sed -i "/That's all, stop editing/i define('WP_ENVIRONMENT_TYPE', 'local');" /var/www/html/wp-config.php
fi

# 删除旧的应用密码
wp user application-password delete $WP_ADMIN_USER --all --allow-root 2>/dev/null || true

# 创建新的应用密码
APP_PASSWORD=$(wp user application-password create $WP_ADMIN_USER "$APP_PASSWORD_NAME" --porcelain --allow-root 2>/dev/null)

if [ -z "$APP_PASSWORD" ]; then
    echo "错误: 无法创建应用密码"
    exit 1
fi
echo "✓ 应用密码已创建: $APP_PASSWORD"

# 通知后端更新 CMS 配置
echo "[6/6] 更新后端 CMS 配置..."
sleep 5  # 等待后端启动

# 调用后端 API 更新 CMS 配置
curl -s -X PUT "$BACKEND_URL/api/cms" \
    -H "Content-Type: application/json" \
    -d "{
        \"platform\": \"wordpress\",
        \"api_url\": \"$WP_INTERNAL_URL\",
        \"username\": \"$WP_ADMIN_USER\",
        \"password\": \"$APP_PASSWORD\",
        \"is_active\": true
    }" > /dev/null 2>&1 && echo "✓ CMS 配置已更新" || echo "⚠ CMS 配置更新失败，请手动配置"

echo ""
echo "========================================"
echo "  初始化完成！"
echo "========================================"
echo "WordPress 后台: $WP_URL/wp-admin"
echo "用户名: $WP_ADMIN_USER"
echo "密码: $WP_ADMIN_PASSWORD"
echo "应用密码: $APP_PASSWORD"
echo ""
