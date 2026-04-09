#!/bin/bash
#
# AI文章自动生成系统 - 一键启动脚本
# 
# 启动顺序：
#   1. Docker: WordPress + MySQL
#   2. Python 环境检查
#   3. uv 依赖管理工具检查
#   4. 安装 Python 依赖
#   5. 初始化数据库
#   6. 启动后端 API
#   7. 等待 API 就绪
#   8. 启动桌面 GUI
#
# 使用方法: 
#   ./start.sh           # 启动全部 (WordPress + 后端 API + GUI)
#   ./start.sh --no-docker # 仅启动后端 API + GUI (不启动 WordPress)
#

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }
step() { echo -e "\n${CYAN}[$1]${NC} $2"; }

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"

# 默认启动 Docker，除非指定 --no-docker
START_DOCKER=true
if [ "$1" == "--no-docker" ] || [ "$1" == "-n" ]; then
    START_DOCKER=false
fi

echo ""
echo "=========================================="
echo "   AI文章自动生成系统 - 启动脚本"
echo "=========================================="

#===========================================
# 步骤 1: Docker (可选)
#===========================================
if [ "$START_DOCKER" = true ]; then
    step "1/8" "启动 Docker 服务 (WordPress + MySQL)"
    
    if ! command -v docker &> /dev/null; then
        error "未找到 Docker，请先安装 Docker Desktop"
    fi
    
    if ! docker info &> /dev/null; then
        error "Docker 未运行，请先启动 Docker Desktop"
    fi
    success "Docker 已就绪"
    
    cd "$SCRIPT_DIR"
    
    # 1.1 启动数据库和 WordPress
    info "启动 MySQL 数据库..."
    docker-compose up -d wordpress-db
    sleep 5
    
    info "启动 WordPress..."
    docker-compose up -d wordpress
    
    # 1.2 等待 WordPress 就绪
    info "等待 WordPress 启动 (最多 2 分钟)..."
    for i in {1..60}; do
        if curl -s http://localhost:8082 > /dev/null 2>&1; then
            success "WordPress 已启动: http://localhost:8082"
            break
        fi
        sleep 2
        echo -n "."
        if [ $i -eq 60 ]; then
            warn "WordPress 启动超时，继续执行..."
        fi
    done
    echo ""
    
    # 1.3 运行 WordPress 初始化（创建管理员、应用密码、写入数据库）
    info "运行 WordPress 初始化 (创建应用密码)..."
    docker-compose up wordpress-init 2>&1 | grep -E "(✓|✗|WordPress|密码|配置)" || warn "初始化可能已完成"
    success "WordPress 初始化完成"
else
    step "1/8" "跳过 Docker (使用 --no-docker 跳过 WordPress)"
fi

#===========================================
# 步骤 2: Python 环境
#===========================================
step "2/8" "检查 Python 环境"

if ! command -v python3 &> /dev/null; then
    error "未找到 Python3，请安装 Python 3.11+"
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')

if python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"; then
    success "Python $PYTHON_VERSION (>= 3.11 ✓)"
else
    error "需要 Python 3.11+，当前: $PYTHON_VERSION"
fi

#===========================================
# 步骤 3: uv 依赖管理工具
#===========================================
step "3/8" "检查 uv 依赖管理工具"

if ! command -v uv &> /dev/null; then
    warn "uv 未安装，正在安装..."
    pip3 install --user uv
    export PATH="$HOME/.local/bin:$PATH"
    
    if ! command -v uv &> /dev/null; then
        error "uv 安装失败，请手动安装: pip install uv"
    fi
fi
success "uv $(uv --version 2>/dev/null | head -1)"

#===========================================
# 步骤 4: 安装 Python 依赖
#===========================================
step "4/8" "安装 Python 依赖"

cd "$BACKEND_DIR"
info "工作目录: $BACKEND_DIR"

uv sync --quiet
success "依赖安装完成"

#===========================================
# 步骤 5: 初始化数据库
#===========================================
step "5/8" "初始化数据库"

mkdir -p data logs

if [ -f "data/app.db" ]; then
    success "数据库已存在，跳过初始化"
else
    info "创建新数据库..."
    if [ -f "schema.sql" ]; then
        sqlite3 data/app.db < schema.sql 2>/dev/null || true
    fi
    if [ -f "init_data.sql" ]; then
        sqlite3 data/app.db < init_data.sql 2>/dev/null || true
    fi
    success "数据库初始化完成"
fi

#===========================================
# 步骤 6: 启动后端 API
#===========================================
step "6/8" "启动后端 API"

# 检查端口
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    warn "端口 8000 被占用，关闭旧进程..."
    pkill -f "python main.py" 2>/dev/null || true
    sleep 2
fi

uv run python main.py &
API_PID=$!
info "后端 API 进程: PID $API_PID"

#===========================================
# 步骤 7: 等待 API 就绪
#===========================================
step "7/8" "等待 API 服务就绪"

for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        success "后端 API 已就绪: http://localhost:8000"
        break
    fi
    sleep 1
    echo -n "."
    if [ $i -eq 30 ]; then
        error "API 启动超时，请检查日志"
    fi
done
echo ""

#===========================================
# 步骤 8: 启动桌面 GUI
#===========================================
step "8/8" "启动桌面 GUI"

uv run python -m gui.main_window &
GUI_PID=$!
success "桌面 GUI 已启动: PID $GUI_PID"

#===========================================
# 完成
#===========================================
echo ""
echo "=========================================="
echo -e "${GREEN}  启动完成！${NC}"
echo "=========================================="
echo ""
echo "  服务地址:"
echo "    后端 API:  http://localhost:8000"
echo "    API 文档:  http://localhost:8000/docs"
if [ "$START_DOCKER" = true ]; then
echo "    WordPress: http://localhost:8082"
echo "               后台: http://localhost:8082/wp-admin"
echo "               账号: admin / admin123"
fi
echo ""
echo "  进程 PID:"
echo "    API: $API_PID"
echo "    GUI: $GUI_PID"
echo ""
echo "  停止命令: ./stop.sh"
echo ""

# 保持前台运行
wait
