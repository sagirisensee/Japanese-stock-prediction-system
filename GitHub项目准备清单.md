# 🎉 GitHub项目准备就绪

## ✅ 已完成的工作

### 1. 环境配置管理
- ✅ `.env.example` - 配置模板
- ✅ `.gitignore` - Git忽略规则
- ✅ `config.py` - 配置加载模块
- ✅ `requirements.txt` - Python依赖
- ✅ 更新 `news_today.py` 使用环境变量

### 2. 项目文档
- ✅ `README.md` - 完整的项目文档
- ✅ `服务器协作方案.md` - 3种同步方案详解

### 3. 安全措施
- ✅ API密钥不会被提交到Git
- ✅ 结果文件不会被提交
- ✅ 使用.env管理敏感信息

---

## 📁 当前文件清单

### 需要提交的（代码）
```
news-prediction/
├── news_today.py           ✅ 主预测脚本（已更新使用环境变量）
├── backtest.py             ✅ 回测脚本
├── config.py               ✅ 配置管理（新增）
├── manage_predictions.py   ✅ 预测管理工具
├── requirements.txt        ✅ Python依赖（新增）
├── .env.example           ✅ 配置模板（新增）
├── .gitignore             ✅ Git忽略规则（新增）
├── README.md              ✅ 项目文档（新增）
├── 服务器协作方案.md       ✅ 部署方案（新增）
├── predictions/.gitkeep   ✅ 目录占位符
└── logs/.gitkeep          ✅ 目录占位符
```

### 不提交的（结果/敏感）
```
.env                       ❌ 实际配置（包含密钥）
predictions/*.json         ❌ 预测数据
report_*/                  ❌ 报告文件
backtest_result_*.json     ❌ 回测结果
weekend_cache/             ❌ 周末缓存
logs/*.log                 ❌ 日志文件
```

---

## 🚀 推荐的服务器+本地方案

### 方案选择建议

#### ⭐ 推荐：Git Results分支
**适合场景**:
- 数据量不大（每天几MB）
- 想要版本控制和历史记录
- 不想配置额外服务

**优点**:
- 免费使用GitHub
- 自动备份
- 本地同步简单

**实施步骤**:
见下文"详细步骤"

#### 备选：rsync同步
**适合场景**:
- 有服务器SSH权限
- 数据量较大
- 需要快速同步

---

## 📋 详细步骤（Git Results分支方案）

### A. 服务器端设置

#### 1. 克隆项目
```bash
git clone https://github.com/yourusername/news-prediction.git news
cd news
```

#### 2. 配置环境
```bash
# 复制配置模板
cp .env.example .env

# 编辑配置（填入API密钥）
nano .env
```

编辑`.env`:
```env
QWEN_API_KEY=sk-your-actual-key-here
GEMINI_API_KEY=AIza-your-actual-key-here
GEMINI_MODEL_ID=models/gemini-2.5-flash
GEMINI_TIMEOUT=300
```

#### 3. 安装依赖
```bash
pip install -r requirements.txt
```

#### 4. 验证配置
```bash
python3 config.py
# 应该看到: ✅ 配置验证通过
```

#### 5. 初始化results分支
```bash
# 创建独立的results分支
git checkout --orphan results
git rm -rf .

# 创建目录结构
mkdir -p predictions reports backtest_results
touch predictions/.gitkeep
touch reports/.gitkeep
touch backtest_results/.gitkeep

# 创建results分支专用的.gitignore
cat > .gitignore << 'EOF'
.DS_Store
*.log
.env
__pycache__/
*.pyc
weekend_cache/
EOF

# 提交并推送
git add .
git commit -m "Initialize results branch"
git push origin results

# 切回main分支
git checkout main
```

#### 6. 创建结果推送脚本
```bash
cat > push_results.sh << 'EOF'
#!/bin/bash
cd ~/news

# 保存当前分支
CURRENT_BRANCH=$(git branch --show-current)

# 切换到results分支
git checkout results

# 复制结果文件
cp predictions/prediction_*.json predictions/ 2>/dev/null || true
cp -r report_*/* reports/ 2>/dev/null || true
cp backtest_result_*.json backtest_results/ 2>/dev/null || true

# 提交并推送
git add predictions/ reports/ backtest_results/
git commit -m "Update results: $(date '+%Y-%m-%d %H:%M:%S')" || true
git push origin results

# 切回原分支
git checkout $CURRENT_BRANCH

echo "✅ 结果已推送到GitHub (results分支)"
EOF

chmod +x push_results.sh
```

#### 7. 设置crontab
```bash
crontab -e
```

添加以下内容:
```cron
# 创建日志目录
@reboot mkdir -p ~/news/logs

# 工作日：每天0点运行预测，5分钟后推送
0 0 * * 1-5 cd ~/news && python3 news_today.py >> logs/news.log 2>&1
5 0 * * 1-5 cd ~/news && ./push_results.sh >> logs/push.log 2>&1

# 周末：每天0点累积新闻
0 0 * * 5-7 cd ~/news && python3 news_today.py >> logs/news.log 2>&1

# 周一1点处理周末+推送
0 1 * * 1 cd ~/news && python3 news_today.py >> logs/news.log 2>&1
5 1 * * 1 cd ~/news && ./push_results.sh >> logs/push.log 2>&1

# 每周日0点运行回测
0 0 * * 0 cd ~/news && python3 backtest.py >> logs/backtest.log 2>&1
5 0 * * 0 cd ~/news && ./push_results.sh >> logs/push.log 2>&1
```

### B. 本地端设置

#### 1. 克隆主分支（代码）
```bash
git clone https://github.com/yourusername/news-prediction.git news
cd news
```

#### 2. 设置results工作树（结果）
```bash
# 在单独目录查看results分支
git worktree add ../news-results results

# 现在你有两个目录：
# ~/news/          - main分支（代码）
# ~/news-results/  - results分支（结果）
```

#### 3. 创建同步脚本
```bash
# 在news目录创建
cat > pull_results.sh << 'EOF'
#!/bin/bash

echo "🔄 正在同步预测结果..."

cd ~/news-results
git pull origin results

echo ""
echo "✅ 同步完成！"
echo ""
echo "📊 最新预测:"
ls -lt predictions/*.json 2>/dev/null | head -5 | awk '{print "  " $9}'
echo ""
echo "📈 回测结果:"
ls -lt backtest_results/*.json 2>/dev/null | head -3 | awk '{print "  " $9}'
EOF

chmod +x pull_results.sh
```

#### 4. 使用
```bash
# 同步结果
./pull_results.sh

# 查看最新预测
cat ~/news-results/predictions/prediction_2026-02-05.json

# 查看回测结果
cat ~/news-results/backtest_results/backtest_result_*.json
```

---

## 🎯 日常工作流程

### 服务器端（自动）
```
每天 0:00  → 运行预测
每天 0:05  → 推送结果到GitHub
每周日0:00 → 运行回测
每周日0:05 → 推送回测结果
```

### 本地端（手动）
```bash
# 方式1: 快速查看
./pull_results.sh

# 方式2: 手动同步
cd ~/news-results
git pull origin results

# 方式3: 查看具体文件
cat ~/news-results/predictions/prediction_2026-02-05.json
```

---

## 📊 数据流示意图

```
服务器
  ↓
运行 news_today.py
  ↓
生成 predictions/prediction_2026-02-05.json
  ↓
push_results.sh
  ↓
GitHub (results分支)
  ↓
本地 pull_results.sh
  ↓
~/news-results/predictions/
```

---

## 🔍 验证检查清单

### 服务器端
- [ ] git配置正确（user.name, user.email）
- [ ] .env文件存在且包含API密钥
- [ ] python3 config.py 验证通过
- [ ] results分支已创建并推送
- [ ] push_results.sh 可执行
- [ ] crontab已配置

### 本地端
- [ ] main分支克隆成功
- [ ] results工作树创建成功
- [ ] pull_results.sh可执行
- [ ] 可以正常拉取results分支

### 测试
```bash
# 服务器：手动运行一次
python3 news_today.py
./push_results.sh

# 本地：同步并查看
./pull_results.sh
ls ~/news-results/predictions/
```

---

## ⚠️ 常见问题

### Q1: push_results.sh失败
**A:** 检查git配置和SSH密钥
```bash
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
ssh -T git@github.com  # 测试SSH连接
```

### Q2: results分支看不到
**A:** 确保已推送
```bash
git checkout results
git push -u origin results
git checkout main
```

### Q3: 本地同步很慢
**A:** 考虑使用rsync方案（见 服务器协作方案.md）

### Q4: .env文件被提交了
**A:** 立即删除并重新提交
```bash
git rm --cached .env
git commit -m "Remove .env file"
git push
# 然后修改API密钥（已泄露）
```

---

## 📝 下一步

1. **推送到GitHub**
   ```bash
   cd ~/news
   git add .
   git commit -m "Initial commit: Stock prediction system"
   git push origin main
   ```

2. **部署到服务器**
   - 按照上述"服务器端设置"操作

3. **本地配置**
   - 按照上述"本地端设置"操作

4. **开始使用**
   - 等待服务器自动运行
   - 或手动测试一次

---

**准备时间**: 2026-02-05
**状态**: ✅ 就绪
**下一步**: 推送到GitHub并部署
