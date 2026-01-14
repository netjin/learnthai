# 泰语学习 Web 应用设计文档

## 项目概述

**项目名称**: LearnThai - 中文用户泰语词汇学习平台
**类型**: 交互式词汇训练 Web 应用
**目标**: 为中文用户提供科学高效的泰语词汇学习工具
**开发阶段**: 工作原型（本地开发优先）

## 一、整体架构

### 技术栈

- **后端框架**: Flask
- **数据库 ORM**: Flask-SQLAlchemy
- **用户认证**: Flask-Login
- **表单处理**: Flask-WTF
- **数据库**: SQLite (开发), PostgreSQL (生产备选)
- **模板引擎**: Jinja2
- **前端**: 原生 JavaScript + CSS (渐进式增强)
- **音频处理**: HTML5 Audio API

### 项目结构

```
LearnThai/
├── app/
│   ├── __init__.py              # Flask 应用初始化
│   ├── models.py                # 数据库模型
│   ├── routes/                  # 路由蓝图
│   │   ├── __init__.py
│   │   ├── auth.py              # 认证路由（注册、登录、登出）
│   │   ├── vocab.py             # 词汇学习路由（学习、答题）
│   │   ├── stats.py             # 统计页面路由
│   │   └── admin.py             # 管理员后台路由
│   ├── templates/               # Jinja2 模板
│   │   ├── base.html
│   │   ├── auth/
│   │   ├── learning/
│   │   ├── stats/
│   │   ├── admin/
│   │   └── errors/
│   ├── static/                  # 静态资源
│   │   ├── css/
│   │   ├── js/
│   │   └── audio/               # 泰语发音音频文件
│   └── utils/                   # 工具函数
│       ├── srs.py               # SRS 算法实现
│       └── validators.py        # 答案验证逻辑
├── data/                        # 词汇数据文件
│   └── basic_vocab.csv          # 初始词汇数据
├── tests/                       # 测试文件
├── migrations/                  # 数据库迁移文件
├── config.py                    # 配置文件
├── init_db.py                   # 数据库初始化脚本
├── import_vocab.py              # 词汇导入脚本
├── create_admin.py              # 创建管理员脚本
└── run.py                       # 应用入口
```

### 架构理念

采用 Flask 单体架构，所有功能集成在一个应用中：
- 使用蓝图（Blueprint）分离功能模块
- 服务端渲染 HTML，JavaScript 渐进增强交互
- 简化开发流程，快速迭代原型
- 易于维护和调试

## 二、数据库设计

### 核心数据模型

#### 1. User (用户表)

```python
class User:
    id: Integer (主键)
    username: String(80) (唯一, 非空)
    email: String(120) (唯一, 非空)
    password_hash: String(128) (非空)
    is_admin: Boolean (默认 False)
    created_at: DateTime (默认当前时间)
    last_login: DateTime
```

**关系**:
- 一对多 → UserVocabulary (学习进度)
- 一对多 → QuizAttempt (答题记录)

#### 2. Vocabulary (词汇表)

```python
class Vocabulary:
    id: Integer (主键)
    thai_word: String(100) (非空)
    chinese_meaning: String(200) (非空)
    pronunciation: String(100)  # 罗马音标注
    audio_file: String(200)      # 音频文件路径
    category: String(50)         # 分类
    difficulty_level: Integer    # 难度等级 1-5
    frequency_rank: Integer      # 词频排名（可选）
    example_sentence_thai: Text  # 泰语例句
    example_sentence_chinese: Text  # 中文例句
    created_at: DateTime
    is_active: Boolean (默认 True)  # 软删除标记
```

**索引**:
- category (分类查询)
- difficulty_level (难度筛选)
- frequency_rank (按词频排序)

#### 3. UserVocabulary (用户学习进度表)

```python
class UserVocabulary:
    id: Integer (主键)
    user_id: Integer (外键 → User, 非空)
    vocabulary_id: Integer (外键 → Vocabulary, 非空)
    familiarity_level: Integer  # 熟悉度 0-5
    next_review_date: DateTime  # SRS 下次复习时间
    review_count: Integer       # 总复习次数
    correct_count: Integer      # 答对次数
    last_reviewed: DateTime     # 最后复习时间
    created_at: DateTime        # 首次学习时间
```

**唯一约束**: (user_id, vocabulary_id) - 每个用户每个词汇只有一条记录

#### 4. QuizAttempt (答题记录表)

```python
class QuizAttempt:
    id: Integer (主键)
    user_id: Integer (外键 → User, 非空)
    vocabulary_id: Integer (外键 → Vocabulary, 非空)
    quiz_type: String(20)  # flashcard, multiple_choice, typing, listening
    is_correct: Boolean
    time_taken: Integer    # 答题用时（秒）
    created_at: DateTime
```

**索引**:
- (user_id, created_at) - 按日期查询用户答题记录
- (user_id, vocabulary_id) - 查询特定词汇答题历史

### 数据关系图

```
User (1) ────< (N) UserVocabulary (N) ────> (1) Vocabulary
  │                                               │
  │                                               │
  └────< (N) QuizAttempt (N) ──────────────────────┘
```

## 三、SRS 间隔重复算法

### 算法选择

采用简化版 **SM-2 算法**（SuperMemo 2），经过验证的记忆曲线算法。

### 熟悉度等级定义

| 等级 | 描述 | 用户感受 |
|------|------|----------|
| 0 | 完全不会 | 从未见过或完全不记得 |
| 1 | 勉强记得 | 看到答案才想起来 |
| 2 | 有印象但不确定 | 模糊记忆，不太确定 |
| 3 | 想起来了 | 需要思考但能答对 |
| 4 | 容易想起 | 快速想起正确答案 |
| 5 | 非常熟悉 | 瞬间反应，完全掌握 |

### 间隔计算逻辑

```python
def calculate_next_review(current_familiarity, review_count, last_interval_days):
    """
    计算下次复习时间

    Args:
        current_familiarity: 本次答题后的熟悉度 (0-5)
        review_count: 已复习次数
        last_interval_days: 上次间隔天数

    Returns:
        下次复习的间隔（分钟或天）
    """

    # 答错或不熟练（熟悉度 < 3）：重新学习
    if current_familiarity < 3:
        return 10  # 10分钟后重新复习

    # 答对的情况：根据复习次数递增间隔
    interval_map = {
        0: 10,      # 首次：10分钟
        1: 1440,    # 第1次：1天（1440分钟）
        2: 4320,    # 第2次：3天
        3: 10080,   # 第3次：7天
        4: 21600,   # 第4次：15天
        5: 43200,   # 第5次：30天
        6: 86400,   # 第6次：60天
    }

    if review_count >= 7:
        return 129600  # 第7次及以后：90天

    return interval_map.get(review_count, 10)
```

### 每日学习流程

1. **生成复习队列**:
   - 筛选 `next_review_date <= 当前时间` 的词汇
   - 排序优先级：过期时间长 > 熟悉度低 > 最后复习时间早

2. **学习新词**:
   - 如果复习队列 < 20 个，补充新词到 20 个
   - 新词优先级：高频词 > 低难度词 > 同分类词

3. **答题更新**:
   - 记录答题结果到 `QuizAttempt`
   - 更新 `UserVocabulary`:
     - `familiarity_level` 根据答题质量调整
     - `next_review_date` 根据 SRS 算法计算
     - `review_count` +1
     - `correct_count` (答对时 +1)

## 四、题型设计

### 1. 闪卡模式 (Flashcard)

**界面**:
```
┌─────────────────────────┐
│   [🔊 播放发音]         │
│                         │
│      สวัสดี            │
│   (sa-wat-dee)          │
│                         │
│  [显示答案]             │
└─────────────────────────┘
```

**流程**:
1. 显示泰语单词 + 罗马音
2. 用户点击"显示答案"查看中文
3. 用户自评熟悉度 (0-5)
4. 系统更新 SRS 数据

**特点**: 最快速的复习方式，依赖用户诚实自评。

### 2. 选择题模式 (Multiple Choice)

**界面**:
```
┌─────────────────────────┐
│   [🔊] ขอบคุณ           │
│                         │
│   A. 你好               │
│   B. 谢谢  ✓            │
│   C. 再见               │
│   D. 对不起             │
└─────────────────────────┘
```

**流程**:
1. 显示泰语单词 + 4 个中文选项
2. 用户点击选择
3. 立即反馈正确/错误
4. 显示正确答案和例句

**干扰项生成**:
- 从同分类词汇中随机抽取 3 个
- 避免语义过于接近的选项
- 难度可调：初级用户差异大的选项，高级用户相似选项

**评分逻辑**:
- 答对：熟悉度 = min(当前熟悉度 + 1, 5)
- 答错：熟悉度 = 1

### 3. 听力模式 (Listening)

**界面**:
```
┌─────────────────────────┐
│   [🔊 播放音频]         │
│   (可重复播放)          │
│                         │
│   ┌─────────────────┐   │
│   │ 输入中文意思... │   │
│   └─────────────────┘   │
│                         │
│   [提交答案]            │
└─────────────────────────┘
```

**流程**:
1. 自动播放泰语音频（或用户点击播放）
2. 用户输入中文意思
3. 模糊匹配答案（允许同义词、多余空格）

**答案验证**:
```python
def validate_listening_answer(user_input, correct_answer):
    # 去除空格和标点
    user_clean = re.sub(r'[^\w]', '', user_input)
    correct_clean = re.sub(r'[^\w]', '', correct_answer)

    # 完全匹配
    if user_clean == correct_clean:
        return True

    # 部分匹配（80% 相似度）
    similarity = difflib.SequenceMatcher(None, user_clean, correct_clean).ratio()
    return similarity >= 0.8
```

### 4. 拼写模式 (Typing)

**界面**:
```
┌─────────────────────────┐
│   中文: 你好            │
│                         │
│   请输入泰语:           │
│   ┌─────────────────┐   │
│   │ สวัสดี         │   │
│   └─────────────────┘   │
│                         │
│   [提交答案]            │
└─────────────────────────┘
```

**流程**:
1. 显示中文释义
2. 用户使用泰语键盘输入泰语单词
3. 精确匹配验证（必须完全正确）

**技术要点**:
- 支持泰语输入法（浏览器原生支持）
- 提供虚拟键盘选项（可选）
- 严格匹配，包括声调符号

**难度**: 最高，适合进阶学习者。

### 学习会话管理

**会话配置**:
```python
SESSION_CONFIG = {
    'default_size': 20,      # 默认每次学习 20 个词
    'review_priority': 0.7,  # 70% 复习，30% 新词
    'max_new_words': 10,     # 每次最多 10 个新词
}
```

**进度显示**:
- 顶部进度条：已完成 / 总数
- 实时统计：当前正确率
- 剩余词汇数量

**完成总结**:
```
恭喜完成今日学习！

📊 学习统计
- 总题数: 20
- 正确率: 85%
- 用时: 8 分 32 秒
- 新学词汇: 5 个
- 复习词汇: 15 个
- 掌握词汇: +3 个

[继续学习] [查看详情] [返回首页]
```

## 五、用户认证与权限

### 认证系统

#### 注册流程

**表单字段**:
- 用户名：3-20 字符，仅字母数字下划线
- 邮箱：有效邮箱格式
- 密码：至少 6 位（原型阶段）
- 确认密码：必须一致

**验证逻辑**:
```python
def validate_registration(username, email, password):
    # 用户名唯一性
    if User.query.filter_by(username=username).first():
        raise ValidationError('用户名已存在')

    # 邮箱唯一性
    if User.query.filter_by(email=email).first():
        raise ValidationError('邮箱已注册')

    # 密码强度（简化版）
    if len(password) < 6:
        raise ValidationError('密码至少 6 位')

    return True
```

**密码加密**:
```python
from werkzeug.security import generate_password_hash

user.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
```

#### 登录机制

**Flask-Login 配置**:
```python
from flask_login import LoginManager, login_user

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = '请先登录'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
```

**会话管理**:
- 默认会话：关闭浏览器后过期
- "记住我"：30 天有效期
- 自动登出：24 小时无活动

#### 权限角色

| 角色 | 权限 |
|------|------|
| **普通用户** | 学习词汇、查看个人统计、修改个人信息 |
| **管理员** | 所有普通用户权限 + 添加/编辑/删除词汇 + 查看全局统计 |

**权限装饰器**:
```python
from functools import wraps
from flask_login import current_user
from flask import abort

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function

# 使用
@app.route('/admin/vocab/add')
@admin_required
def add_vocabulary():
    ...
```

### 安全措施

**1. CSRF 保护**:
```python
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect(app)
```

所有 POST 表单自动包含 CSRF token。

**2. SQL 注入防护**:
使用 SQLAlchemy ORM 参数化查询：
```python
# 安全
User.query.filter_by(username=username).first()

# 不安全（避免）
db.session.execute(f"SELECT * FROM user WHERE username='{username}'")
```

**3. XSS 防护**:
Jinja2 自动转义：
```html
<!-- 自动转义用户输入 -->
<p>{{ user_input }}</p>

<!-- 需要原始 HTML 时（谨慎使用）-->
<p>{{ trusted_html | safe }}</p>
```

**4. 密码安全**:
- Werkzeug 加盐哈希存储
- 前端密码强度提示
- 可选：密码重置功能（邮件验证）

**5. 会话安全**:
```python
# config.py
SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
SESSION_COOKIE_SECURE = True   # 仅 HTTPS（生产环境）
SESSION_COOKIE_HTTPONLY = True # 防止 JS 访问
SESSION_COOKIE_SAMESITE = 'Lax' # CSRF 保护
```

## 六、统计与进度追踪

### 个人学习仪表板

#### 核心指标卡片

```
┌────────────────┬────────────────┬────────────────┐
│  学习天数      │  已学词汇      │  掌握词汇      │
│     15 天      │    156 个      │     89 个      │
│  🔥 连续 7 天  │                │   (57.1%)      │
└────────────────┴────────────────┴────────────────┘

┌────────────────┬────────────────┬────────────────┐
│  今日新学      │  今日复习      │  今日准确率    │
│     5 个       │    15 个       │     85%        │
└────────────────┴────────────────┴────────────────┘

┌─────────────────────────────────────────────────┐
│  ⏰ 待复习词汇: 23 个                           │
│     [开始复习]                                   │
└─────────────────────────────────────────────────┘
```

#### 统计查询实现

```python
def get_user_dashboard_stats(user_id):
    """获取用户仪表板统计数据"""

    # 学习天数统计
    first_attempt = QuizAttempt.query.filter_by(user_id=user_id)\
        .order_by(QuizAttempt.created_at.asc()).first()
    days_learning = (datetime.now() - first_attempt.created_at).days if first_attempt else 0

    # 连续学习天数
    streak = calculate_learning_streak(user_id)

    # 已学词汇总数
    total_learned = UserVocabulary.query.filter_by(user_id=user_id).count()

    # 已掌握词汇（熟悉度 >= 4）
    mastered = UserVocabulary.query.filter(
        UserVocabulary.user_id == user_id,
        UserVocabulary.familiarity_level >= 4
    ).count()

    # 今日统计
    today_start = datetime.now().replace(hour=0, minute=0, second=0)
    today_attempts = QuizAttempt.query.filter(
        QuizAttempt.user_id == user_id,
        QuizAttempt.created_at >= today_start
    ).all()

    today_new = len(set(a.vocabulary_id for a in today_attempts
                       if a.created_at == UserVocabulary.query.filter_by(
                           user_id=user_id,
                           vocabulary_id=a.vocabulary_id
                       ).first().created_at))

    today_reviewed = len(today_attempts) - today_new
    today_accuracy = sum(1 for a in today_attempts if a.is_correct) / len(today_attempts) * 100 if today_attempts else 0

    # 待复习词汇
    due_review = UserVocabulary.query.filter(
        UserVocabulary.user_id == user_id,
        UserVocabulary.next_review_date <= datetime.now()
    ).count()

    return {
        'days_learning': days_learning,
        'streak': streak,
        'total_learned': total_learned,
        'mastered': mastered,
        'mastered_percentage': round(mastered / total_learned * 100, 1) if total_learned else 0,
        'today_new': today_new,
        'today_reviewed': today_reviewed,
        'today_accuracy': round(today_accuracy, 1),
        'due_review': due_review,
    }

def calculate_learning_streak(user_id):
    """计算连续学习天数"""
    # 获取所有学习日期（去重）
    attempts = QuizAttempt.query.filter_by(user_id=user_id)\
        .order_by(QuizAttempt.created_at.desc()).all()

    learning_dates = sorted(set(a.created_at.date() for a in attempts), reverse=True)

    if not learning_dates or learning_dates[0] != datetime.now().date():
        return 0

    streak = 1
    for i in range(len(learning_dates) - 1):
        if (learning_dates[i] - learning_dates[i+1]).days == 1:
            streak += 1
        else:
            break

    return streak
```

### 可视化图表

#### 1. 学习日历热力图

类似 GitHub Contributions:
```
2026年1月
周一  ■ □ ■ ■
周二  ■ ■ □ ■
周三  □ ■ ■ ■
...
```

**实现**:
- 前端：纯 CSS 网格 + JavaScript
- 数据：每日答题数量
- 颜色：0=灰色, 1-10=浅绿, 11-30=绿色, 31+=深绿

#### 2. 学习曲线图

```
词汇数
  ^
60|           ●
  |         ●
40|       ●
  |     ●
20|   ●
  | ●
  +-------------------> 日期
   1/8 1/9 ... 1/14
```

**数据点**: 每日累计学习词汇数
**前端库**: Chart.js 或纯 SVG

#### 3. 熟悉度分布饼图

```
  5级 (精通) ─── 20%
  4级 (熟悉) ─── 35%
  3级 (掌握) ─── 25%
  2级 (认识) ─── 15%
  1级 (薄弱) ─── 5%
```

#### 4. 分类掌握进度

```
日常用语  ████████████░░░░░░  60% (30/50)
食物饮料  ███████░░░░░░░░░░░  35% (14/40)
交通出行  ██████████████████  90% (27/30)
```

### 词汇列表视图

#### 我的词库

**筛选选项**:
- 全部 / 学习中 / 已掌握 / 薄弱
- 按分类
- 按熟悉度等级
- 按添加时间

**列表显示**:
```
┌─────────────────────────────────────────┐
│ สวัสดี  你好                 ★★★★★    │
│ sa-wat-dee                  [🔊] [详情] │
├─────────────────────────────────────────┤
│ ขอบคุณ  谢谢                 ★★★★☆    │
│ khop-khun                   [🔊] [详情] │
└─────────────────────────────────────────┘
```

**详情页面**:
- 完整释义和例句
- 学习历史：首次学习时间、复习次数、正确率
- 答题记录时间线
- 快速练习按钮

#### 薄弱环节

筛选条件：
```python
weak_words = UserVocabulary.query.filter(
    UserVocabulary.user_id == user_id,
    UserVocabulary.familiarity_level <= 2
).order_by(UserVocabulary.familiarity_level.asc()).all()
```

**推荐操作**: "加强练习"按钮 → 进入专门针对这些词的学习会话

#### 即将遗忘

筛选条件：
```python
overdue_words = UserVocabulary.query.filter(
    UserVocabulary.user_id == user_id,
    UserVocabulary.next_review_date < datetime.now()
).order_by(UserVocabulary.next_review_date.asc()).all()
```

**显示**: 距离建议复习时间已过去的天数
**操作**: "立即复习"按钮

#### 已掌握归档

筛选条件：
```python
mastered_words = UserVocabulary.query.filter(
    UserVocabulary.user_id == user_id,
    UserVocabulary.familiarity_level == 5,
    UserVocabulary.review_count >= 5
).all()
```

**功能**:
- 展示学习成果
- 可手动移除归档（重新加入学习）
- 定期抽查测试（防止遗忘）

## 七、词汇内容管理

### 数据文件格式

#### CSV 格式示例

```csv
thai_word,chinese_meaning,pronunciation,category,difficulty_level,audio_file,example_thai,example_chinese
สวัสดี,你好,sa-wat-dee,日常用语,1,audio/greetings/sawatdee.mp3,สวัสดีครับ,你好（男性用语）
สวัสดีค่ะ,你好（女性），sa-wat-dee-kha,日常用语,1,audio/greetings/sawatdeekha.mp3,สวัสดีค่ะ,你好（女性用语）
ขอบคุณ,谢谢,khop-khun,日常用语,1,audio/greetings/khopkhun.mp3,ขอบคุณมาก,非常感谢
ครับ,是的（男性），khrap,日常用语,1,audio/common/khrap.mp3,ครับผม,是的（正式）
ค่ะ,是的（女性），kha,日常用语,1,audio/common/kha.mp3,ค่ะ,好的
```

#### JSON 格式示例

```json
{
  "vocabularies": [
    {
      "thai_word": "สวัสดี",
      "chinese_meaning": "你好",
      "pronunciation": "sa-wat-dee",
      "category": "日常用语",
      "difficulty_level": 1,
      "audio_file": "audio/greetings/sawatdee.mp3",
      "example_sentence_thai": "สวัสดีครับ",
      "example_sentence_chinese": "你好（男性用语）"
    }
  ]
}
```

### 词汇导入脚本

```python
# import_vocab.py
import csv
from app import create_app, db
from app.models import Vocabulary

def import_from_csv(csv_file_path):
    """从 CSV 文件导入词汇"""
    app = create_app()
    with app.app_context():
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                # 检查是否已存在
                existing = Vocabulary.query.filter_by(
                    thai_word=row['thai_word']
                ).first()

                if existing:
                    print(f"跳过重复词汇: {row['thai_word']}")
                    continue

                vocab = Vocabulary(
                    thai_word=row['thai_word'],
                    chinese_meaning=row['chinese_meaning'],
                    pronunciation=row['pronunciation'],
                    category=row['category'],
                    difficulty_level=int(row['difficulty_level']),
                    audio_file=row['audio_file'],
                    example_sentence_thai=row.get('example_thai', ''),
                    example_sentence_chinese=row.get('example_chinese', '')
                )
                db.session.add(vocab)
                count += 1

            db.session.commit()
            print(f"成功导入 {count} 个词汇")

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("用法: python import_vocab.py <csv文件路径>")
        sys.exit(1)

    import_from_csv(sys.argv[1])
```

### 管理员后台功能

#### 词汇管理界面

**列表页面**:
- 分页显示所有词汇（每页 50 条）
- 搜索：按泰语/中文/分类搜索
- 批量操作：批量删除、批量修改分类
- 排序：按 ID、分类、难度、创建时间

**添加/编辑表单**:
```html
<form method="POST">
  泰语单词*: <input name="thai_word" required>
  中文释义*: <input name="chinese_meaning" required>
  罗马音标: <input name="pronunciation">
  分类: <select name="category">
    <option>日常用语</option>
    <option>食物饮料</option>
    ...
  </select>
  难度等级: <select name="difficulty_level">
    <option value="1">1 - 入门</option>
    ...
  </select>
  音频文件: <input type="file" accept=".mp3">
  泰语例句: <textarea name="example_thai"></textarea>
  中文例句: <textarea name="example_chinese"></textarea>

  <button>保存</button>
</form>
```

#### 音频文件管理

**上传处理**:
```python
from werkzeug.utils import secure_filename
import os

ALLOWED_EXTENSIONS = {'mp3', 'wav'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/admin/vocab/upload_audio', methods=['POST'])
@admin_required
def upload_audio():
    if 'audio' not in request.files:
        return jsonify({'error': '未选择文件'}), 400

    file = request.files['audio']
    if file.filename == '':
        return jsonify({'error': '文件名为空'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        category = request.form.get('category', 'misc')

        # 保存路径: static/audio/{category}/{filename}
        upload_folder = os.path.join(app.config['UPLOAD_FOLDER'], category)
        os.makedirs(upload_folder, exist_ok=True)

        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)

        # 返回相对路径用于数据库存储
        relative_path = f'audio/{category}/{filename}'
        return jsonify({'audio_file': relative_path}), 200

    return jsonify({'error': '不支持的文件格式'}), 400
```

**存储结构**:
```
app/static/audio/
├── greetings/
│   ├── sawatdee.mp3
│   └── khopkhun.mp3
├── food/
│   ├── khao.mp3
│   └── nam.mp3
└── ...
```

### 初始词汇分类体系

| 分类 | 预计词汇数 | 难度范围 | 优先级 |
|------|-----------|---------|--------|
| 日常用语 | 50 | 1-2 | 高 |
| 数字与时间 | 30 | 1-2 | 高 |
| 食物与餐饮 | 80 | 1-3 | 中 |
| 交通与出行 | 60 | 2-3 | 中 |
| 购物与消费 | 50 | 2-3 | 中 |
| 家庭与关系 | 40 | 2-3 | 低 |
| 工作与学习 | 70 | 3-4 | 低 |
| 旅游常用语 | 100 | 1-3 | 高 |

**初期目标**: 至少 500 个核心词汇覆盖日常场景。

### 词频列表集成

**数据来源**:
- 公开泰语词频数据库（如 Leeds Corpus）
- 手动标注常用词

**导入示例**:
```python
def import_frequency_list(json_file):
    """导入词频列表，自动设置难度"""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for rank, item in enumerate(data['words'], 1):
        # 根据词频排名自动分配难度
        if rank <= 100:
            difficulty = 1
        elif rank <= 500:
            difficulty = 2
        elif rank <= 1000:
            difficulty = 3
        else:
            difficulty = 4

        vocab = Vocabulary(
            thai_word=item['word'],
            chinese_meaning=item['meaning'],
            frequency_rank=rank,
            difficulty_level=difficulty,
            category='高频词汇'
        )
        db.session.add(vocab)

    db.session.commit()
```

## 八、错误处理与用户体验

### 错误处理策略

#### 1. HTTP 错误页面

**404 Not Found**:
```html
<!-- templates/errors/404.html -->
<h1>页面未找到</h1>
<p>抱歉，您访问的页面不存在。</p>
<a href="/">返回首页</a>
```

**500 Internal Server Error**:
```html
<!-- templates/errors/500.html -->
<h1>服务器错误</h1>
<p>抱歉，服务器遇到问题。我们已记录此错误并会尽快修复。</p>
<a href="/">返回首页</a>
```

**403 Forbidden**:
```html
<!-- templates/errors/403.html -->
<h1>访问被拒绝</h1>
<p>您没有权限访问此页面。</p>
<a href="/">返回首页</a>
```

#### 2. 表单验证错误

**后端验证**:
```python
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Email, Length

class RegistrationForm(FlaskForm):
    username = StringField('用户名',
        validators=[
            DataRequired(message='用户名不能为空'),
            Length(min=3, max=20, message='用户名长度为 3-20 字符')
        ])
    email = StringField('邮箱',
        validators=[
            DataRequired(message='邮箱不能为空'),
            Email(message='邮箱格式不正确')
        ])
    password = PasswordField('密码',
        validators=[
            DataRequired(message='密码不能为空'),
            Length(min=6, message='密码至少 6 位')
        ])
```

**前端实时验证**:
```javascript
// 密码强度提示
document.getElementById('password').addEventListener('input', function(e) {
    const password = e.target.value;
    const strengthBar = document.getElementById('password-strength');

    let strength = 0;
    if (password.length >= 6) strength++;
    if (password.length >= 10) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;

    strengthBar.className = ['weak', 'medium', 'strong', 'very-strong'][strength];
    strengthBar.textContent = ['弱', '中', '强', '很强'][strength];
});
```

#### 3. 数据库错误

```python
from sqlalchemy.exc import IntegrityError, OperationalError

@app.errorhandler(IntegrityError)
def handle_db_integrity_error(e):
    db.session.rollback()
    flash('数据保存失败：违反唯一性约束', 'error')
    return redirect(request.referrer or url_for('index'))

@app.errorhandler(OperationalError)
def handle_db_operational_error(e):
    db.session.rollback()
    flash('数据库连接错误，请稍后重试', 'error')
    return redirect(url_for('index'))
```

#### 4. 文件上传错误

```python
@app.errorhandler(413)  # Request Entity Too Large
def request_entity_too_large(e):
    flash('文件太大，最大支持 5MB', 'error')
    return redirect(request.referrer)

# 配置最大上传大小
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB
```

### Flash 消息系统

```python
# 四种消息类型
flash('注册成功！', 'success')   # 绿色
flash('用户名已存在', 'error')   # 红色
flash('密码过于简单', 'warning') # 黄色
flash('建议开启邮箱验证', 'info') # 蓝色
```

**模板显示**:
```html
<!-- base.html -->
{% with messages = get_flashed_messages(with_categories=true) %}
  {% if messages %}
    <div class="flash-messages">
      {% for category, message in messages %}
        <div class="alert alert-{{ category }}">
          {{ message }}
          <button class="close">&times;</button>
        </div>
      {% endfor %}
    </div>
  {% endif %}
{% endwith %}
```

**自动消失 JS**:
```javascript
document.querySelectorAll('.alert').forEach(alert => {
    setTimeout(() => {
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 300);
    }, 3000);  // 3 秒后消失
});
```

### 用户体验优化

#### 1. 性能优化

**音频预加载**:
```javascript
// 预加载下一题的音频
function preloadNextAudio(audioUrl) {
    const audio = new Audio(audioUrl);
    audio.preload = 'auto';
}

// 在当前题显示时预加载下一题
showQuestion(currentQuestion);
if (questions[currentIndex + 1]) {
    preloadNextAudio(questions[currentIndex + 1].audio_file);
}
```

**数据库查询优化**:
```python
# 使用 join 减少查询次数
user_progress = db.session.query(UserVocabulary, Vocabulary)\
    .join(Vocabulary)\
    .filter(UserVocabulary.user_id == user_id)\
    .all()

# 使用索引
class UserVocabulary(db.Model):
    __table_args__ = (
        db.Index('idx_user_next_review', 'user_id', 'next_review_date'),
    )
```

**分页加载**:
```python
from flask import request

@app.route('/my-vocab')
@login_required
def my_vocab():
    page = request.args.get('page', 1, type=int)
    per_page = 20

    pagination = UserVocabulary.query.filter_by(user_id=current_user.id)\
        .paginate(page=page, per_page=per_page, error_out=False)

    return render_template('vocab/my_vocab.html',
                          vocabularies=pagination.items,
                          pagination=pagination)
```

#### 2. 响应式设计

**移动端适配**:
```css
/* 基础样式 */
.quiz-container {
    max-width: 600px;
    margin: 0 auto;
    padding: 20px;
}

/* 移动端 */
@media (max-width: 768px) {
    .quiz-container {
        padding: 10px;
    }

    .thai-word {
        font-size: 36px;  /* 移动端字体更大 */
    }

    .options {
        flex-direction: column;  /* 选项垂直排列 */
    }
}
```

**触摸优化**:
```css
/* 增大按钮点击区域 */
.btn {
    min-height: 44px;  /* iOS 推荐最小点击区域 */
    padding: 12px 24px;
}

/* 禁用长按选择（避免误操作）*/
.quiz-word {
    user-select: none;
    -webkit-user-select: none;
}
```

#### 3. 键盘快捷键

```javascript
document.addEventListener('keydown', function(e) {
    // 空格键：播放音频
    if (e.code === 'Space' && !e.target.matches('input, textarea')) {
        e.preventDefault();
        playAudio();
    }

    // 回车键：提交答案/下一题
    if (e.code === 'Enter') {
        if (answerVisible) {
            nextQuestion();
        } else {
            submitAnswer();
        }
    }

    // 数字键 1-4：选择选项（选择题模式）
    if (quizType === 'multiple_choice' && e.key >= '1' && e.key <= '4') {
        selectOption(parseInt(e.key) - 1);
    }
});
```

#### 4. 学习反馈

**答对动画**:
```css
@keyframes correctAnswer {
    0% { transform: scale(1); }
    50% { transform: scale(1.1); background-color: #4CAF50; }
    100% { transform: scale(1); background-color: #E8F5E9; }
}

.answer-correct {
    animation: correctAnswer 0.5s ease;
}
```

**鼓励文字随机化**:
```javascript
const encouragements = [
    '太棒了！',
    '答对了！',
    '很好！',
    '继续加油！',
    '掌握得不错！'
];

function showCorrectFeedback() {
    const message = encouragements[Math.floor(Math.random() * encouragements.length)];
    showMessage(message, 'success');
}
```

#### 5. 进度自动保存

```javascript
// 每题答完自动保存进度
function autoSave(questionId, isCorrect) {
    const data = {
        vocabulary_id: questionId,
        is_correct: isCorrect,
        time_taken: calculateTimeSpent()
    };

    fetch('/api/save-progress', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        console.log('进度已保存');
    })
    .catch(error => {
        // 静默失败，不干扰用户学习
        console.error('保存失败:', error);
    });
}
```

**离线检测**:
```javascript
window.addEventListener('online', function() {
    showMessage('网络已恢复', 'info');
    syncPendingData();  // 同步离线期间的数据
});

window.addEventListener('offline', function() {
    showMessage('网络已断开，数据将在恢复后同步', 'warning');
});
```

#### 6. 无障碍优化

**语义化 HTML**:
```html
<main role="main">
    <section aria-label="学习区域">
        <h2 id="question-heading">当前题目</h2>
        <div role="region" aria-labelledby="question-heading">
            <p class="thai-word" lang="th">สวัสดี</p>
        </div>
    </section>
</main>
```

**ARIA 属性**:
```html
<button aria-label="播放泰语发音"
        aria-pressed="false"
        onclick="playAudio()">
    🔊
</button>

<div role="alert" aria-live="polite" class="feedback">
    <!-- 答题反馈会在这里显示 -->
</div>
```

## 九、测试与部署

### 测试策略

#### 单元测试

**测试框架配置**:
```python
# tests/conftest.py
import pytest
from app import create_app, db
from app.models import User, Vocabulary, UserVocabulary

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

@pytest.fixture
def sample_user(app):
    user = User(username='testuser', email='test@example.com')
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def sample_vocab(app):
    vocab = Vocabulary(
        thai_word='สวัสดี',
        chinese_meaning='你好',
        pronunciation='sa-wat-dee',
        category='日常用语',
        difficulty_level=1
    )
    db.session.add(vocab)
    db.session.commit()
    return vocab
```

**模型测试**:
```python
# tests/test_models.py
def test_user_password_hashing(app):
    user = User(username='test', email='test@test.com')
    user.set_password('secret')

    assert user.password_hash != 'secret'
    assert user.check_password('secret')
    assert not user.check_password('wrong')

def test_vocabulary_creation(app, sample_vocab):
    assert sample_vocab.thai_word == 'สวัสดี'
    assert sample_vocab.difficulty_level == 1

def test_user_vocabulary_relationship(app, sample_user, sample_vocab):
    uv = UserVocabulary(
        user_id=sample_user.id,
        vocabulary_id=sample_vocab.id,
        familiarity_level=3
    )
    db.session.add(uv)
    db.session.commit()

    assert sample_user.vocabularies.count() == 1
    assert sample_user.vocabularies.first().vocabulary.thai_word == 'สวัสดี'
```

**SRS 算法测试**:
```python
# tests/test_srs.py
from app.utils.srs import calculate_next_review
from datetime import timedelta

def test_srs_failed_review():
    """答错后应该 10 分钟内复习"""
    interval = calculate_next_review(familiarity=2, review_count=5)
    assert interval == 10

def test_srs_first_success():
    """首次答对应该 1 天后复习"""
    interval = calculate_next_review(familiarity=3, review_count=0)
    assert interval == 1440  # 1 天 = 1440 分钟

def test_srs_progression():
    """复习间隔应该递增"""
    intervals = [
        calculate_next_review(familiarity=4, review_count=i)
        for i in range(7)
    ]
    # 确保间隔递增
    assert all(intervals[i] <= intervals[i+1] for i in range(len(intervals)-1))
```

**认证测试**:
```python
# tests/test_auth.py
def test_register(client):
    response = client.post('/auth/register', data={
        'username': 'newuser',
        'email': 'new@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert User.query.filter_by(username='newuser').first() is not None

def test_login_logout(client, sample_user):
    # 登录
    response = client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'password123'
    }, follow_redirects=True)

    assert b'登录成功' in response.data

    # 登出
    response = client.get('/auth/logout', follow_redirects=True)
    assert b'已登出' in response.data

def test_login_required(client):
    """未登录访问受保护页面应重定向"""
    response = client.get('/learning/start')
    assert response.status_code == 302  # Redirect
```

#### 集成测试

```python
# tests/test_learning_flow.py
def test_complete_learning_session(client, sample_user, sample_vocab):
    # 1. 登录
    client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'password123'
    })

    # 2. 开始学习
    response = client.get('/learning/start')
    assert response.status_code == 200

    # 3. 答题
    response = client.post('/learning/submit', json={
        'vocabulary_id': sample_vocab.id,
        'quiz_type': 'flashcard',
        'familiarity': 4,
        'time_taken': 5
    })

    assert response.status_code == 200

    # 4. 验证数据更新
    uv = UserVocabulary.query.filter_by(
        user_id=sample_user.id,
        vocabulary_id=sample_vocab.id
    ).first()

    assert uv is not None
    assert uv.familiarity_level == 4
    assert uv.review_count == 1

    # 5. 查看统计
    response = client.get('/stats/dashboard')
    assert b'1' in response.data  # 已学 1 个词
```

#### 手动测试检查清单

**功能测试**:
- [ ] 新用户注册流程
- [ ] 登录/登出功能
- [ ] 四种题型答题流程
- [ ] 音频播放（不同浏览器）
- [ ] 进度统计准确性
- [ ] 管理员添加/编辑词汇
- [ ] 批量导入词汇
- [ ] 密码重置（如实现）

**兼容性测试**:
- [ ] Chrome 最新版
- [ ] Firefox 最新版
- [ ] Safari (macOS/iOS)
- [ ] Edge 最新版
- [ ] 移动端浏览器（iOS Safari, Chrome Android）

**数据完整性**:
- [ ] 连续 7 天学习 streak 计数正确
- [ ] SRS 间隔计算正确
- [ ] 答题后数据库更新一致
- [ ] 并发用户数据不冲突

**性能测试**:
- [ ] 1000 词汇加载时间 < 2s
- [ ] 答题响应时间 < 500ms
- [ ] 音频加载时间 < 1s

### 本地开发部署

#### 环境准备

**系统要求**:
- Python 3.8 或更高版本
- pip 包管理器
- SQLite 3（系统自带）

**依赖安装**:
```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

**requirements.txt**:
```
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Login==0.6.3
Flask-WTF==1.2.1
Werkzeug==3.0.1
pytest==7.4.3
python-dotenv==1.0.0
```

#### 配置文件

```python
# config.py
import os
from datetime import timedelta

class Config:
    """基础配置"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'app/static/audio'
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB

    # 会话配置
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # 分页
    ITEMS_PER_PAGE = 20

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///learnthai_dev.db'
    SQLALCHEMY_ECHO = True  # 打印 SQL 语句

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # 内存数据库
    WTF_CSRF_ENABLED = False  # 测试时禁用 CSRF

class ProductionConfig(Config):
    """生产环境配置"""
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///learnthai.db'
    SESSION_COOKIE_SECURE = True  # 仅 HTTPS

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
```

#### 初始化脚本

**数据库初始化**:
```python
# init_db.py
from app import create_app, db

def init_database():
    app = create_app()
    with app.app_context():
        # 创建所有表
        db.create_all()
        print("数据库表创建成功！")

if __name__ == '__main__':
    init_database()
```

**创建管理员账户**:
```python
# create_admin.py
from app import create_app, db
from app.models import User
import getpass

def create_admin():
    app = create_app()
    with app.app_context():
        username = input("管理员用户名: ")
        email = input("管理员邮箱: ")
        password = getpass.getpass("管理员密码: ")

        # 检查用户是否已存在
        if User.query.filter_by(username=username).first():
            print(f"错误：用户名 '{username}' 已存在")
            return

        admin = User(
            username=username,
            email=email,
            is_admin=True
        )
        admin.set_password(password)

        db.session.add(admin)
        db.session.commit()

        print(f"管理员账户 '{username}' 创建成功！")

if __name__ == '__main__':
    create_admin()
```

#### 启动应用

```python
# run.py
from app import create_app
import os

app = create_app(os.getenv('FLASK_ENV') or 'default')

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',  # 允许外部访问
        port=5000,
        debug=True       # 开发模式
    )
```

**启动步骤**:
```bash
# 1. 初始化数据库
python init_db.py

# 2. 导入初始词汇
python import_vocab.py data/basic_vocab.csv

# 3. 创建管理员
python create_admin.py

# 4. 启动应用
python run.py

# 访问 http://localhost:5000
```

**开发工具**:
```bash
# 使用 Flask CLI
export FLASK_APP=run.py
export FLASK_ENV=development

# 运行开发服务器
flask run

# 打开交互式 shell
flask shell

# 数据库迁移（使用 Flask-Migrate）
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 未来部署选项

**注意**: 以下为原型完成后的生产部署参考，当前阶段**不实现**。

#### Heroku 部署

```bash
# 1. 创建 Procfile
echo "web: gunicorn run:app" > Procfile

# 2. 添加 gunicorn 到 requirements.txt
echo "gunicorn==21.2.0" >> requirements.txt

# 3. 部署
heroku create learnthai-app
git push heroku main
heroku run python init_db.py
```

#### Docker 容器化

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-b", "0.0.0.0:5000", "run:app"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://user:pass@db/learnthai
    depends_on:
      - db

  db:
    image: postgres:14
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=learnthai
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

#### VPS 部署（Nginx + Gunicorn）

```nginx
# /etc/nginx/sites-available/learnthai
server {
    listen 80;
    server_name learnthai.example.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static {
        alias /var/www/learnthai/app/static;
        expires 30d;
    }
}
```

```bash
# systemd 服务配置
# /etc/systemd/system/learnthai.service
[Unit]
Description=LearnThai Flask Application
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/learnthai
Environment="PATH=/var/www/learnthai/venv/bin"
ExecStart=/var/www/learnthai/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 run:app

[Install]
WantedBy=multi-user.target
```

## 总结

### 项目特性

✅ **技术栈**: Flask 单体架构，快速原型开发
✅ **用户界面**: 中文界面，专为中文用户设计
✅ **核心功能**: 中泰词汇对照学习，支持音频发音
✅ **学习算法**: SM-2 间隔重复算法，科学记忆
✅ **题型丰富**: 闪卡、选择题、听力、拼写四种模式
✅ **用户系统**: 完整的注册/登录/权限管理
✅ **进度追踪**: 详细的学习统计和可视化图表
✅ **内容管理**: 灵活的词汇分类和批量导入
✅ **用户体验**: 响应式设计，移动端友好

### 开发优先级

**第一阶段**（核心功能）:
1. 基础架构搭建（Flask + 数据库）
2. 用户认证系统
3. 词汇数据模型和导入
4. 闪卡模式（最简单的学习方式）
5. 基本 SRS 算法

**第二阶段**（功能扩展）:
1. 其他三种题型
2. 音频播放功能
3. 进度统计仪表板
4. 管理员后台

**第三阶段**（优化完善）:
1. 可视化图表
2. 性能优化
3. 移动端适配
4. 完整测试覆盖

### 技术债务与未来改进

**当前简化的部分**（可后期优化）:
- 邮箱验证：注册时跳过邮箱验证
- 密码强度：最低 6 位（可增强到 8 位+复杂度要求）
- 音频来源：手动上传或 TTS（可接入专业泰语语音库）
- 数据库：SQLite（生产环境建议迁移到 PostgreSQL）
- 缓存：无缓存层（可添加 Redis）

**可扩展功能**（超出当前范围）:
- 社交功能：学习小组、排行榜
- 个性化推荐：AI 推荐学习内容
- 移动应用：React Native/Flutter 版本
- 离线模式：PWA 支持
- 语音识别：口语练习评分

---

**文档版本**: 1.0
**创建日期**: 2026-01-14
**目标**: 工作原型（本地开发）
**预计开发时间**: 视实现进度而定（无时间压力）
