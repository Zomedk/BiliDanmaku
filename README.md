# 🎯 B站弹幕分析可视化系统

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0.3-green.svg)
![Vue.js](https://img.shields.io/badge/Vue.js-2.6.14-brightgreen.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

**一个简单基础的的B站视频弹幕分析工具，提供弹幕数据抓取、词频统计、情感分析、可视化图表等功能**

[🚀 快速开始](#快速开始) • [📊 功能特性](#功能特性) • [🔧 安装部署](#安装部署) • [📖 使用指南](#使用指南)

</div>

---

## 📋 项目简介

B站弹幕分析可视化系统是一个基于Python Flask后端和Vue.js前端的Web应用，专门用于分析B站视频的弹幕数据。通过输入B站视频的BV号或链接，系统可以抓取弹幕数据并进行深度分析，包括词频统计、情感分析、用户活跃度分析等，并生成直观的可视化图表。

## ✨ 功能特性

### 🎬 视频信息获取
- 自动获取视频标题、UP主信息、封面图片
- 支持BV号和视频链接两种输入方式
- 实时显示视频时长和基本信息

### 💬 弹幕数据分析
- **弹幕抓取**: 批量获取视频所有弹幕数据
- **关键词搜索**: 支持按关键词筛选弹幕
- **分页显示**: 支持大量弹幕数据的分页浏览
- **排序功能**: 按时间、发送时间等多种方式排序
- **用户弹幕查询**: 根据用户哈希值查询特定用户的弹幕

### 📊 数据可视化
- **词频统计**: 统计弹幕中最常出现的词语
- **词云图生成**: 生成美观的词云可视化图表
- **时间分布图**: 展示弹幕在视频时间轴上的分布
- **活跃用户排行**: 统计发送弹幕最多的用户

### 🧠 智能分析
- **情感分析**: 使用机器学习分析弹幕情感倾向
- **弹幕长度分布**: 统计不同长度弹幕的分布情况
- **弹幕颜色分析**: 分析用户使用的弹幕颜色偏好
- **数据摘要**: 提供弹幕数据的整体统计信息

### 🔐 用户系统
- 用户注册和登录功能
- 个人弹幕历史记录
- 用户权限管理

## 🛠️ 技术栈

### 后端技术
- **Python 3.8+**: 主要开发语言
- **Flask 3.0.3**: Web框架
- **Flask-CORS**: 跨域请求处理
- **requests**: HTTP请求库
- **jieba**: 中文分词
- **snownlp**: 中文情感分析
- **matplotlib**: 数据可视化
- **wordcloud**: 词云生成
- **pandas**: 数据处理
- **scikit-learn**: 机器学习

### 前端技术
- **Vue.js 2.6.14**: 前端框架
- **Axios**: HTTP客户端
- **CSS3**: 样式设计
- **HTML5**: 页面结构

## 🚀 快速开始

### 环境要求
- Python 3.8 或更高版本
- Windows 10/11 (推荐)
- 现代浏览器 (Chrome, Firefox, Edge)

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd danmaku_test
```

2. **安装Python依赖**
```bash
cd danmaku_test/backend
pip install -r requirement.txt
```

3. **启动后端服务**
```bash
python app.py
C:\Users\zzw\AppData\Local\Programs\Python\Python38\python.exe D:\Lernen\danmaku_test\danmaku_test\backend\app.py
```

4. **访问前端页面**
打开浏览器访问: `http://127.0.0.1:5000`

## 📖 使用指南

### 基本使用流程

1. **输入视频信息**
   - 在输入框中输入B站视频的BV号或完整链接
   - 点击"查询"按钮获取视频基本信息

2. **查看视频信息**
   - 系统会显示视频标题、UP主、封面等信息
   - 确认信息无误后继续下一步

3. **获取弹幕数据**
   - 切换到"弹幕列表"选项卡
   - 点击"查询弹幕"按钮开始抓取弹幕

4. **数据分析**
   - **词频统计**: 查看弹幕中最常出现的词语
   - **高级分析**: 生成词云图、时间分布图等可视化图表
   - **情感分析**: 分析弹幕的情感倾向
   - **用户分析**: 查看活跃用户排行榜

### 高级功能

#### 关键词搜索
- 在弹幕列表页面输入关键词
- 系统会筛选出包含该关键词的弹幕
- 支持模糊匹配和大小写不敏感搜索

#### 用户弹幕查询
- 输入用户哈希值
- 查看该用户在该视频中的所有弹幕
- 支持点击用户哈希查看用户UID

#### 数据导出
- 支持将分析结果导出为Excel格式
- 包含词频统计、用户活跃度等数据

## 📁 项目结构

```
danmaku_test/
├── backend/                 # 后端代码
│   ├── app.py              # Flask主应用
│   ├── config.py           # 配置文件
│   ├── requirement.txt     # Python依赖
│   ├── modules/            # 功能模块
│   │   ├── auth.py         # 用户认证
│   │   ├── danmaku.py      # 弹幕处理
│   │   ├── video_info.py   # 视频信息
│   │   ├── sentiment_analysis.py  # 情感分析
│   │   └── ...
│   ├── static/             # 静态资源
│   └── assets/             # 资源文件
├── frontend/               # 前端代码
│   ├── index.html          # 主页面
│   ├── login.html          # 登录页面
│   ├── css/                # 样式文件
│   └── js/                 # JavaScript文件
└── README.md               # 项目说明
```

## 🔧 配置说明

### 环境变量
创建 `.env` 文件并配置以下变量：
```env
# 数据库配置
DATABASE_URL=sqlite:///users.db

# 日志级别
LOG_LEVEL=INFO

# 跨域设置
CORS_ORIGINS=http://127.0.0.1:5000,http://localhost:5000
```

### 字体配置
确保系统安装了中文字体：
- Windows: `C:\Users\[用户名]\AppData\Local\Microsoft\Windows\Fonts\NotoSansSC-Regular.otf`
- Linux: `/usr/share/fonts/truetype/noto/NotoSansSC-Regular.otf`

## 🐛 常见问题

### Q: 无法获取弹幕数据？
A: 请检查：
- 网络连接是否正常
- BV号是否正确
- 视频是否公开可见
- 是否触发了B站的访问限制

### Q: 词云图显示异常？
A: 确保：
- 系统已安装中文字体
- Python环境中安装了wordcloud库
- 有足够的弹幕数据用于生成词云

### Q: 情感分析不准确？
A: 这是正常现象，因为：
- 弹幕语言通常比较随意
- 中文情感分析模型较为基础，仍在优化中
- 网络用语和表情符号可能影响分析结果

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进这个项目！

### 开发环境设置
1. Fork项目到你的GitHub账户
2. 克隆你的Fork到本地
3. 创建新的功能分支
4. 提交你的更改
5. 推送到你的Fork
6. 创建Pull Request

### 代码规范
- 使用Python PEP 8代码规范
- 添加适当的注释和文档字符串
- 确保代码通过所有测试

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [B站](https://www.bilibili.com/) - 提供视频和弹幕数据
- [Flask](https://flask.palletsprojects.com/) - Web框架
- [Vue.js](https://vuejs.org/) - 前端框架
- [jieba](https://github.com/fxsjy/jieba) - 中文分词
- [wordcloud](https://github.com/amueller/word_cloud) - 词云生成

## 📞 联系方式

- 项目主页: [暂无]
- 问题反馈: [暂无]
- 邮箱: [暂无]

---

<div align="center">

**如果这个项目对你有帮助，请给它一个 ⭐ Star！**

Made with ❤️ by [Your Name]

</div>
