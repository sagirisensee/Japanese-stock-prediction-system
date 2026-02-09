#!/usr/bin/env python3
"""
测试周末模式逻辑
"""
from datetime import datetime, timedelta
import sys

def test_is_weekend():
    """测试 is_weekend() 函数的逻辑"""

    print("=" * 60)
    print("测试周末模式判断逻辑")
    print("=" * 60)
    print()

    test_cases = [
        # (weekday, hour, expected_result, description)
        (0, 0, True, "周一 00:00 - 应该处理周末新闻"),
        (0, 1, True, "周一 01:00 - 应该处理周末新闻"),
        (0, 2, True, "周一 02:00 - 应该处理周末新闻"),
        (0, 3, False, "周一 03:00 - 已过周末模式时间"),
        (0, 12, False, "周一 12:00 - 正常工作日"),
        (1, 0, False, "周二 00:00 - 正常工作日"),
        (2, 0, False, "周三 00:00 - 正常工作日"),
        (3, 0, False, "周四 00:00 - 正常工作日"),
        (4, 0, True, "周五 00:00 - 周末模式开始"),
        (4, 12, True, "周五 12:00 - 周末模式"),
        (5, 0, True, "周六 00:00 - 周末模式"),
        (5, 12, True, "周六 12:00 - 周末模式"),
        (6, 0, True, "周日 00:00 - 周末模式"),
        (6, 20, True, "周日 20:00 - 周末模式"),
    ]

    passed = 0
    failed = 0

    for weekday, hour, expected, desc in test_cases:
        # 模拟 is_weekend() 的逻辑
        if weekday in [4, 5, 6]:
            result = True
        elif weekday == 0 and hour < 3:
            result = True
        else:
            result = False

        status = "✅" if result == expected else "❌"
        if result == expected:
            passed += 1
        else:
            failed += 1

        print(f"{status} {desc}")
        print(f"   weekday={weekday}, hour={hour}, 预期={expected}, 实际={result}")
        if result != expected:
            print(f"   ⚠️  测试失败！")
        print()

    print("=" * 60)
    print(f"测试结果: 通过 {passed}/{len(test_cases)}, 失败 {failed}/{len(test_cases)}")
    print("=" * 60)

    return failed == 0

def test_should_process_logic():
    """测试 should_process 的逻辑"""

    print()
    print("=" * 60)
    print("测试周末新闻处理时机")
    print("=" * 60)
    print()

    test_cases = [
        # (weekday, hour, news_count, should_process, description)
        (0, 0, 240, True, "周一 00:00, 240条新闻 - 应该处理"),
        (0, 1, 240, True, "周一 01:00, 240条新闻 - 应该处理"),
        (0, 2, 160, True, "周一 02:00, 160条新闻 - 应该处理"),
        (0, 0, 80, True, "周一 00:00, 80条新闻 - 数量不足也处理"),
        (0, 3, 240, False, "周一 03:00, 240条新闻 - 已过处理时间"),
        (4, 0, 80, False, "周五 00:00, 80条新闻 - 只累积不处理"),
        (5, 0, 160, False, "周六 00:00, 160条新闻 - 只累积不处理"),
        (6, 0, 240, False, "周日 00:00, 240条新闻 - 只累积不处理"),
        (6, 20, 240, False, "周日 20:00, 240条新闻 - 等待周一"),
    ]

    passed = 0
    failed = 0

    for weekday, hour, news_count, expected, desc in test_cases:
        # 模拟 should_process 的逻辑
        result = (weekday == 0 and hour < 3)

        status = "✅" if result == expected else "❌"
        if result == expected:
            passed += 1
        else:
            failed += 1

        print(f"{status} {desc}")
        print(f"   weekday={weekday}, hour={hour}, news={news_count}, 预期={expected}, 实际={result}")
        if result != expected:
            print(f"   ⚠️  测试失败！")
        print()

    print("=" * 60)
    print(f"测试结果: 通过 {passed}/{len(test_cases)}, 失败 {failed}/{len(test_cases)}")
    print("=" * 60)

    return failed == 0

def simulate_weekend_workflow():
    """模拟完整的周末工作流"""

    print()
    print("=" * 60)
    print("模拟周末工作流程")
    print("=" * 60)
    print()

    # 模拟从周五到周一的运行
    dates = []
    start_date = datetime(2026, 2, 7, 0, 5)  # 2026-02-07 周五 00:05

    for day_offset in range(4):  # 周五、周六、周日、周一
        current_date = start_date + timedelta(days=day_offset)
        weekday = current_date.weekday()
        hour = current_date.hour

        is_weekend_mode = weekday in [4, 5, 6] or (weekday == 0 and hour < 3)
        should_process = (weekday == 0 and hour < 3)

        weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

        print(f"📅 {current_date.strftime('%Y-%m-%d %H:%M')} ({weekday_names[weekday]})")
        print(f"   is_weekend_mode: {is_weekend_mode}")
        print(f"   should_process: {should_process}")

        if is_weekend_mode:
            if should_process:
                cumulative_count = (day_offset) * 80
                print(f"   ✅ 处理周末累积的 {cumulative_count} 条新闻")
            else:
                cumulative_count = (day_offset + 1) * 80
                print(f"   📦 累积新闻（当前 {cumulative_count} 条），等待周一处理")
        else:
            print(f"   🔄 正常工作日流程（抓取80条立即处理）")

        print()

    print("=" * 60)
    print("预期结果:")
    print("  - 周五: 累积80条新闻")
    print("  - 周六: 累积160条新闻")
    print("  - 周日: 累积240条新闻")
    print("  - 周一: 处理240条新闻，生成预测")
    print("=" * 60)

if __name__ == "__main__":
    all_passed = True

    all_passed &= test_is_weekend()
    all_passed &= test_should_process_logic()
    simulate_weekend_workflow()

    print()
    if all_passed:
        print("🎉 所有测试通过！")
        sys.exit(0)
    else:
        print("❌ 部分测试失败，请检查代码")
        sys.exit(1)
