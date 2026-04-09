#!/bin/bash
#
# AI文章自动生成系统 - 停止脚本
# 使用方法:
#   ./stop.sh            # 停止全部 (WordPress + 后端 API + GUI)
#   ./stop.sh --no-docker # 仅停止后端 API + GUI
#

echo "停止 AI文章自动生成系统..."
echo ""

# 停止后端 API
pkill -f "python main.py" 2>/dev/null && echo "✓ 后端 API 已停止" || echo "- 后端 API 未运行"

# 停止桌面 GUI
pkill -f "gui.main_window" 2>/dev/null && echo "✓ 桌面 GUI 已停止" || echo "- 桌面 GUI 未运行"

# 默认停止 Docker，除非指定 --no-docker
if [ "$1" != "--no-docker" ] && [ "$1" != "-n" ]; then
    echo ""
    echo "停止 Docker 容器..."
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    cd "$SCRIPT_DIR"
    
    if command -v docker-compose &> /dev/null; then
        docker-compose down 2>/dev/null && echo "✓ WordPress (Docker) 已停止" || echo "- Docker 容器未运行"
    elif command -v docker &> /dev/null; then
        docker compose down 2>/dev/null && echo "✓ WordPress (Docker) 已停止" || echo "- Docker 容器未运行"
    fi
fi

echo ""
echo "所有服务已停止"
