#!/bin/bash
# 紧急修复脚本 - 切回 main 分支并清理状态

echo "🚨 紧急修复：切回 main 分支"
echo ""

# 1. 显示当前状态
echo "当前状态："
echo "  工作目录: $(pwd)"
echo "  当前分支: $(git branch --show-current 2>/dev/null || echo '未知')"
echo ""

# 2. 放弃所有更改并切回 main
echo "正在切换到 main 分支..."

# 保存当前分支
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null)

if [ "$CURRENT_BRANCH" = "main" ]; then
    echo "✅ 已经在 main 分支上"
else
    echo "📝 从 $CURRENT_BRANCH 切换到 main..."

    # 放弃所有本地更改
    git reset --hard HEAD 2>/dev/null

    # 切换分支
    git checkout main || {
        echo "❌ 无法切换到 main 分支"
        echo "   尝试强制切换..."
        git checkout -f main || {
            echo "❌ 强制切换也失败了"
            exit 1
        }
    }

    echo "✅ 已切换到 main 分支"
fi

echo ""

# 3. 更新 main 分支
echo "拉取最新代码..."
git pull origin main || {
    echo "⚠️  拉取失败，但继续执行"
}

echo ""

# 4. 清理状态
echo "清理工作目录..."
git clean -fd 2>/dev/null || true

echo ""

# 5. 确认状态
echo "修复后的状态："
echo "  当前分支: $(git branch --show-current)"
echo "  最新提交: $(git log -1 --oneline)"
echo ""

# 6. 检查必需文件
echo "检查必需文件："
for file in news_today.py backtest.py config.py run_daily.sh push_results.sh; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file (缺失！)"
    fi
done

echo ""
echo "✅ 修复完成！"
echo ""
echo "建议测试运行："
echo "  bash run_daily.sh"
