#!/bin/bash
# 推送预测结果到results分支（适用于worktree模式）

set -e

echo "🚀 推送结果到results分支（worktree模式）..."

# 定义路径
MAIN_DIR=$(pwd)
RESULTS_DIR="../news-results"

# 检查results工作树是否存在
if [ ! -d "$RESULTS_DIR" ]; then
    echo "❌ 找不到results工作树: $RESULTS_DIR"
    echo "   请先创建: git worktree add ../news-results results"
    exit 1
fi

echo "📦 准备结果文件..."

# 计数器
PRED_COUNT=0
REPORT_COUNT=0
BACKTEST_COUNT=0

# 1. 检查预测文件
if ls predictions/prediction_*.json 1> /dev/null 2>&1; then
    PRED_COUNT=$(ls predictions/prediction_*.json 2>/dev/null | wc -l | tr -d ' ')
    echo "   ✓ 找到 $PRED_COUNT 个预测文件"
else
    echo "   ⚠️  没有找到预测文件"
fi

# 2. 检查报告目录
if ls -d report_* 1> /dev/null 2>&1; then
    REPORT_COUNT=$(ls -d report_* 2>/dev/null | wc -l | tr -d ' ')
    echo "   ✓ 找到 $REPORT_COUNT 个报告目录"
else
    echo "   ⚠️  没有找到报告目录"
fi

# 3. 检查回测结果
if ls backtest_result_*.json 1> /dev/null 2>&1; then
    BACKTEST_COUNT=$(ls backtest_result_*.json 2>/dev/null | wc -l | tr -d ' ')
    echo "   ✓ 找到 $BACKTEST_COUNT 个回测结果"
else
    echo "   ⚠️  没有找到回测结果"
fi

# 如果没有任何文件，退出
if [ $PRED_COUNT -eq 0 ] && [ $REPORT_COUNT -eq 0 ] && [ $BACKTEST_COUNT -eq 0 ]; then
    echo ""
    echo "❌ 没有找到任何结果文件，跳过推送"
    exit 0
fi

echo ""
echo "📥 复制到results工作树..."

# 清空results目录的旧文件
rm -rf "$RESULTS_DIR/predictions"/* "$RESULTS_DIR/reports"/* "$RESULTS_DIR/backtest_results"/* 2>/dev/null || true

# 复制预测文件
if [ $PRED_COUNT -gt 0 ]; then
    mkdir -p "$RESULTS_DIR/predictions"
    cp predictions/prediction_*.json "$RESULTS_DIR/predictions/"
    echo "   ✓ 已复制 $PRED_COUNT 个预测文件"
fi

# 复制报告目录
if [ $REPORT_COUNT -gt 0 ]; then
    mkdir -p "$RESULTS_DIR/reports"
    for dir in report_*; do
        if [ -d "$dir" ]; then
            cp -r "$dir" "$RESULTS_DIR/reports/"
        fi
    done
    echo "   ✓ 已复制 $REPORT_COUNT 个报告目录"
fi

# 复制回测结果
if [ $BACKTEST_COUNT -gt 0 ]; then
    mkdir -p "$RESULTS_DIR/backtest_results"
    cp backtest_result_*.json "$RESULTS_DIR/backtest_results/"
    echo "   ✓ 已复制 $BACKTEST_COUNT 个回测结果"
fi

# 进入results目录提交
cd "$RESULTS_DIR"

# 检查是否有变化
if [ -n "$(git status --porcelain)" ]; then
    echo ""
    echo "📊 提交更新..."
    git add predictions/ reports/ backtest_results/
    git commit -m "Update: $(date '+%Y-%m-%d %H:%M:%S')"

    echo "⬆️  推送到GitHub..."
    git push origin results

    echo "✅ 推送成功"
else
    echo ""
    echo "ℹ️  没有变化，跳过提交"
fi

# 返回主目录
cd "$MAIN_DIR"

echo ""
echo "✅ 完成！"
echo "   查看结果: cd $RESULTS_DIR && ls predictions/ reports/"
