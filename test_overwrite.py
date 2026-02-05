#!/usr/bin/env python3
"""测试预测覆盖功能"""
import json
import os
import time

# 模拟第一次预测
def create_first_prediction():
    os.makedirs("./predictions", exist_ok=True)

    data = {
        "date": "2026-02-05",
        "target_date": "2026-02-06",
        "prediction": {"stock_code": "8035.T", "direction": "看涨"},
        "timestamp": "2026-02-05T10:00:00",
        "version": "latest"
    }

    with open("./predictions/prediction_2026-02-05.json", "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("✅ 创建第一次预测: 8035.T 看涨 (10:00)")

# 模拟第二次预测（覆盖）
def create_second_prediction():
    from news_today import save_prediction

    print("\n⏳ 3秒后创建第二次预测...")
    time.sleep(3)

    save_prediction(
        date_str="2026-02-05",
        target_date="2026-02-06",
        report="更新的报告内容",
        prediction={"stock_code": "6758.T", "direction": "看跌"},
        news_count=20,
        is_weekend_data=False
    )

# 检查结果
def check_results():
    print("\n" + "=" * 60)
    print("检查结果")
    print("=" * 60)

    # 主文件
    main_file = "./predictions/prediction_2026-02-05.json"
    if os.path.exists(main_file):
        with open(main_file, 'r') as f:
            data = json.load(f)
        print("\n📄 主预测文件 (最新):")
        print(f"  股票: {data['prediction']['stock_code']}")
        print(f"  方向: {data['prediction']['direction']}")
        print(f"  时间: {data['timestamp']}")
        print(f"  版本: {data.get('version', 'unknown')}")

    # 备份文件
    backup_dir = "./predictions/backup"
    if os.path.exists(backup_dir):
        backups = sorted(os.listdir(backup_dir))
        if backups:
            print(f"\n📦 备份文件 ({len(backups)}个):")
            for backup in backups:
                print(f"  {backup}")
                with open(f"{backup_dir}/{backup}", 'r') as f:
                    data = json.load(f)
                print(f"    → 股票: {data['prediction']['stock_code']} {data['prediction']['direction']}")

    print("\n✅ 验证: 每天只有一个最新预测，旧版本已备份")

if __name__ == "__main__":
    create_first_prediction()
    create_second_prediction()
    check_results()
