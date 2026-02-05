# 🎯 日股新闻预测与回测系统

基于雅虎财经新闻和AI模型的日本股市预测系统，支持自动化预测和历史回测。

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ 特性

- 🤖 **AI驱动**: 使用Gemini 2.5 Flash和Qwen3-8B进行新闻分析
- 📊 **智能预测**: 从80条新闻中筛选20条核心信息，预测股票涨跌
- 🔄 **周末模式**: 自动累积周末240条新闻，周一统一分析
- 📈 **回测系统**: 自动计算历史预测的正确率和收益率
- 🔐 **安全配置**: 使用.env管理敏感信息
- 🌐 **远程协作**: 支持服务器运行+本地查看

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/yourusername/news-prediction.git
cd news-prediction
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env 填入你的API密钥
nano .env
```

`.env` 示例：
```env
QWEN_API_KEY=your_qwen_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL_ID=models/gemini-2.5-flash
GEMINI_TIMEOUT=300
```

### 4. 验证配置

```bash
python3 config.py
```

### 5. 运行预测

```bash
# 生成今日预测
python3 news_today.py

# 运行回测
python3 backtest.py
```

## 📁 项目结构

```
news-prediction/
├── news_today.py           # 主预测脚本
├── backtest.py             # 回测脚本
├── config.py               # 配置管理
├── manage_predictions.py   # 预测管理工具
├── requirements.txt        # Python依赖
├── .env.example           # 配置模板
├── .env                   # 实际配置（不提交）
├── .gitignore             # Git忽略规则
├── README.md              # 项目文档
│
├── predictions/           # 预测数据（不提交）
├── reports/              # 分析报告（不提交）
└── logs/                 # 日志文件（不提交）
```

## 🔧 使用说明

### 日常预测

```bash
# 手动运行
python3 news_today.py

# 或设置定时任务（crontab）
0 0 * * * cd ~/news-prediction && python3 news_today.py
```

### 历史回测

```bash
# 回测所有历史预测
python3 backtest.py

# 查看回测结果
cat backtest_result_*.json
```

### 管理预测

```bash
# 查看所有预测
python3 manage_predictions.py

# 验证唯一性
python3 manage_predictions.py verify

# 清理旧备份（保留7天）
python3 manage_predictions.py clean 7
```

## 📊 数据格式

### 预测数据
```json
{
  "date": "2026-02-05",
  "target_date": "2026-02-06",
  "prediction": {
    "stock_code": "8035.T",
    "direction": "看涨"
  },
  "news_count": 20,
  "timestamp": "2026-02-05T12:00:00"
}
```

### 回测结果
```json
{
  "summary": {
    "total_predictions": 30,
    "correct_predictions": 18,
    "accuracy": 60.0,
    "average_return": 1.25,
    "total_return": 37.5
  },
  "details": [...]
}
```

## 🌐 服务器部署

### 方案1: 使用Git Results分支（推荐）

**服务器端：**
```bash
# 初始化results分支
git checkout --orphan results
git rm -rf .
mkdir -p predictions reports
git add .
git commit -m "Initialize results"
git push origin results

# 设置自动推送
cat > push_results.sh << 'EOF'
#!/bin/bash
git checkout results
cp -r predictions/* predictions/
git add predictions/
git commit -m "Update: $(date)"
git push origin results
git checkout main
EOF

chmod +x push_results.sh

# 添加到crontab
crontab -e
0 0 * * * cd ~/news-prediction && python3 news_today.py
5 0 * * * cd ~/news-prediction && ./push_results.sh
```

**本地端：**
```bash
# 克隆并设置worktree
git clone https://github.com/yourusername/news-prediction.git
cd news-prediction
git worktree add ../news-results results

# 同步结果
cd ../news-results
git pull origin results
```

### 方案2: 使用rsync同步

**本地端：**
```bash
# 创建同步脚本
cat > sync_from_server.sh << 'EOF'
#!/bin/bash
rsync -avz user@server:~/news-prediction/predictions/ ./predictions/
EOF

chmod +x sync_from_server.sh
./sync_from_server.sh
```

详细部署方案见 [服务器协作方案.md](服务器协作方案.md)

## 🎨 功能特性

### 周末模式
- 周五/六/日每天抓取80条新闻
- 累积到240条
- 周日晚或周一凌晨统一处理
- 预测周一股市表现

### 多股票支持
- 支持预测单个或多个股票
- 自动提取股票代码和方向
- 回测时逐个计算收益率

### 智能备份
- 同一天多次运行自动覆盖
- 旧版本自动备份到backup/
- 回测只使用最新预测

## 📈 系统架构

```
雅虎财经新闻
    ↓
抓取80条标题
    ↓
Gemini初筛20条
    ↓
抓取完整正文
    ↓
Qwen生成摘要
    ↓
Gemini终极研判
    ↓
提取预测 → predictions/
    ↓
生成报告 → reports/
```

## 🔐 安全说明

- ✅ API密钥使用.env文件管理
- ✅ .env文件已加入.gitignore
- ✅ 使用.env.example作为模板
- ⚠️ 不要提交.env到Git
- ⚠️ 不要在代码中硬编码密钥

## 📝 注意事项

1. **API限制**: 注意API调用频率限制
2. **数据延迟**: yfinance数据可能有延迟
3. **仅供参考**: 预测结果仅供学习研究
4. **风险自负**: 股市有风险，投资需谨慎

## 🛠️ 故障排查

### 配置问题
```bash
# 验证配置
python3 config.py

# 检查环境变量
python3 -c "from config import Config; Config.print_config()"
```

### 依赖问题
```bash
# 重新安装依赖
pip install -r requirements.txt --upgrade
```

### 预测问题
```bash
# 查看日志
tail -f logs/news.log

# 手动测试
python3 test_fetch.py
```

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

- [Gemini 2.5 Flash](https://ai.google.dev/) - AI新闻分析
- [Qwen3-8B](https://www.siliconflow.cn/) - 新闻摘要生成
- [yfinance](https://github.com/ranaroussi/yfinance) - 股票数据获取

---

**Star ⭐ 如果这个项目对你有帮助！**
