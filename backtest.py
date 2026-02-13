import json
import os
from datetime import datetime, timedelta
import yfinance as yf
from pathlib import Path

# 加载配置
try:
    from config import Config
    KEEP_DAYS = Config.PREDICTION_RETENTION_DAYS if hasattr(Config, 'PREDICTION_RETENTION_DAYS') else 30
except:
    KEEP_DAYS = 30

# 配置
PREDICTIONS_DIR = "./predictions"
CUMULATIVE_STATS_FILE = "./backtest_cumulative_stats.json"  # 累计统计文件

def load_cumulative_stats():
    """加载累计统计数据"""
    if os.path.exists(CUMULATIVE_STATS_FILE):
        try:
            with open(CUMULATIVE_STATS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass

    # 默认初始值
    return {
        "total_predictions": 0,
        "correct_predictions": 0,
        "total_return": 0.0,
        "processed_dates": [],  # 已处理过的日期列表
        "last_updated": None,
        "history": []  # 保留最近的详细记录
    }

def save_cumulative_stats(stats):
    """保存累计统计数据"""
    with open(CUMULATIVE_STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(f"✅ 累计统计已更新: {CUMULATIVE_STATS_FILE}")

def get_stock_performance(stock_code, target_date):
    """
    获取股票在目标日期的涨跌情况
    返回: (涨跌幅百分比, 是否成功获取)
    """
    try:
        target = datetime.strptime(target_date, '%Y-%m-%d')
        start_date = (target - timedelta(days=5)).strftime('%Y-%m-%d')
        end_date = (target + timedelta(days=2)).strftime('%Y-%m-%d')

        ticker = yf.Ticker(stock_code)
        hist = ticker.history(start=start_date, end=end_date)

        if len(hist) < 2:
            return None, False

        target_str = target.strftime('%Y-%m-%d')

        if target_str in hist.index.strftime('%Y-%m-%d'):
            idx = list(hist.index.strftime('%Y-%m-%d')).index(target_str)
            if idx > 0:
                prev_close = hist.iloc[idx - 1]['Close']
                target_close = hist.iloc[idx]['Close']
                change_pct = ((target_close - prev_close) / prev_close) * 100
                return round(change_pct, 2), True

        available_dates = hist.index.strftime('%Y-%m-%d').tolist()
        for date_str in available_dates:
            if date_str >= target_str:
                idx = available_dates.index(date_str)
                if idx > 0:
                    prev_close = hist.iloc[idx - 1]['Close']
                    target_close = hist.iloc[idx]['Close']
                    change_pct = ((target_close - prev_close) / prev_close) * 100
                    return round(change_pct, 2), True

        return None, False

    except Exception as e:
        print(f"  ❌ 获取 {stock_code} 数据失败: {e}")
        return None, False

def evaluate_prediction(prediction, actual_change):
    """评估预测是否正确"""
    if actual_change is None:
        return None, None

    if prediction == "看涨":
        is_correct = actual_change > 0
        return_rate = actual_change
    elif prediction == "看跌":
        is_correct = actual_change < 0
        return_rate = -actual_change
    else:
        return None, None

    return is_correct, return_rate

def clean_old_files():
    """清理旧的预测和报告文件，只保留最近 KEEP_DAYS 天的"""
    cutoff_date = datetime.now() - timedelta(days=KEEP_DAYS)

    deleted_count = 0

    # 清理旧的预测文件
    if os.path.exists(PREDICTIONS_DIR):
        for pred_file in Path(PREDICTIONS_DIR).glob("prediction_*.json"):
            try:
                # 从文件名提取日期 prediction_2026-02-05.json
                date_str = pred_file.stem.replace("prediction_", "")
                file_date = datetime.strptime(date_str, '%Y-%m-%d')

                if file_date < cutoff_date:
                    pred_file.unlink()
                    deleted_count += 1
                    print(f"  🗑️  删除旧预测: {pred_file.name}")
            except:
                pass

    # 清理旧的报告目录
    for report_dir in Path(".").glob("report_*"):
        if report_dir.is_dir():
            try:
                # 从目录名提取日期 report_20260205
                date_str = report_dir.name.replace("report_", "")
                file_date = datetime.strptime(date_str, '%Y%m%d')

                if file_date < cutoff_date:
                    import shutil
                    shutil.rmtree(report_dir)
                    deleted_count += 1
                    print(f"  🗑️  删除旧报告: {report_dir.name}/")
            except:
                pass

    # 清理旧的回测结果文件
    for backtest_file in Path(".").glob("backtest_result_*.json"):
        try:
            # backtest_result_20260205_120000.json
            parts = backtest_file.stem.replace("backtest_result_", "").split("_")
            if len(parts) >= 1:
                date_str = parts[0]
                file_date = datetime.strptime(date_str, '%Y%m%d')

                if file_date < cutoff_date:
                    backtest_file.unlink()
                    deleted_count += 1
                    print(f"  🗑️  删除旧回测: {backtest_file.name}")
        except:
            pass

    if deleted_count > 0:
        print(f"\n✅ 清理完成，删除了 {deleted_count} 个旧文件")
    else:
        print(f"\n✅ 没有需要清理的旧文件")

def run_incremental_backtest():
    """运行增量回测：只处理新的预测文件"""
    print("=" * 60)
    print("开始增量回测...")
    print("=" * 60)

    if not os.path.exists(PREDICTIONS_DIR):
        print(f"❌ 预测目录不存在: {PREDICTIONS_DIR}")
        return

    # 加载累计统计
    cumulative = load_cumulative_stats()
    processed_dates = set(cumulative["processed_dates"])

    print(f"📊 当前累计统计:")
    print(f"   总预测次数: {cumulative['total_predictions']}")
    print(f"   正确次数: {cumulative['correct_predictions']}")
    if cumulative['total_predictions'] > 0:
        accuracy = (cumulative['correct_predictions'] / cumulative['total_predictions']) * 100
        print(f"   累计正确率: {accuracy:.2f}%")
        print(f"   累计收益率: {cumulative['total_return']:+.2f}%")
    print(f"   已处理日期数: {len(processed_dates)}")
    print()

    # 读取所有预测文件
    prediction_files = sorted([
        f for f in Path(PREDICTIONS_DIR).glob("prediction_*.json")
        if "backup" not in str(f)
    ])

    if not prediction_files:
        print(f"❌ 未找到预测文件")
        return

    # 只处理未处理过的文件
    new_files = [f for f in prediction_files
                 if f.stem.replace("prediction_", "") not in processed_dates]

    if not new_files:
        print("✅ 没有新的预测需要回测")
        return

    print(f"🔍 发现 {len(new_files)} 个新预测文件\n")

    new_results = []

    for pred_file in new_files:
        print(f"处理文件: {pred_file.name}")

        with open(pred_file, 'r', encoding='utf-8') as f:
            pred_data = json.load(f)

        date = pred_data.get('date')
        prediction_info = pred_data.get('prediction')

        if not prediction_info:
            print(f"  ⚠️  未找到预测信息，跳过")
            continue

        # 处理预测（支持单个或多个股票）
        predictions_list = [prediction_info] if isinstance(prediction_info, dict) else prediction_info

        # 修正：预测文件预测的是当天(date)的涨跌，而不是target_date
        print(f"  预测日期: {date}")

        for idx, pred in enumerate(predictions_list, 1):
            stock_code = pred.get('stock_code')
            direction = pred.get('direction')

            if not stock_code or not direction:
                continue

            if len(predictions_list) > 1:
                print(f"  股票 {idx}/{len(predictions_list)}: {stock_code}")

            # 获取实际表现 - 使用预测日期date而不是target_date
            actual_change, success = get_stock_performance(stock_code, date)

            if not success:
                print(f"  ⚠️  无法获取数据，跳过")
                continue

            print(f"  预测: {direction}, 实际: {actual_change:+.2f}%", end=" ")

            # 评估
            is_correct, return_rate = evaluate_prediction(direction, actual_change)

            if is_correct is None:
                print("⚠️  无法评估")
                continue

            # 更新累计统计
            cumulative["total_predictions"] += 1
            if is_correct:
                cumulative["correct_predictions"] += 1
                print("✅ 正确", end="")
            else:
                print("❌ 错误", end="")

            print(f", 收益: {return_rate:+.2f}%")

            cumulative["total_return"] += return_rate

            # 记录详细结果（只保留最近的）
            new_results.append({
                "date": date,
                "stock_code": stock_code,
                "prediction": direction,
                "actual_change": float(actual_change),
                "is_correct": bool(is_correct),
                "return_rate": float(return_rate)
            })

        # 标记为已处理
        processed_dates.add(date)
        print()

    # 更新历史记录（只保留最近的）
    cumulative["history"].extend(new_results)
    cumulative["history"] = cumulative["history"][-100:]  # 只保留最近100条
    cumulative["processed_dates"] = sorted(list(processed_dates))
    cumulative["last_updated"] = datetime.now().isoformat()

    # 保存累计统计
    save_cumulative_stats(cumulative)

    # 输出最新统计
    print("\n" + "=" * 60)
    print("回测结果汇总（累计）")
    print("=" * 60)

    if cumulative["total_predictions"] > 0:
        accuracy = (cumulative["correct_predictions"] / cumulative["total_predictions"]) * 100
        avg_return = cumulative["total_return"] / cumulative["total_predictions"]

        print(f"📊 总预测次数: {cumulative['total_predictions']}")
        print(f"✅ 正确次数: {cumulative['correct_predictions']}")
        print(f"❌ 错误次数: {cumulative['total_predictions'] - cumulative['correct_predictions']}")
        print(f"🎯 累计正确率: {accuracy:.2f}%")
        print(f"💰 平均收益率: {avg_return:+.2f}%")
        print(f"💰 累积总收益: {cumulative['total_return']:+.2f}%")
        print(f"📅 覆盖天数: {len(processed_dates)}")

    print("=" * 60)

    # 显示最近的详细结果
    if new_results:
        print("\n本次新增结果:")
        print("-" * 100)
        print(f"{'日期':<12} {'股票':<10} {'预测':<6} {'实际涨跌':<10} {'结果':<6} {'收益率':<10}")
        print("-" * 100)
        for r in new_results:
            result_symbol = "✓" if r['is_correct'] else "✗"
            print(f"{r['date']:<12} {r['stock_code']:<10} {r['prediction']:<6} "
                  f"{r['actual_change']:+7.2f}%   {result_symbol:<6} {r['return_rate']:+7.2f}%")
        print("-" * 100)

if __name__ == "__main__":
    print("\n📊 日股预测回测系统（增量模式）\n")

    # 运行增量回测
    run_incremental_backtest()

    # 清理旧文件
    print("\n🗑️  检查是否有旧文件需要清理...")
    clean_old_files()
