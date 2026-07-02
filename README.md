# AI Paper Assistant 🔬

一个功能丰富的 AI 论文学习与开源项目追踪助手。自动从 arXiv 抓取 AI 领域最新论文，支持 AI 驱动的论文翻译、深度总结、学习记录，并追踪 OpenAI / Google / Anthropic 的最新开源成果。

## ✨ 功能特性

### 📄 论文发现与管理
- **智能抓取**：自动从 arXiv 抓取 AI Agent、LLM、多智能体等领域的最新论文
- **相关度评分**：基于 25 个加权关键词对论文进行智能排序，精准推荐
- **自定义搜索**：支持自定义关键词搜索，灵活探索感兴趣的方向
- **每日更新**：每天早上 8 点自动抓取，也可手动触发
- **阅读管理**：标记已读/未读、收藏感兴趣的论文
- **按日期浏览**：每次抓取按日期记录，支持日期切换查看历史

### 📖 AI 论文学习
- **一键学习**：论文详情页点击「开始学习」进入沉浸式学习界面
- **英中双栏翻译**：自动提取 PDF 全文，左栏英文原文、右栏中文翻译，逐段对照
- **AI 深度总结**：从研究背景、核心方法、创新点、实验结果、消融分析、局限性等 7 个维度生成 1500-2000 字深度分析
- **学习缓存**：翻译和总结结果自动缓存，重复访问秒加载
- **智能推荐**：基于学习历史，AI 自动推荐新的搜索关键词，填充到抓取弹窗

### 🔬 开源项目追踪
- **三大公司追踪**：自动从 GitHub 抓取 OpenAI、Google（DeepMind/Research）、Anthropic 的最新开源项目
- **智能过滤**：基于 AI 相关关键词自动筛选，排除非 AI 项目
- **公司分类**：按 OpenAI / Google / Anthropic 分类查看
- **按日期记录**：每次抓取按日期存储，支持历史对比
- **阅读记忆**：标记已读/收藏，已读项目自动降低透明度

### 🎨 界面设计
- **Apple 风格 UI**：glassmorphism 磨砂玻璃效果、流畅动画、圆角卡片
- **暗色模式**：完整的 Light / Dark 主题切换，自动记忆偏好
- **动态背景**：四色渐变光球漂浮动画
- **3D 卡片**：鼠标悬停时的 3D 倾斜效果
- **响应式**：适配桌面和移动端
- **GitHub 同步**：一键将项目推送到 GitHub 仓库

## 🚀 快速开始

### 环境要求
- Python 3.8+
- macOS / Linux / Windows

### 安装

```bash
git clone https://github.com/fbwnbnb-oss/ai-paper-assistant.git
cd ai-paper-assistant
pip3 install -r requirements.txt
```

### 启动

```bash
python3 app.py
```

浏览器打开 **http://localhost:5000** 即可使用。

首次启动会自动抓取当天的论文。

## 📁 项目结构

```
ai-paper-assistant/
├── app.py                  # Flask 主应用，路由定义
├── fetcher.py              # arXiv 论文抓取与相关度评分
├── models.py               # SQLite 数据库模型与 CRUD
├── ai_service.py           # AI 服务（翻译、总结、关键词推荐）
├── pdf_extractor.py        # PDF 文本提取
├── opensource_fetcher.py   # GitHub 开源项目抓取
├── github_sync.py          # GitHub 仓库同步
├── requirements.txt        # Python 依赖
├── papers.db               # SQLite 数据库（自动生成）
├── templates/
│   ├── base.html           # 基础模板（导航栏、弹窗、主题切换）
│   ├── index.html          # 首页（论文列表）
│   ├── paper.html          # 论文详情页
│   ├── study.html          # 学习页面（双栏翻译 + 总结）
│   └── opensource.html     # 开源追踪页面
└── static/
    └── style.css           # 全局样式（Light/Dark 主题、动画）
```

## 🔧 技术栈

| 组件 | 技术 |
|------|------|
| 后端 | Python 3 + Flask |
| 数据库 | SQLite |
| 论文源 | arXiv API |
| AI 模型 | Qwen3 Max (DashScope API) |
| PDF 解析 | pdfplumber |
| 开源追踪 | GitHub REST API |
| 定时任务 | APScheduler |
| 前端 | HTML + CSS + JavaScript + Jinja2 |

## 📊 数据库设计

| 表名 | 用途 |
|------|------|
| `papers` | 论文信息（标题、作者、摘要、PDF链接、相关度评分） |
| `paper_status` | 论文阅读状态（已读、收藏） |
| `study_records` | 学习记录（原文、翻译、总结） |
| `opensource_projects` | 开源项目信息（名称、公司、stars、topics） |
| `opensource_status` | 开源项目阅读状态（已读、收藏） |

## ⚙️ 配置说明

### AI 模型配置
在 `ai_service.py` 中配置 DashScope API：
- `API_KEY`：你的 DashScope API Key
- `MODEL`：模型名称（默认 `qwen3-235b-a22b`）
- `BASE_URL`：API 端点

### 论文关键词配置
在 `fetcher.py` 中修改 `KEYWORDS_WEIGHTED` 字典来自定义关注的主题和权重：
- 权重 15-20：最感兴趣的核心主题
- 权重 7-12：相关但次要的主题
- 权重 3-5：泛 AI 领域关键词

### GitHub 同步配置
通过网页界面配置 GitHub Token 和仓库信息，支持一键同步。

## 🖥️ 页面预览

- **首页** `/` — 按日期浏览论文推荐，卡片式布局
- **论文详情** `/paper/<id>` — 完整摘要、分类标签、操作按钮
- **学习页面** `/study/<id>` — 英中双栏翻译 + AI 深度总结
- **开源追踪** `/opensource` — 三大公司最新开源项目，按日期/公司筛选

## 📝 使用技巧

1. **首次使用**：启动后自动抓取论文，点击「开源追踪」→「抓取最新」获取开源项目
2. **自定义搜索**：点击「抓取论文」输入关键词，或使用快速标签
3. **学习论文**：进入论文详情 → 点击紫色「开始学习」按钮，等待翻译完成
4. **AI 推荐**：学习几篇论文后，抓取弹窗会自动出现 AI 推荐关键词
5. **暗色模式**：点击导航栏月亮图标切换

## License

MIT
