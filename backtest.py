import json
import os
from datetime import datetime, timedelta
import yfinance as yf
from pathlib import Path

# 配置
PREDICTIONS_DIR = "./predictions"

def get_stock_performance(stock_code, target_date):
    """
    获取股票在目标日期的涨跌情况
    返回: (涨跌幅百分比, 是否成功获取)
    """
    try:
        # 转换日期格式
        target = datetime.strptime(target_date, '%Y-%m-%d')
        # 获取前一天和当天的数据（需要多取几天以应对节假日）
        start_date = (target - timedelta(days=5)).strftime('%Y-%m-%d')
        end_date = (target + timedelta(days=2)).strftime('%Y-%m-%d')

        # 下载股票数据
        ticker = yf.Ticker(stock_code)
        hist = ticker.history(start=start_date, end=end_date)

        if len(hist) < 2:
            print(f"  ⚠️  {stock_code} 数据不足")
            return None, False

        # 找到目标日期及其前一个交易日
        target_str = target.strftime('%Y-%m-%d')

        # 获取目标日期的数据
        if target_str in hist.index.strftime('%Y-%m-%d'):
            idx = list(hist.index.strftime('%Y-%m-%d')).index(target_str)
            if idx > 0:
                prev_close = hist.iloc[idx - 1]['Close']
                target_close = hist.iloc[idx]['Close']
                change_pct = ((target_close - prev_close) / prev_close) * 100
                return round(change_pct, 2), True

        # 如果目标日期不是交易日，取下一个交易日
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
    """
    评估预测是否正确
    prediction: "看涨" 或 "看跌"
    actual_change: 实际涨跌幅（百分比）
    返回: (是否正确, 收益率)
    """
    if actual_change is None:
        return None, None

    if prediction == "看涨":
        # 预测看涨：实际涨幅为正则正确
        is_correct = actual_change > 0
        # 收益率 = 实际涨跌幅（如果看涨正确就赚钱，错了就亏钱）
        return_rate = actual_change
    elif prediction == "看跌":
        # 预测看跌：实际跌幅为负则正确
        is_correct = actual_change < 0
        # 做空收益 = -实际涨跌幅
        return_rate = -actual_change
    else:
        return None, None

    return is_correct, return_rate

def run_backtest():
    """
    运行回测，计算历史预测的正确率和收益率
    """
    print("=" * 60)
    print("开始回测...")
    print("=" * 60)

    if not os.path.exists(PREDICTIONS_DIR):
        print(f"❌ 预测目录不存在: {PREDICTIONS_DIR}")
        return

    # 读取所有预测文件（排除备份）
    prediction_files = sorted([
        f for f in Path(PREDICTIONS_DIR).glob("prediction_*.json")
        if "backup" not in str(f)  # 排除备份文件
    ])

    if not prediction_files:
        print(f"❌ 未找到预测文件")
        return

    results = []
    total_predictions = 0
    correct_predictions = 0
    total_return = 0.0
    successful_trades = 0

    for pred_file in prediction_files:
        print(f"\n处理文件: {pred_file.name}")

        with open(pred_file, 'r', encoding='utf-8') as f:
            pred_data = json.load(f)

        # 验证是否为最新版本（如果有version字段）
        version = pred_data.get('version')
        if version and version != 'latest':
            print(f"  ⚠️  检测到非最新版本，跳过（可能是备份文件）")
            continue

        # 提取关键信息
        date = pred_data.get('date')
        target_date = pred_data.get('target_date')
        prediction_info = pred_data.get('prediction')
        timestamp = pred_data.get('timestamp', 'unknown')

        if not prediction_info:
            print(f"  ⚠️  未找到预测信息，跳过")
            continue

        # 支持单个股票或多个股票
        predictions_list = []
        if isinstance(prediction_info, list):
            # 多个股票
            predictions_list = prediction_info
            print(f"  日期: {date}")
            print(f"  目标日期: {target_date}")
            print(f"  预测股票数: {len(predictions_list)}")
        elif isinstance(prediction_info, dict):
            # 单个股票
            predictions_list = [prediction_info]
            print(f"  日期: {date}")
            print(f"  目标日期: {target_date}")
            print(f"  股票: {prediction_info.get('stock_code')}")
            print(f"  预测: {prediction_info.get('direction')}")
        else:
            print(f"  ⚠️  预测信息格式错误，跳过")
            continue

        # 处理每只股票
        for idx, pred in enumerate(predictions_list, 1):
            stock_code = pred.get('stock_code')
            direction = pred.get('direction')

            if not stock_code or not direction:
                print(f"  ⚠️  股票 {idx} 信息不完整，跳过")
                continue

            if len(predictions_list) > 1:
                print(f"\n  股票 {idx}/{len(predictions_list)}: {stock_code} - {direction}")

            # 获取实际表现
            actual_change, success = get_stock_performance(stock_code, target_date)

            if not success:
                print(f"  ⚠️  无法获取实际数据，跳过")
                continue

            print(f"  实际涨跌: {actual_change:+.2f}%")

            # 评估预测
            is_correct, return_rate = evaluate_prediction(direction, actual_change)

            if is_correct is None:
                print(f"  ⚠️  无法评估，跳过")
                continue

            total_predictions += 1
            if is_correct:
                correct_predictions += 1
                print(f"  ✅ 预测正确")
            else:
                print(f"  ❌ 预测错误")

            print(f"  收益率: {return_rate:+.2f}%")

            total_return += return_rate
            successful_trades += 1

            # 记录结果
            results.append({
                "date": date,
                "target_date": target_date,
                "stock_code": stock_code,
                "prediction": direction,
                "actual_change": float(actual_change),
                "is_correct": bool(is_correct),
                "return_rate": float(return_rate)
            })

    # 输出统计结果
    print("\n" + "=" * 60)
    print("回测结果汇总")
    print("=" * 60)

    if total_predictions == 0:
        print("❌ 没有有效的预测数据")
        return

    accuracy = (correct_predictions / total_predictions) * 100
    avg_return = total_return / successful_trades if successful_trades > 0 else 0

    print(f"总预测次数: {total_predictions}")
    print(f"正确次数: {correct_predictions}")
    print(f"错误次数: {total_predictions - correct_predictions}")
    print(f"预测正确率: {accuracy:.2f}%")
    print(f"平均单次收益率: {avg_return:+.2f}%")
    print(f"累积收益率: {total_return:+.2f}%")

    # 保存回测结果
    backtest_result_file = f"./backtest_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(backtest_result_file, 'w', encoding='utf-8') as f:
        json.dump({
            "summary": {
                "total_predictions": total_predictions,
                "correct_predictions": correct_predictions,
                "accuracy": round(accuracy, 2),
                "average_return": round(avg_return, 2),
                "total_return": round(total_return, 2)
            },
            "details": results
        }, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 回测结果已保存: {backtest_result_file}")
    print("=" * 60)

    # 详细结果表格
    print("\n详细结果:")
    print("-" * 100)
    print(f"{'日期':<12} {'股票':<10} {'预测':<6} {'实际涨跌':<10} {'结果':<6} {'收益率':<10}")
    print("-" * 100)
    for r in results:
        result_symbol = "✓" if r['is_correct'] else "✗"
        print(f"{r['date']:<12} {r['stock_code']:<10} {r['prediction']:<6} "
              f"{r['actual_change']:+7.2f}%   {result_symbol:<6} {r['return_rate']:+7.2f}%")
    print("-" * 100)

if __name__ == "__main__":
    print("\n📊 日股预测回测系统\n")
    run_backtest()
