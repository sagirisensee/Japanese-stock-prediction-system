#!/bin/bash
# 推送预测结果到results分支
# 智能模式：自动检测worktree或普通模式

# 注意：不使用 set -e，因为需要确保在任何情况下都能切回 main 分支

echo "🚀 推送结果到results分支..."

# 定义路径
MAIN_DIR=$(pwd)
RESULTS_WORKTREE="../news-results"
CURRENT_BRANCH=$(git branch --show-current)

# 检测模式
USE_WORKTREE=false
if [ -d "$RESULTS_WORKTREE" ] && git worktree list | grep -q "news-results"; then
    USE_WORKTREE=true
    echo "📋 模式: Worktree"
else
    echo "📋 模式: Git Checkout"
fi

# ===== 收集文件到临时目录 =====
TEMP_DIR=$(mktemp -d)
echo "📦 准备结果文件..."

PRED_COUNT=0
REPORT_COUNT=0
BACKTEST_COUNT=0

# 1. 复制预测文件
if ls predictions/prediction_*.json 1> /dev/null 2>&1; then
    mkdir -p "$TEMP_DIR/predictions"
    cp predictions/prediction_*.json "$TEMP_DIR/predictions/"
    PRED_COUNT=$(ls "$TEMP_DIR/predictions"/prediction_*.json 2>/dev/null | wc -l | tr -d ' ')
    echo "   ✓ 找到 $PRED_COUNT 个预测文件"
else
    echo "   ⚠️  没有找到预测文件"
fi

# 2. 复制报告目录
if ls -d report_* 1> /dev/null 2>&1; then
    mkdir -p "$TEMP_DIR/reports"
    for dir in report_*; do
        if [ -d "$dir" ]; then
            cp -r "$dir" "$TEMP_DIR/reports/"
        fi
    done
    REPORT_COUNT=$(ls -d "$TEMP_DIR/reports"/report_* 2>/dev/null | wc -l | tr -d ' ')
    echo "   ✓ 找到 $REPORT_COUNT 个报告目录"
else
    echo "   ⚠️  没有找到报告目录"
fi

# 3. 复制回测结果
if ls backtest_result_*.json 1> /dev/null 2>&1; then
    mkdir -p "$TEMP_DIR/backtest_results"
    cp backtest_result_*.json "$TEMP_DIR/backtest_results/"
    BACKTEST_COUNT=$(ls "$TEMP_DIR/backtest_results"/backtest_result_*.json 2>/dev/null | wc -l | tr -d ' ')
    echo "   ✓ 找到 $BACKTEST_COUNT 个回测结果"
else
    echo "   ⚠️  没有找到回测结果"
fi

# 检查是否有文件
if [ $PRED_COUNT -eq 0 ] && [ $REPORT_COUNT -eq 0 ] && [ $BACKTEST_COUNT -eq 0 ]; then
    echo ""
    echo "❌ 没有找到任何结果文件，跳过推送"
    rm -rf "$TEMP_DIR"
    exit 0
fi

echo ""

# ===== 根据模式推送 =====
if [ "$USE_WORKTREE" = true ]; then
    # === Worktree 模式 ===
    echo "📥 复制到results工作树..."

    # 增量追加文件（不清空历史）
    # 复制文件
    if [ $PRED_COUNT -gt 0 ]; then
        mkdir -p "$RESULTS_WORKTREE/predictions"
        cp -r "$TEMP_DIR/predictions"/* "$RESULTS_WORKTREE/predictions/"
        echo "   ✓ 已复制 $PRED_COUNT 个预测文件"
    fi

    if [ $REPORT_COUNT -gt 0 ]; then
        mkdir -p "$RESULTS_WORKTREE/reports"
        cp -r "$TEMP_DIR/reports"/* "$RESULTS_WORKTREE/reports/"
        echo "   ✓ 已复制 $REPORT_COUNT 个报告目录"
    fi

    if [ $BACKTEST_COUNT -gt 0 ]; then
        mkdir -p "$RESULTS_WORKTREE/backtest_results"
        cp -r "$TEMP_DIR/backtest_results"/* "$RESULTS_WORKTREE/backtest_results/"
        echo "   ✓ 已复制 $BACKTEST_COUNT 个回测结果"
    fi

    # 提交
    cd "$RESULTS_WORKTREE"
    if [ -n "$(git status --porcelain)" ]; then
        echo ""
        echo "📊 提交更新..."
        git add predictions/ reports/ backtest_results/ 2>/dev/null || true

        # 检查是否有 staged changes
        if git diff --cached --quiet; then
            echo "ℹ️  没有需要提交的更改"
        else
            git commit -m "Update: $(date '+%Y-%m-%d %H:%M:%S')" || {
                echo "⚠️  提交失败"
            }

            echo "⬆️  推送到GitHub..."
            git push origin results || {
                echo "⚠️  推送失败"
            }

            echo "✅ 推送成功"
        fi
    else
        echo "ℹ️  没有变化，跳过提交"
    fi

    cd "$MAIN_DIR"

else
    # === Git Checkout 模式 ===
    echo "📝 切换到results分支..."
    git checkout results || {
        echo "❌ 无法切换到 results 分支"
        exit 1
    }

    # 增量追加文件（不清空历史）
    echo "📥 复制结果文件..."

    # 复制文件
    if [ $PRED_COUNT -gt 0 ]; then
        mkdir -p predictions
        cp -r "$TEMP_DIR/predictions"/* predictions/
        echo "   ✓ 已复制 $PRED_COUNT 个预测文件"
    fi

    if [ $REPORT_COUNT -gt 0 ]; then
        mkdir -p reports
        cp -r "$TEMP_DIR/reports"/* reports/
        echo "   ✓ 已复制 $REPORT_COUNT 个报告目录"
    fi

    if [ $BACKTEST_COUNT -gt 0 ]; then
        mkdir -p backtest_results
        cp -r "$TEMP_DIR/backtest_results"/* backtest_results/
        echo "   ✓ 已复制 $BACKTEST_COUNT 个回测结果"
    fi

    # 提交（使用 trap 确保切回分支）
    trap "git checkout $CURRENT_BRANCH 2>/dev/null || git checkout main 2>/dev/null" EXIT

    if [ -n "$(git status --porcelain)" ]; then
        echo ""
        echo "📊 提交更新..."
        git add predictions/ reports/ backtest_results/ 2>/dev/null || true

        # 检查是否有 staged changes
        if git diff --cached --quiet; then
            echo "ℹ️  没有需要提交的更改"
        else
            git commit -m "Update: $(date '+%Y-%m-%d %H:%M:%S')" || {
                echo "⚠️  提交失败，但会继续切回分支"
            }

            echo "⬆️  推送到GitHub..."
            git push origin results || {
                echo "⚠️  推送失败"
            }

            echo "✅ 推送成功"
        fi
    else
        echo ""
        echo "ℹ️  没有变化，跳过提交"
    fi

    # trap 会自动执行切回分支，但我们显式执行一次
    echo ""
    echo "🔙 切回 $CURRENT_BRANCH 分支..."
    git checkout "$CURRENT_BRANCH" || git checkout main
fi

# 清理临时目录
rm -rf "$TEMP_DIR"

echo ""
echo "✅ 完成！"
