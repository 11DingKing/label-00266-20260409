#!/bin/bash
# WordPress 自动初始化脚本
# 自动完成 WordPress 安装并创建应用密码

set -e

# 配置
WP_URL="http://localhost:8082"
WP_TITLE="AI Article Test Site"
WP_ADMIN_USER="admin"
WP_ADMIN_PASSWORD="admin123"
WP_ADMIN_EMAIL="admin@example.com"
APP_PASSWORD_NAME="ai-article-api"

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  WordPress 自动初始化脚本${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 检查 WordPress 容器是否运行
echo -e "${YELLOW}[1/5] 检查 WordPress 容器...${NC}"
if ! docker ps | grep -q "ai-article-wordpress"; then
    echo -e "${RED}错误: WordPress 容器未运行${NC}"
    echo "请先运行: docker-compose up -d wordpress wordpress-db"
    exit 1
fi
echo -e "${GREEN}✓ WordPress 容器运行中${NC}"

# 等待 WordPress 就绪
echo -e "${YELLOW}[2/5] 等待 WordPress 就绪...${NC}"
MAX_WAIT=60
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    if curl -s -o /dev/null -w "%{http_code}" "$WP_URL" | grep -q "200\|302"; then
        break
    fi
    sleep 2
    WAITED=$((WAITED + 2))
    echo "  等待中... ($WAITED 秒)"
done

if [ $WAITED -ge $MAX_WAIT ]; then
    echo -e "${RED}错误: WordPress 启动超时${NC}"
    exit 1
fi
echo -e "${GREEN}✓ WordPress 已就绪${NC}"

# 在容器中安装 WP-CLI
echo -e "${YELLOW}[3/5] 安装 WP-CLI...${NC}"
docker exec ai-article-wordpress bash -c '
if [ ! -f /usr/local/bin/wp ]; then
    curl -sO https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar
    chmod +x wp-cli.phar
    mv wp-cli.phar /usr/local/bin/wp
fi
' 2>/dev/null || true
echo -e "${GREEN}✓ WP-CLI 已安装${NC}"

# 检查是否已安装 WordPress
echo -e "${YELLOW}[4/6] 检查/执行 WordPress 安装...${NC}"
WP_INSTALLED=$(docker exec ai-article-wordpress wp core is-installed --allow-root 2>/dev/null && echo "yes" || echo "no")

if [ "$WP_INSTALLED" = "no" ]; then
    echo "  执行 WordPress 安装..."
    docker exec ai-article-wordpress wp core install \
        --url="$WP_URL" \
        --title="$WP_TITLE" \
        --admin_user="$WP_ADMIN_USER" \
        --admin_password="$WP_ADMIN_PASSWORD" \
        --admin_email="$WP_ADMIN_EMAIL" \
        --skip-email \
        --allow-root
    echo -e "${GREEN}✓ WordPress 安装完成${NC}"
else
    echo -e "${GREEN}✓ WordPress 已安装${NC}"
fi

# 启用 HTTP 环境下的应用密码功能
echo -e "${YELLOW}[5/6] 配置应用密码...${NC}"
docker exec ai-article-wordpress bash -c "grep -q 'WP_ENVIRONMENT_TYPE' /var/www/html/wp-config.php || sed -i \"/That's all, stop editing/i define('WP_ENVIRONMENT_TYPE', 'local');\" /var/www/html/wp-config.php" 2>/dev/null

# 创建应用密码
# 先删除旧的同名应用密码（如果存在）
docker exec ai-article-wordpress wp user application-password delete $WP_ADMIN_USER --all --allow-root 2>/dev/null || true

# 创建新的应用密码
APP_PASSWORD=$(docker exec ai-article-wordpress wp user application-password create $WP_ADMIN_USER "$APP_PASSWORD_NAME" --porcelain --allow-root 2>/dev/null)

if [ -z "$APP_PASSWORD" ]; then
    echo -e "${RED}错误: 无法创建应用密码${NC}"
    exit 1
fi

echo -e "${GREEN}✓ 应用密码已创建${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  初始化完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "WordPress 后台: ${YELLOW}$WP_URL/wp-admin${NC}"
echo -e "管理员用户名:   ${YELLOW}$WP_ADMIN_USER${NC}"
echo -e "管理员密码:     ${YELLOW}$WP_ADMIN_PASSWORD${NC}"
echo ""
echo -e "${GREEN}API 配置信息（用于 CMS 配置页面）:${NC}"
echo -e "API URL:        ${YELLOW}$WP_URL${NC}"
echo -e "用户名:         ${YELLOW}$WP_ADMIN_USER${NC}"
echo -e "应用密码:       ${YELLOW}$APP_PASSWORD${NC}"
echo ""

# 自动写入数据库
echo -e "${YELLOW}[7/7] 写入系统数据库...${NC}"

# 检查数据库文件
DB_FILE=""
if [ -f "backend/data/app.db" ]; then
    DB_FILE="backend/data/app.db"
elif [ -f "data/app.db" ]; then
    DB_FILE="data/app.db"
fi

if [ -n "$DB_FILE" ]; then
    # 删除旧配置，插入新配置
    sqlite3 "$DB_FILE" "DELETE FROM cms_config WHERE platform='wordpress';"
    sqlite3 "$DB_FILE" "INSERT INTO cms_config (platform, api_url, username, password, is_active, created_at, updated_at) VALUES ('wordpress', '$WP_URL', '$WP_ADMIN_USER', '$APP_PASSWORD', 1, datetime('now'), datetime('now'));"
    echo -e "${GREEN}✓ 配置已写入数据库${NC}"
else
    echo -e "${YELLOW}未找到数据库文件，请手动在CMS配置页面填入以上信息${NC}"
fi

echo ""
echo -e "${GREEN}完成！现在可以在文章页面测试发布功能了。${NC}"
