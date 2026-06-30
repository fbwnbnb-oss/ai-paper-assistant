# AI Paper Assistant

每日自动从 arXiv 获取 10 篇 AI Agent 相关论文的本地学习助手。

## 功能特性

- 🔍 自动从 arXiv 抓取 AI Agent 相关论文
- 🎯 智能关键词匹配和相关度评分
- 📅 按日期浏览历史推荐
- ✓ 标记已读/未读状态
- ⭐ 收藏感兴趣的论文
- 🔄 每天自动更新（早上 8 点）
- 💻 本地运行，无需服务器

## 安装

```bash
cd ~/ai-paper-assistant
pip install -r requirements.txt
```

## 使用

启动应用：

```bash
python app.py
```

然后在浏览器中打开：http://localhost:5000

## 工作原理

1. **论文获取**：从 arXiv API 搜索 cs.AI、cs.MA、cs.CL、cs.LG 等分类的最新论文
2. **关键词匹配**：使用加权关键词系统评估论文与 AI Agent 的相关性
   - 高权重：agent, multi-agent, LLM agent, MCP, tool use
   - 中权重：planning, reasoning, RAG, chain-of-thought
   - 基础权重：LLM, GPT, fine-tuning
3. **智能排序**：按相关度评分选出 Top 10 论文
4. **本地存储**：使用 SQLite 数据库保存论文和阅读状态

## 项目结构

```
ai-paper-assistant/
├── app.py              # Flask 主应用
├── fetcher.py          # arXiv 论文抓取
├── models.py           # 数据库模型
├── requirements.txt    # Python 依赖
├── templates/          # HTML 模板
│   ├── base.html
│   ├── index.html
│   └── paper.html
└── static/
    └── style.css       # 样式文件
```

## 关键词配置

可以在 `fetcher.py` 中修改 `KEYWORDS_WEIGHTED` 来自定义关注的主题和权重。

## 技术栈

- **后端**: Python + Flask
- **数据库**: SQLite
- **论文源**: arXiv API
- **定时任务**: APScheduler
- **前端**: HTML + CSS + Jinja2

## 提示

- 首次启动时会自动抓取当天的论文
- 可以点击"立即抓取"按钮手动更新
- 论文数据保存在本地 `papers.db` 文件中
