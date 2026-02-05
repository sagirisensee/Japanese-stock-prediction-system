#!/bin/bash

echo "=========================================="
echo "日股预测回测系统 - 环境配置"
echo "=========================================="
echo ""

# 检查 Python 版本
echo "检查 Python 版本..."
python3 --version
if [ $? -ne 0 ]; then
    echo "❌ 未找到 Python 3，请先安装 Python 3"
    exit 1
fi
echo "✅ Python 3 已安装"
echo ""

# 安装依赖
echo "安装 Python 依赖包..."
pip3 install -q requests beautifulsoup4 yfinance
if [ $? -eq 0 ]; then
    echo "✅ 依赖安装完成"
else
    echo "❌ 依赖安装失败"
    exit 1
fi
echo ""

# 创建必要的目录
echo "创建必要的目录..."
mkdir -p predictions
mkdir -p weekend_cache
mkdir -p logs
echo "✅ 目录创建完成"
echo ""

# 测试 API 密钥
echo "检查配置文件..."
if grep -q "your_qwen_api_key\|your_gemini_api_key" news_today.py; then
    echo "⚠️  警告: 请在 news_today.py 中配置你的 API 密钥"
    echo "   QWEN_API_KEY 和 GEMINI_API_KEY"
else
    echo "✅ API 密钥已配置"
fi
echo ""

# 显示 crontab 配置建议
echo "=========================================="
echo "✅ 环境配置完成！"
echo "=========================================="
echo ""
echo "建议的 crontab 配置："
echo ""
echo "# 编辑 crontab"
echo "crontab -e"
echo ""
echo "# 添加以下定时任务："
echo "# 工作日每天凌晨 0:00"
echo "0 0 * * 1-5 cd $(pwd) && python3 news_today.py >> logs/news.log 2>&1"
echo ""
echo "# 周末每天凌晨 0:00 (累积新闻)"
echo "0 0 * * 5-7 cd $(pwd) && python3 news_today.py >> logs/news.log 2>&1"
echo ""
echo "# 周一凌晨 1:00 (处理周末新闻)"
echo "0 1 * * 1 cd $(pwd) && python3 news_today.py >> logs/news.log 2>&1"
echo ""
echo "=========================================="
echo ""
echo "测试系统："
echo "  1. 创建测试数据: python3 create_test_data.py"
echo "  2. 运行回测: python3 backtest.py"
echo ""
echo "手动运行预测："
echo "  python3 news_today.py"
echo ""
