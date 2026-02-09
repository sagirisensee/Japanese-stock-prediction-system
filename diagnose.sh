#!/bin/bash
# 诊断脚本 - 检查项目配置和状态

echo "=========================================="
echo "📋 日股预测系统 - 环境诊断"
echo "=========================================="
echo ""

# 1. 基本信息
echo "1️⃣ 基本信息"
echo "   当前时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "   工作目录: $(pwd)"
echo "   用户: $(whoami)"
echo "   主机: $(hostname)"
echo ""

# 2. Git 状态
echo "2️⃣ Git 状态"
if [ -d .git ]; then
    echo "   ✅ 这是一个 Git 仓库"
    echo "   当前分支: $(git branch --show-current)"
    echo "   远程仓库: $(git remote get-url origin 2>/dev/null || echo 'N/A')"
    echo "   最近提交: $(git log -1 --oneline 2>/dev/null || echo 'N/A')"
    echo ""
    echo "   未跟踪/修改的文件:"
    git status --short | head -10
else
    echo "   ❌ 不是 Git 仓库"
fi
echo ""

# 3. Python 环境
echo "3️⃣ Python 环境"
if command -v python3 &> /dev/null; then
    echo "   ✅ Python3: $(python3 --version)"
else
    echo "   ❌ 未找到 Python3"
fi

if command -v pip3 &> /dev/null; then
    echo "   ✅ pip3: $(pip3 --version)"
else
    echo "   ❌ 未找到 pip3"
fi
echo ""

# 4. 必需文件检查
echo "4️⃣ 必需文件检查"
FILES=("news_today.py" "backtest.py" "config.py" "push_results.sh" "run_daily.sh" ".env")
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        if [ -x "$file" ] || [[ $file == *.py ]]; then
            echo "   ✅ $file"
        else
            echo "   ⚠️  $file (不可执行)"
        fi
    else
        echo "   ❌ $file (不存在)"
    fi
done
echo ""

# 5. 目录检查
echo "5️⃣ 目录检查"
DIRS=("predictions" "weekend_cache" "report_*")
for dir_pattern in "${DIRS[@]}"; do
    # 使用 bash 的 globbing
    found=false
    for dir in $dir_pattern; do
        if [ -d "$dir" ]; then
            count=$(ls "$dir" 2>/dev/null | wc -l | tr -d ' ')
            echo "   ✅ $dir/ (包含 $count 个项目)"
            found=true
        fi
    done
    if [ "$found" = false ] && [[ ! "$dir_pattern" =~ \* ]]; then
        echo "   ⚠️  $dir_pattern/ (不存在)"
    fi
done
echo ""

# 6. Crontab 检查
echo "6️⃣ Crontab 配置"
if crontab -l &> /dev/null; then
    echo "   ✅ Crontab 已配置:"
    crontab -l | grep -v "^#" | grep -v "^$" | while read -r line; do
        echo "      $line"
    done
else
    echo "   ⚠️  未配置 crontab"
fi
echo ""

# 7. 最近的日志
echo "7️⃣ 最近的运行日志"
if [ -f "/home/ubuntu/daily_cron.log" ]; then
    echo "   日志文件: /home/ubuntu/daily_cron.log"
    echo "   最后 20 行:"
    tail -20 /home/ubuntu/daily_cron.log | sed 's/^/      /'
elif [ -f "daily_cron.log" ]; then
    echo "   日志文件: $(pwd)/daily_cron.log"
    echo "   最后 20 行:"
    tail -20 daily_cron.log | sed 's/^/      /'
else
    echo "   ⚠️  未找到日志文件"
fi
echo ""

# 8. 周末缓存状态
echo "8️⃣ 周末缓存状态"
if [ -d "weekend_cache" ]; then
    cache_count=$(ls weekend_cache/*.json 2>/dev/null | wc -l | tr -d ' ')
    if [ $cache_count -gt 0 ]; then
        echo "   ✅ 找到 $cache_count 个缓存文件:"
        for cache_file in weekend_cache/*.json; do
            if [ -f "$cache_file" ]; then
                size=$(du -h "$cache_file" | cut -f1)
                echo "      $(basename "$cache_file") ($size)"
            fi
        done
    else
        echo "   ℹ️  没有缓存文件（正常，非周末时期）"
    fi
else
    echo "   ⚠️  weekend_cache 目录不存在"
fi
echo ""

# 9. API 配置检查
echo "9️⃣ API 配置检查"
if [ -f ".env" ]; then
    echo "   ✅ .env 文件存在"
    if grep -q "QWEN_API_KEY" .env && grep -q "GEMINI_API_KEY" .env; then
        echo "   ✅ API 密钥配置项存在"
    else
        echo "   ⚠️  API 密钥配置不完整"
    fi
else
    echo "   ❌ .env 文件不存在"
fi
echo ""

# 10. 推荐操作
echo "=========================================="
echo "🔧 推荐操作"
echo "=========================================="

# 检查是否在 main 分支
current_branch=$(git branch --show-current 2>/dev/null)
if [ "$current_branch" != "main" ]; then
    echo "⚠️  当前在 '$current_branch' 分支，建议切换到 main:"
    echo "   git checkout main"
    echo ""
fi

# 检查是否有 run_daily.sh
if [ ! -f "run_daily.sh" ]; then
    echo "⚠️  缺少 run_daily.sh，请从本地上传"
    echo ""
fi

# 检查 crontab
if ! crontab -l 2>/dev/null | grep -q "run_daily.sh"; then
    echo "⚠️  Crontab 未配置 run_daily.sh，建议添加:"
    echo "   crontab -e"
    echo "   添加: 5 0 * * * $(pwd)/run_daily.sh >> /home/ubuntu/daily_cron.log 2>&1"
    echo ""
fi

echo "✅ 诊断完成！"
