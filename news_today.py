import requests
from bs4 import BeautifulSoup
import json
import time
import os
import re
from datetime import datetime, timedelta
import sys

# 加载配置
from config import Config

# 验证配置
if not Config.validate():
    print("\n❌ 配置不完整，请检查 .env 文件")
    sys.exit(1)

# --- 使用配置 ---
QWEN_API_KEY = Config.QWEN_API_KEY
GEMINI_API_KEY = Config.GEMINI_API_KEY
MODEL_ID = Config.GEMINI_MODEL_ID

def get_save_dir():
    folder = f"report_{datetime.now().strftime('%Y%m%d')}"
    if not os.path.exists(folder):
        os.makedirs(folder)
    return folder

def is_weekend():
    """判断今天是否是周五/周六/周日"""
    return datetime.now().weekday() in [4, 5, 6]  # 4=周五, 5=周六, 6=周日

def get_next_trading_day(from_date=None):
    """获取下一个交易日"""
    if from_date is None:
        today = datetime.now()
    else:
        today = from_date

    next_day = today + timedelta(days=1)
    # 跳过周末
    while next_day.weekday() >= 5:
        next_day += timedelta(days=1)
    return next_day.strftime('%Y-%m-%d')

def get_weekend_cache_file():
    """获取周末缓存文件路径"""
    cache_dir = "./weekend_cache"
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    # 找到本周五的日期作为标识
    today = datetime.now()
    # 计算距离上一个或当前周五的天数
    days_since_friday = (today.weekday() - 4) % 7
    this_friday = today - timedelta(days=days_since_friday)

    return f"{cache_dir}/weekend_{this_friday.strftime('%Y%m%d')}.json"

# 1. 抓取模块
def fetch_80_titles():
    now = datetime.now()
    target_dt = now - timedelta(days=1) if now.hour < 3 else now
    target_date_short = target_dt.strftime('%-m/%-d')

    print(f"🎯 正在检索日期为 {target_date_short} 的新闻标题...")

    url = "https://finance.yahoo.co.jp/news/bus_all"
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}

    titles_pool = []
    for page in range(1, 6):
        try:
            res = requests.get(f"{url}?page={page}", headers=headers, timeout=30)
            soup = BeautifulSoup(res.text, 'html.parser')
            news_items = soup.select('a[href*="/news/detail/"]')
            for a in news_items:
                title = a.get_text(strip=True)
                parent = a.find_parent()
                time_text = parent.get_text() if parent else ""

                if (target_date_short in time_text) or (":" in time_text and "/" not in time_text):
                    if not any(t['title'] == title for t in titles_pool):
                        # 确保URL是完整的
                        href = a['href']
                        if href.startswith('/'):
                            href = f"https://finance.yahoo.co.jp{href}"
                        titles_pool.append({"title": title, "url": href})
            if len(titles_pool) >= 80: break
            time.sleep(1)
        except: break
    return titles_pool[:80]

# 2. Gemini 初筛
def gemini_stage1_filter(titles_list, target_count=20):
    print(f"⚡️ Gemini 2.5 Flash 正在高速初筛...")
    url = f"https://generativelanguage.googleapis.com/v1beta/{MODEL_ID}:generateContent?key={GEMINI_API_KEY}"
    context = "\n".join([f"ID {i}: {t['title']}" for i, t in enumerate(titles_list)])
    prompt = f"你是操盘手。从以下标题中选出影响明日股市的 {target_count} 条，只返回 ID 列表 [1, 2, 3]：\n{context}"

    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=300)
        if res.status_code != 200:
            print(f"❌ Gemini 初筛请求失败，状态码: {res.status_code}")
            sys.exit(1)

        raw_text = res.json()['candidates'][0]['content']['parts'][0]['text']
        ids = [int(i) for i in re.findall(r'\d+', raw_text)]
        return [titles_list[i] for i in ids if i < len(titles_list)][:target_count]
    except Exception as e:
        print(f"❌ 初筛异常: {e}")
        sys.exit(1)

# 3. 爬正文：支持长文本抓取
def fetch_content(url):
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')

        # 智能查找有效段落（过滤JavaScript、登录等无关内容）
        all_ps = soup.find_all('p')
        valid_paragraphs = []

        for p in all_ps:
            text = p.get_text().strip()
            # 过滤条件：长度>50，不包含常见的无关词
            if (len(text) > 50 and
                'JavaScript' not in text and
                'ログイン' not in text and
                'ポートフォリオ' not in text and
                '機能を利用' not in text):
                valid_paragraphs.append(text)

        if valid_paragraphs:
            full_text = "\n".join(valid_paragraphs)
            return full_text[:100000]

        # 备用方案：尝试特定选择器
        content_selectors = [
            'div[class*="article"] p',
            'div[class*="content"] p',
            'div[class*="body"] p',
            'article p'
        ]

        for selector in content_selectors:
            ps = soup.select(selector)
            if ps and len(ps) > 2:
                paragraphs = [p.get_text().strip() for p in ps if len(p.get_text().strip()) > 50]
                if paragraphs:
                    return "\n".join(paragraphs)[:100000]

        return ""
    except Exception as e:
        print(f"  ⚠️  抓取失败: {e}")
        return ""

# 4. Qwen 摘要
def qwen_summarize(title, content, max_retries=3):
    headers = {"Authorization": f"Bearer {QWEN_API_KEY}"}
    # 利用 Qwen3-8B 的 128K 上下文能力进行全文摘要
    payload = {
        "model": "Qwen/Qwen3-8B",
        "messages": [{"role": "user", "content": f"请为以下新闻写专业金融摘要（80字内）：\n标题：{title}\n正文：{content}"}]
    }

    for attempt in range(max_retries):
        try:
            res = requests.post("https://api.siliconflow.cn/v1/chat/completions",
                              json=payload, headers=headers, timeout=300)
            if res.status_code == 200:
                return res.json()['choices'][0]['message']['content']
            else:
                print(f"  ⚠️  Qwen API 返回错误: {res.status_code}, 重试 {attempt+1}/{max_retries}")
                time.sleep(2)
        except Exception as e:
            print(f"  ⚠️  Qwen API 调用异常: {e}, 重试 {attempt+1}/{max_retries}")
            time.sleep(2)

    return f"摘要生成失败: {title}"

# 5. Gemini 终极研判
def gemini_stage2_rank(summaries, target_date, max_retries=3):
    print("🏆 Gemini 终极研判...")
    # 利用 Gemini 2.5 Flash 的超大上下文容量进行全量分析
    prompt = f"""以下是全量财经新闻汇总：

{json.dumps(summaries, ensure_ascii=False)}

我正在进行日股回测，上面是给你的全量财经新闻汇总。请在不参考未来信息的情况下，完成以下任务：

核心矛盾识别：找出当日新闻中，对日本股市影响最大的 3 个宏观逻辑（例如：汇率、利率、或美股某板块的映射）。

个股狙击：基于以上逻辑，推导下一个交易日（{target_date}）最可能受益的推荐日本个股股票。

**重要要求**：
1. 必须是真实存在的、在东京证券交易所上市的大型股票（如丰田7203.T、索尼6758.T、软银9984.T、快速零售9983.T等）
2. 给出准确的Yahoo Finance股票代码格式（4位数字.T）
3. 给出具体推导逻辑

涨跌预测：请预测对应个股在下一个交易日的表现，**必须明确说明是"看涨"还是"看跌"**。

输出格式（严格按照此格式）：

宏观逻辑： ...

板块预测： 板块 A看多，理由...

核心个股： [股票代码，如7203.T]
股票名称： [公司名称]
预测方向： 看涨/看跌
理由： ...

风险提示： ..."""

    url = f"https://generativelanguage.googleapis.com/v1beta/{MODEL_ID}:generateContent?key={GEMINI_API_KEY}"

    for attempt in range(max_retries):
        try:
            # 增加timeout到300秒（5分钟），足够处理240条新闻
            res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=300)
            if res.status_code == 200:
                return res.json()['candidates'][0]['content']['parts'][0]['text']
            else:
                print(f"  ⚠️  Gemini API 返回错误: {res.status_code}, 重试 {attempt+1}/{max_retries}")
                time.sleep(3)
        except Exception as e:
            print(f"  ⚠️  Gemini API 调用异常: {e}, 重试 {attempt+1}/{max_retries}")
            time.sleep(3)

    print("❌ Gemini 终极研判失败")
    sys.exit(1)

# 6. 提取预测信息（支持多股票）
def extract_prediction(report_text):
    """
    从报告中提取股票代码和预测方向
    支持单个或多个股票预测
    返回格式:
        单个股票: {"stock_code": "8035.T", "direction": "看涨"}
        多个股票: [{"stock_code": "8035.T", "direction": "看涨"}, {...}]
    """

    # 查找所有股票代码和对应的预测
    predictions = []

    # 方法1：查找"核心个股"或"推荐股票"部分
    sections = re.split(r'(核心个股[：:]|核心個股[：:]|推荐股票[：:]|推薦股票[：:])', report_text)

    for i, section in enumerate(sections):
        if i == 0:
            continue

        # 获取这个section的内容（下一个元素）
        if i + 1 < len(sections):
            content = sections[i + 1]

            # 在这个content中查找股票代码
            stock_codes = re.findall(r'(\d{4}\.T)', content[:500])  # 只看前500字符

            # 查找预测方向（兼容简繁体）
            direction_matches = re.findall(r'(看涨|看跌|看漲)', content[:500])

            if stock_codes and direction_matches:
                # 可能有多个股票
                for j, code in enumerate(stock_codes[:3]):  # 最多取3个
                    direction = direction_matches[j] if j < len(direction_matches) else direction_matches[0]
                    predictions.append({
                        "stock_code": code,
                        "direction": direction.replace('漲', '涨')
                    })

    # 方法2：如果方法1没找到，使用全局搜索
    if not predictions:
        # 查找所有"预测方向"或"预测"模式
        pattern = r'(\d{4}\.T).*?(看涨|看跌|看漲)'
        matches = re.findall(pattern, report_text, re.DOTALL)

        for match in matches[:3]:  # 最多取3个
            predictions.append({
                "stock_code": match[0],
                "direction": match[1].replace('漲', '涨')
            })

    # 去重（保持顺序）
    seen = set()
    unique_predictions = []
    for p in predictions:
        key = p['stock_code']
        if key not in seen:
            seen.add(key)
            unique_predictions.append(p)

    # 返回格式：单个返回dict，多个返回list
    if len(unique_predictions) == 0:
        return None
    elif len(unique_predictions) == 1:
        return unique_predictions[0]
    else:
        return unique_predictions

# 7. 保存标准化预测数据
def save_prediction(date_str, target_date, report, prediction, news_count, is_weekend_data=False):
    """
    保存预测数据，格式化供回测使用
    如果当天已有预测，会自动覆盖（备份旧版本）
    """
    prediction_file = f"./predictions/prediction_{date_str}.json"
    os.makedirs("./predictions", exist_ok=True)

    # 如果文件已存在，先备份
    if os.path.exists(prediction_file):
        backup_dir = "./predictions/backup"
        os.makedirs(backup_dir, exist_ok=True)

        # 备份文件名包含时间戳
        backup_time = datetime.now().strftime('%H%M%S')
        backup_file = f"{backup_dir}/prediction_{date_str}_backup_{backup_time}.json"

        import shutil
        shutil.copy2(prediction_file, backup_file)
        print(f"⚠️  检测到已有预测，已备份到: {backup_file}")

    # 保存新预测（覆盖旧的）
    data = {
        "date": date_str,
        "target_date": target_date,
        "is_weekend": is_weekend_data,
        "news_count": news_count,
        "prediction": prediction,
        "full_report": report,
        "timestamp": datetime.now().isoformat(),
        "version": "latest"  # 标记为最新版本
    }

    with open(prediction_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ 预测数据已保存: {prediction_file}")
    print(f"   时间戳: {data['timestamp']}")
    print(f"   版本: 最新 (旧版本已备份)")

# 8. 周末模式：累积新闻
def handle_weekend_mode():
    """周末模式：累积周五/周六/周日的新闻"""
    cache_file = get_weekend_cache_file()

    # 读取现有缓存
    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            cached_data = json.load(f)
    else:
        cached_data = {"titles": [], "dates": []}

    # 抓取今天的80条新闻
    today_titles = fetch_80_titles()
    today_str = datetime.now().strftime('%Y-%m-%d')

    # 追加到缓存
    if today_str not in cached_data["dates"]:
        cached_data["titles"].extend(today_titles)
        cached_data["dates"].append(today_str)

        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cached_data, f, ensure_ascii=False, indent=2)

        print(f"✅ 周末模式：已累积 {len(today_titles)} 条新闻（总计 {len(cached_data['titles'])} 条）")

    # 检查是否到了周日晚上或周一凌晨，该处理了
    weekday = datetime.now().weekday()
    hour = datetime.now().hour

    # 周日晚上20点后 或 周一凌晨
    should_process = (weekday == 6 and hour >= 20) or (weekday == 0 and hour < 3)

    if should_process and len(cached_data["titles"]) > 0:
        print(f"🎯 周末模式：开始处理累积的 {len(cached_data['titles'])} 条新闻...")
        return cached_data["titles"], True, cached_data["dates"][0]
    else:
        print(f"⏳ 周末模式：等待更多数据... (当前 {len(cached_data['titles'])} 条)")
        return None, False, None

# --- 执行主程序 ---
if __name__ == "__main__":
    save_dir = get_save_dir()
    today_str = datetime.now().strftime('%Y-%m-%d')

    # 判断是否是周末模式
    if is_weekend():
        print("📅 检测到周末日期，启用周末模式...")
        all_titles, should_process, base_date = handle_weekend_mode()

        if not should_process:
            print("✅ 今日新闻已缓存，等待周末结束后统一处理。")
            sys.exit(0)

        # 周末模式：从240条中筛选20条
        print(f"✅ 抓取到 {len(all_titles)} 条周末累积标题。")
        top_20 = gemini_stage1_filter(all_titles, target_count=20)
        is_weekend_data = True
        date_for_save = base_date  # 使用周五的日期作为标识
    else:
        # 工作日模式
        print("📅 工作日模式...")
        all_titles = fetch_80_titles()
        print(f"✅ 抓取到 {len(all_titles)} 条标题。")
        top_20 = gemini_stage1_filter(all_titles, target_count=20)
        is_weekend_data = False
        date_for_save = today_str

    print(f"✅ 初筛 {len(top_20)} 条潜力新闻完成。")

    # 3 & 4. 爬全文并由 Qwen 总结
    summaries = []
    for i, item in enumerate(top_20):
        print(f"[{i+1}/{len(top_20)}] 正在深度解析正文并生成摘要: {item['title'][:15]}...")
        raw_text = fetch_content(item['url'])
        if raw_text:
            summary = qwen_summarize(item['title'], raw_text)
            summaries.append({"title": item['title'], "summary": summary})
            time.sleep(1.5)
        else:
            print(f"  ⚠️  未能获取正文内容，跳过")

    print(f"\n✅ 成功生成 {len(summaries)} 条新闻摘要")

    # 5. 最终研判
    if summaries:
        print(f"开始生成最终研判报告...")
        target_date = get_next_trading_day()
        report = gemini_stage2_rank(summaries, target_date)

        # 提取预测信息
        prediction = extract_prediction(report)

        if prediction:
            # 判断是单个还是多个股票
            if isinstance(prediction, list):
                print(f"\n🎯 预测结果（{len(prediction)}只股票）:")
                for i, p in enumerate(prediction, 1):
                    print(f"  {i}. {p['stock_code']} - {p['direction']}")
            else:
                print(f"\n🎯 预测结果: {prediction['stock_code']} - {prediction['direction']}")
        else:
            print(f"\n⚠️  未能从报告中提取明确的预测信息")

        # 保存传统报告
        report_path = f"{save_dir}/final_report.txt"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)

        # 保存标准化预测数据供回测使用
        save_prediction(
            date_str=date_for_save,
            target_date=target_date,
            report=report,
            prediction=prediction,
            news_count=len(summaries),
            is_weekend_data=is_weekend_data
        )

        print(f"\n🔥 全流程结束！报告已生成: {report_path}")
        print("-" * 30)
        print(report[:500] + "...")

        # 如果是周末模式，清理缓存
        if is_weekend_data:
            cache_file = get_weekend_cache_file()
            if os.path.exists(cache_file):
                os.remove(cache_file)
                print("✅ 周末缓存已清理")
