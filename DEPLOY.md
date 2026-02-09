# Ubuntu 服务器部署指南

## 周末模式说明

**周末模式工作流程：**
1. **周五晚上 00:05** - 抓取周五的80条新闻并缓存
2. **周六晚上 00:05** - 抓取周六的80条新闻并追加到缓存
3. **周日晚上 00:05** - 抓取周日的80条新闻并追加到缓存
4. **周一凌晨 00:05** - 处理周末累积的240条新闻，生成预测

## 部署步骤

### 1. 确认服务器上的项目路径

```bash
# SSH登录服务器
ssh ubuntu@your-server-ip

# 找到项目目录
ls -la /home/ubuntu/

# 如果目录名是 Japanese-stock-prediction-system
cd /home/ubuntu/Japanese-stock-prediction-system

# 或者如果是其他名称，记住这个路径
PROJECT_DIR="/home/ubuntu/Japanese-stock-prediction-system"
```

**重要**：后续所有操作都要使用你的实际项目路径！

### 2. 上传修改的文件到服务器

```bash
# 在本地Mac执行（替换成你的实际路径和IP）
cd /Users/yunkaichen/Downloads/news

# 上传文件（替换 PROJECT_DIR 为实际路径）
scp news_today.py run_daily.sh DEPLOY.md test_weekend_mode.py \
    ubuntu@your-ip:/home/ubuntu/Japanese-stock-prediction-system/
```

### 3. 在服务器上配置环境

```bash
# SSH登录服务器
ssh ubuntu@your-server-ip

# 进入项目目录（替换为实际路径）
cd /home/ubuntu/Japanese-stock-prediction-system

# 确认文件已上传
ls -la news_today.py run_daily.sh

# 给运行脚本执行权限
chmod +x run_daily.sh

# 测试脚本（先手动运行一次）
bash run_daily.sh
```

### 4. 配置 Crontab

```bash
# 编辑crontab
crontab -e

# 添加以下任务（注意：替换为你的实际项目路径！）
5 0 * * * /home/ubuntu/Japanese-stock-prediction-system/run_daily.sh >> /home/ubuntu/daily_cron.log 2>&1

# 保存并退出（nano编辑器按 Ctrl+X, Y, Enter）
```

**关键点**：
- ✅ 使用**绝对路径**调用 `run_daily.sh`
- ✅ 脚本会自动切换到正确的工作目录
- ✅ 脚本会检查并确保在 main 分支上运行

**重要说明：**
- 只需要配置**一个**cron任务
- 脚本会自动判断是工作日还是周末模式
- 周末会累积新闻，周一会统一处理

### 4. 查看日志

```bash
# 查看最新的运行日志
tail -n 100 /home/ubuntu/daily_cron.log

# 实时监控日志
tail -f /home/ubuntu/daily_cron.log
```

### 5. 手动测试

```bash
# 测试完整流程
cd /home/ubuntu/news
bash run_daily.sh

# 只测试预测生成
python3 news_today.py

# 只测试回测
python3 backtest.py
```

## 目录结构

```
/home/ubuntu/news/
├── news_today.py           # 主程序
├── backtest.py             # 回测程序
├── config.py               # 配置文件
├── run_daily.sh            # 每日运行脚本
├── push_results.sh         # 推送结果脚本
├── setup.sh                # 环境配置脚本
├── .env                    # API密钥（需要手动创建）
├── predictions/            # 预测结果目录
├── weekend_cache/          # 周末缓存目录
└── report_YYYYMMDD/        # 报告目录
```

## 常见问题

### Q1: 如何检查 cron 是否正常运行？

```bash
# 查看cron服务状态
sudo systemctl status cron

# 查看最近的执行日志
grep CRON /var/log/syslog | tail -20
```

### Q2: 周末模式没有生成预测？

**原因分析：**
- 周末（周五/六/日）运行时只会累积新闻，不会生成预测
- 只有在**周一凌晨0:05**运行时才会处理周末新闻并生成预测

**检查步骤：**
```bash
# 1. 检查周末缓存文件是否存在
ls -la /home/ubuntu/news/weekend_cache/

# 2. 查看缓存内容
cat /home/ubuntu/news/weekend_cache/weekend_*.json | head -50

# 3. 查看日志，确认周一是否正常处理
grep "周末模式：开始处理" /home/ubuntu/daily_cron.log
```

### Q3: 路径错误问题？

**错误示例：**
```
python3: can't open file '/home/ubuntu/Japanese-stock-prediction-system/backtest.py': [Errno 2] No such file or directory
```

**可能的原因：**

1. **在错误的分支上**：
   - results 分支只有结果文件，没有 Python 代码
   - 必须在 main 分支上运行 Python 脚本

2. **cron 没有使用绝对路径**：
   - ❌ 错误：`5 0 * * * cd /some/path && python3 news_today.py`
   - ✅ 正确：`5 0 * * * /full/path/to/run_daily.sh >> /path/to/log 2>&1`

3. **push_results.sh 没有正确切回 main 分支**：
   - 检查脚本是否执行完整
   - 查看是否有错误导致提前退出

**解决步骤：**

```bash
# 1. 检查当前分支
cd /home/ubuntu/Japanese-stock-prediction-system
git branch --show-current

# 2. 如果不在 main 分支，切换回去
git checkout main

# 3. 确认 Python 文件存在
ls -la *.py

# 4. 测试运行脚本
bash run_daily.sh

# 5. 检查 crontab 配置
crontab -l

# 6. 确保使用绝对路径
# 应该是这样：
5 0 * * * /home/ubuntu/Japanese-stock-prediction-system/run_daily.sh >> /home/ubuntu/daily_cron.log 2>&1
```

**run_daily.sh 的保护机制：**

我们更新后的 `run_daily.sh` 包含了以下保护：
- ✅ 自动检测并切换到 main 分支
- ✅ 检查文件是否存在再执行
- ✅ 显示当前分支信息（方便排查）
- ✅ 使用脚本所在目录作为工作目录

## 时间线示例

假设今天是2026年2月7日（周五）：

| 时间 | 动作 | 说明 |
|------|------|------|
| 2/7 00:05 | 抓取周五80条新闻 | 存入 weekend_cache/weekend_20260207.json |
| 2/8 00:05 | 抓取周六80条新闻 | 追加到缓存（总计160条） |
| 2/9 00:05 | 抓取周日80条新闻 | 追加到缓存（总计240条） |
| 2/10 00:05 | **处理240条新闻** | 生成预测，清理缓存 |
| 2/11 00:05 | 正常工作日流程 | 抓取80条，直接处理 |

## 监控建议

```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
alias check-news="tail -100 /home/ubuntu/daily_cron.log"
alias watch-news="tail -f /home/ubuntu/daily_cron.log"
```
