# LearnThai 泰语学习平台

一个专为中文用户设计的泰语学习 Web 应用，基于 Flask 框架构建。

## 功能特性

### 词汇学习
- **闪卡模式** - 快速浏览泰语词汇与中文释义
- **选择题模式** - 四选一测试词汇掌握程度
- **是非题模式** - 判断词汇与释义是否匹配
- **间隔重复算法 (SRS)** - 科学安排复习时间，优化记忆效果

### 泰语字母
- **辅音学习** - 44 个泰语辅音，按高/中/低音类分组
- **元音学习** - 泰语元音系统
- **字母练习** - 闪卡和选择题模式

### 情景对话
- **多种生活场景** - 餐厅点餐、购物、问路等实用对话
- **分句学习** - 逐句展示泰语、中文翻译和发音
- **角色对话** - 模拟真实对话场景

### 用户系统
- 注册/登录
- 学习进度追踪
- 个人学习统计

### 管理后台
- 用户管理
- 词汇管理（增删改查、批量导入）
- 字母管理
- 对话场景管理
- 学习数据统计仪表板

## 技术栈

- **后端**: Flask 3.0, Flask-SQLAlchemy, Flask-Login
- **数据库**: SQLite
- **前端**: Jinja2 模板, 原生 CSS
- **测试**: pytest

## 快速开始

### 1. 克隆项目
```bash
git clone <repository-url>
cd LearnThai
```

### 2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 初始化数据库
```bash
python init_db.py
```

### 5. 导入初始数据（可选）
```bash
python import_vocab.py        # 导入词汇
python import_alphabet.py     # 导入泰语字母
python import_conversations.py # 导入对话数据
```

### 6. 创建管理员账户
```bash
python create_admin.py
```

### 7. 启动应用
```bash
python run.py
```

访问 http://127.0.0.1:5000 即可使用。

## 项目结构

```
LearnThai/
├── app/
│   ├── __init__.py          # Flask 应用工厂
│   ├── models.py            # 数据模型
│   ├── routes/              # 路由蓝图
│   │   ├── auth.py          # 认证相关
│   │   ├── learning.py      # 词汇学习
│   │   ├── alphabet.py      # 字母学习
│   │   ├── conversation.py  # 对话学习
│   │   └── admin.py         # 管理后台
│   ├── templates/           # Jinja2 模板
│   ├── static/              # 静态资源
│   └── utils/               # 工具函数
│       ├── srs.py           # 间隔重复算法
│       └── decorators.py    # 装饰器
├── tests/                   # 测试文件
├── data/                    # 数据文件
├── docs/                    # 文档
├── config.py                # 配置文件
├── run.py                   # 启动脚本
└── requirements.txt         # 依赖列表
```

## 运行测试

```bash
pytest
```

## 数据模型

- **User** - 用户
- **Vocabulary** - 词汇
- **UserVocabulary** - 用户词汇学习进度
- **ThaiAlphabet** - 泰语字母
- **UserAlphabet** - 用户字母学习进度
- **ConversationScene** - 对话场景
- **Conversation** - 对话
- **ConversationLine** - 对话句子
- **UserConversation** - 用户对话学习进度
- **QuizAttempt** - 答题记录

## License

MIT
