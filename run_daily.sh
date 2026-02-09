#!/bin/bash

# 日股预测系统 - 每日运行脚本
# 使用方法：
#   chmod +x run_daily.sh
#   在crontab中添加: 5 0 * * * /path/to/run_daily.sh >> /home/ubuntu/daily_cron.log 2>&1

# 设置脚本所在目录为工作目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

# 日志分隔符
echo ""
echo "=================================================="
echo "🕐 运行时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "📂 工作目录: $SCRIPT_DIR"
echo "🌿 当前分支: $(git branch --show-current 2>/dev/null || echo 'N/A')"
echo "=================================================="
echo ""

# 检测并激活虚拟环境
if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
    echo "🐍 激活虚拟环境..."
    source venv/bin/activate
    echo "✅ Python: $(which python3)"
    echo "   版本: $(python3 --version)"
else
    echo "⚠️  未找到 venv，使用系统 Python"
    echo "   Python: $(which python3)"
    echo "   版本: $(python3 --version 2>/dev/null || echo '未安装')"
fi
echo ""

# 确保在 main 分支上
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "⚠️  当前不在 main 分支，尝试切换..."
    git checkout main || {
        echo "❌ 无法切换到 main 分支"
        exit 1
    }
    echo "✅ 已切换到 main 分支"
fi

# 确保必要的目录存在
echo "📁 检查目录..."
mkdir -p predictions weekend_cache
echo "✅ 目录就绪"
echo ""

# 1. 运行历史预测回测
echo "📊 正在进行历史预测回测..."
if [ -f "backtest.py" ]; then
    python3 backtest.py
else
    echo "⚠️  backtest.py 不存在，跳过回测"
fi

# 2. 生成今日预测
echo "🎯 正在生成今日预测..."
if [ -f "news_today.py" ]; then
    python3 news_today.py
else
    echo "❌ news_today.py 不存在，退出"
    exit 1
fi

# 3. 推送结果到results分支
echo "🚀 推送结果到results分支..."
if [ -f "push_results.sh" ]; then
    bash push_results.sh
else
    echo "⚠️  push_results.sh 不存在，跳过推送"
fi

echo ""
echo "=================================================="
echo "✅ 日常任务完成: $(date '+%Y-%m-%d %H:%M:%S')"
echo "🌿 当前分支: $(git branch --show-current 2>/dev/null || echo 'N/A')"
echo "=================================================="
echo ""
