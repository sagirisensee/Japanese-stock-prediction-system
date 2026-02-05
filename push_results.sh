#!/bin/bash
# 推送预测结果到results分支
# 简化版：直接覆盖，不保留备份

set -e

echo "🚀 推送结果到results分支..."

# 保存当前状态
WORK_DIR=$(pwd)
CURRENT_BRANCH=$(git branch --show-current)

# 切换到results分支
echo "📝 切换到results分支..."
git checkout results

# 清空旧结果（避免累积）
rm -rf predictions/* reports/* backtest_results/* 2>/dev/null || true

echo "📦 复制最新结果..."

# 1. 复制预测文件 (predictions/*.json)
if ls "$WORK_DIR"/predictions/prediction_*.json 1> /dev/null 2>&1; then
    cp "$WORK_DIR"/predictions/prediction_*.json predictions/ 2>/dev/null || true
    COUNT=$(ls predictions/prediction_*.json 2>/dev/null | wc -l | tr -d ' ')
    echo "   ✓ 已复制 $COUNT 个预测文件"
fi

# 2. 复制报告目录 (report_*/)
if ls -d "$WORK_DIR"/report_* 1> /dev/null 2>&1; then
    for dir in "$WORK_DIR"/report_*; do
        if [ -d "$dir" ]; then
            basename=$(basename "$dir")
            mkdir -p "reports/$basename"
            cp -r "$dir"/* "reports/$basename/" 2>/dev/null || true
        fi
    done
    COUNT=$(ls -d reports/report_* 2>/dev/null | wc -l | tr -d ' ')
    echo "   ✓ 已复制 $COUNT 个报告目录"
fi

# 3. 复制回测结果 (backtest_result_*.json)
if ls "$WORK_DIR"/backtest_result_*.json 1> /dev/null 2>&1; then
    cp "$WORK_DIR"/backtest_result_*.json backtest_results/ 2>/dev/null || true
    COUNT=$(ls backtest_results/backtest_result_*.json 2>/dev/null | wc -l | tr -d ' ')
    echo "   ✓ 已复制 $COUNT 个回测结果"
fi

# 检查是否有变化
if [ -n "$(git status --porcelain)" ]; then
    echo "📊 提交更新..."
    git add predictions/ reports/ backtest_results/
    git commit -m "Update: $(date '+%Y-%m-%d %H:%M:%S')"

    echo "⬆️  推送到GitHub..."
    git push origin results

    echo "✅ 推送成功"
else
    echo "ℹ️  没有变化，跳过提交"
fi

# 切回原分支
echo "🔙 切回 $CURRENT_BRANCH 分支..."
git checkout "$CURRENT_BRANCH"

echo ""
echo "✅ 完成！"
