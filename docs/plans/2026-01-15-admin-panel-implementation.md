# 管理后台实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为 LearnThai 添加完整管理后台，包括仪表板、词汇管理和用户管理。

**Architecture:** Flask 蓝图模式，添加 admin 蓝图处理所有 /admin/* 路由。使用装饰器进行管理员权限验证。纯 CSS 实现图表，无需引入外部库。

**Tech Stack:** Flask, SQLAlchemy, Jinja2, CSS

---

## 任务 1：添加 User.is_active 字段

**涉及文件：**
- 修改：`app/models.py`
- 修改：`app/routes/auth.py`
- 创建：`tests/test_admin.py`

**步骤 1：修改 User 模型添加 is_active 字段**

在 `app/models.py` 的 User 类中，在 `is_admin` 后添加：

```python
is_active = db.Column(db.Boolean, default=True)
```

**步骤 2：修改登录逻辑检查 is_active**

在 `app/routes/auth.py` 的 login 函数中，修改验证逻辑：

```python
if user is None or not user.check_password(password):
    flash('用户名或密码错误', 'error')
    return render_template('auth/login.html')

if not user.is_active:
    flash('账户已被禁用', 'error')
    return render_template('auth/login.html')
```

**步骤 3：创建测试文件**

创建 `tests/test_admin.py`：

```python
from app.models import User
from app import db

def test_inactive_user_cannot_login(client, app):
    """测试禁用用户无法登录"""
    with app.app_context():
        user = User(username='inactive', email='inactive@test.com', is_active=False)
        user.set_password('pass')
        db.session.add(user)
        db.session.commit()

    response = client.post('/auth/login', data={
        'username': 'inactive',
        'password': 'pass'
    }, follow_redirects=True)

    assert '账户已被禁用' in response.data.decode('utf-8')
```

**步骤 4：运行测试**

运行：`pytest tests/test_admin.py::test_inactive_user_cannot_login -v`
预期：通过

**步骤 5：重建数据库**

运行：`python init_db.py`
预期：数据库表更新成功

**步骤 6：提交**

```bash
git add app/models.py app/routes/auth.py tests/test_admin.py
git commit -m "feat: 添加用户 is_active 字段和禁用登录检查

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## 任务 2：创建管理员权限装饰器

**涉及文件：**
- 创建：`app/utils/decorators.py`
- 修改：`tests/test_admin.py`

**步骤 1：创建装饰器文件**

创建 `app/utils/decorators.py`：

```python
from functools import wraps
from flask import flash, redirect, url_for, abort
from flask_login import current_user

def admin_required(f):
    """要求用户是管理员"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('请先登录', 'error')
            return redirect(url_for('auth.login'))
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
```

**步骤 2：添加测试**

在 `tests/test_admin.py` 中添加：

```python
def test_non_admin_cannot_access_admin(client, app):
    """测试非管理员无法访问后台"""
    with app.app_context():
        user = User(username='normal', email='normal@test.com', is_admin=False)
        user.set_password('pass')
        db.session.add(user)
        db.session.commit()

    client.post('/auth/login', data={
        'username': 'normal',
        'password': 'pass'
    })

    response = client.get('/admin/')
    assert response.status_code == 403

def test_admin_can_access_admin(client, app):
    """测试管理员可以访问后台"""
    with app.app_context():
        admin = User(username='admin', email='admin@test.com', is_admin=True)
        admin.set_password('pass')
        db.session.add(admin)
        db.session.commit()

    client.post('/auth/login', data={
        'username': 'admin',
        'password': 'pass'
    })

    response = client.get('/admin/')
    assert response.status_code == 200
```

**步骤 3：运行测试确认失败**

运行：`pytest tests/test_admin.py::test_non_admin_cannot_access_admin -v`
预期：失败（404，路由尚不存在）

**步骤 4：提交装饰器**

```bash
git add app/utils/decorators.py
git commit -m "feat: 添加 admin_required 装饰器

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## 任务 3：创建管理后台基础框架

**涉及文件：**
- 创建：`app/routes/admin.py`
- 创建：`app/templates/admin/base_admin.html`
- 创建：`app/templates/admin/dashboard.html`
- 修改：`app/__init__.py`
- 修改：`app/templates/base.html`

**步骤 1：创建管理蓝图**

创建 `app/routes/admin.py`：

```python
from flask import Blueprint, render_template
from flask_login import current_user
from app.utils.decorators import admin_required
from app import db
from app.models import User, Vocabulary, UserVocabulary, QuizAttempt
from datetime import datetime, timedelta
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@admin_required
def dashboard():
    """管理仪表板"""
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())

    # 统计数据
    stats = {
        'total_users': User.query.count(),
        'new_users_today': User.query.filter(User.created_at >= today_start).count(),
        'total_vocab': Vocabulary.query.count(),
        'active_vocab': Vocabulary.query.filter_by(is_active=True).count(),
        'active_users_today': db.session.query(func.count(func.distinct(QuizAttempt.user_id))).filter(
            QuizAttempt.created_at >= today_start
        ).scalar() or 0,
        'total_attempts': QuizAttempt.query.count(),
        'attempts_today': QuizAttempt.query.filter(QuizAttempt.created_at >= today_start).count(),
    }

    # 最近7天活跃趋势
    daily_active = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_start = datetime.combine(day, datetime.min.time())
        day_end = datetime.combine(day, datetime.max.time())
        count = db.session.query(func.count(func.distinct(QuizAttempt.user_id))).filter(
            QuizAttempt.created_at >= day_start,
            QuizAttempt.created_at <= day_end
        ).scalar() or 0
        daily_active.append({'date': day.strftime('%m-%d'), 'count': count})

    # 熟悉度分布
    familiarity_dist = []
    for level in range(6):
        count = UserVocabulary.query.filter_by(familiarity_level=level).count()
        familiarity_dist.append({'level': level, 'count': count})

    # 困难词汇 TOP 5
    difficult_vocab = db.session.query(
        Vocabulary.thai_word,
        Vocabulary.chinese_meaning,
        func.count(QuizAttempt.id).label('total'),
        func.sum(db.case((QuizAttempt.is_correct == False, 1), else_=0)).label('wrong')
    ).join(QuizAttempt, QuizAttempt.vocabulary_id == Vocabulary.id)\
    .group_by(Vocabulary.id)\
    .having(func.count(QuizAttempt.id) >= 5)\
    .order_by((func.sum(db.case((QuizAttempt.is_correct == False, 1), else_=0)) * 100 / func.count(QuizAttempt.id)).desc())\
    .limit(5).all()

    # 热门词汇 TOP 5
    popular_vocab = db.session.query(
        Vocabulary.thai_word,
        Vocabulary.chinese_meaning,
        func.count(QuizAttempt.id).label('count')
    ).join(QuizAttempt, QuizAttempt.vocabulary_id == Vocabulary.id)\
    .group_by(Vocabulary.id)\
    .order_by(func.count(QuizAttempt.id).desc())\
    .limit(5).all()

    return render_template('admin/dashboard.html',
                          stats=stats,
                          daily_active=daily_active,
                          familiarity_dist=familiarity_dist,
                          difficult_vocab=difficult_vocab,
                          popular_vocab=popular_vocab)
```

**步骤 2：注册蓝图**

修改 `app/__init__.py`，在 learning_bp 注册后添加：

```python
    from app.routes.admin import admin_bp
    app.register_blueprint(admin_bp)
```

**步骤 3：创建管理后台基础模板**

创建目录：`mkdir -p app/templates/admin`

创建 `app/templates/admin/base_admin.html`：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}管理后台{% endblock %} - LearnThai</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/admin.css') }}">
</head>
<body class="admin-body">
    <div class="admin-layout">
        <aside class="admin-sidebar">
            <div class="admin-logo">
                <h2>LearnThai</h2>
                <span>管理后台</span>
            </div>
            <nav class="admin-nav">
                <a href="{{ url_for('admin.dashboard') }}" class="{% if request.endpoint == 'admin.dashboard' %}active{% endif %}">
                    仪表板
                </a>
                <a href="{{ url_for('admin.vocabulary_list') }}" class="{% if 'vocabulary' in request.endpoint %}active{% endif %}">
                    词汇管理
                </a>
                <a href="{{ url_for('admin.user_list') }}" class="{% if 'user' in request.endpoint %}active{% endif %}">
                    用户管理
                </a>
                <hr>
                <a href="{{ url_for('index') }}">返回前台</a>
            </nav>
        </aside>

        <main class="admin-main">
            <header class="admin-header">
                <h1>{% block page_title %}仪表板{% endblock %}</h1>
                <div class="admin-user">
                    <span>{{ current_user.username }}</span>
                    <a href="{{ url_for('auth.logout') }}">登出</a>
                </div>
            </header>

            <div class="admin-content">
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        <div class="flash-messages">
                            {% for category, message in messages %}
                                <div class="alert alert-{{ category }}">
                                    {{ message }}
                                    <button class="close" onclick="this.parentElement.remove()">&times;</button>
                                </div>
                            {% endfor %}
                        </div>
                    {% endif %}
                {% endwith %}

                {% block content %}{% endblock %}
            </div>
        </main>
    </div>
</body>
</html>
```

**步骤 4：创建仪表板模板**

创建 `app/templates/admin/dashboard.html`：

```html
{% extends "admin/base_admin.html" %}

{% block title %}仪表板{% endblock %}
{% block page_title %}仪表板{% endblock %}

{% block content %}
<div class="stats-cards">
    <div class="stat-card">
        <div class="stat-number">{{ stats.total_users }}</div>
        <div class="stat-label">总用户数</div>
        <div class="stat-sub">今日新增 +{{ stats.new_users_today }}</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">{{ stats.total_vocab }}</div>
        <div class="stat-label">总词汇数</div>
        <div class="stat-sub">已启用 {{ stats.active_vocab }}</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">{{ stats.active_users_today }}</div>
        <div class="stat-label">今日活跃</div>
        <div class="stat-sub">用户数</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">{{ stats.total_attempts }}</div>
        <div class="stat-label">总答题数</div>
        <div class="stat-sub">今日 +{{ stats.attempts_today }}</div>
    </div>
</div>

<div class="charts-row">
    <div class="chart-card">
        <h3>每日活跃趋势（最近7天）</h3>
        <div class="bar-chart">
            {% set max_count = daily_active|map(attribute='count')|max or 1 %}
            {% for day in daily_active %}
            <div class="bar-item">
                <div class="bar" style="height: {{ (day.count / max_count * 100)|int }}%">
                    <span class="bar-value">{{ day.count }}</span>
                </div>
                <span class="bar-label">{{ day.date }}</span>
            </div>
            {% endfor %}
        </div>
    </div>

    <div class="chart-card">
        <h3>词汇掌握度分布</h3>
        <div class="bar-chart horizontal">
            {% set max_fam = familiarity_dist|map(attribute='count')|max or 1 %}
            {% for item in familiarity_dist %}
            <div class="bar-item-h">
                <span class="bar-label-h">等级 {{ item.level }}</span>
                <div class="bar-h" style="width: {{ (item.count / max_fam * 100)|int }}%">
                    <span class="bar-value-h">{{ item.count }}</span>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</div>

<div class="tables-row">
    <div class="table-card">
        <h3>困难词汇 TOP 5</h3>
        <table class="admin-table">
            <thead>
                <tr>
                    <th>泰语</th>
                    <th>中文</th>
                    <th>错误次数</th>
                </tr>
            </thead>
            <tbody>
                {% for vocab in difficult_vocab %}
                <tr>
                    <td>{{ vocab.thai_word }}</td>
                    <td>{{ vocab.chinese_meaning }}</td>
                    <td>{{ vocab.wrong or 0 }}</td>
                </tr>
                {% else %}
                <tr><td colspan="3">暂无数据</td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <div class="table-card">
        <h3>热门词汇 TOP 5</h3>
        <table class="admin-table">
            <thead>
                <tr>
                    <th>泰语</th>
                    <th>中文</th>
                    <th>学习次数</th>
                </tr>
            </thead>
            <tbody>
                {% for vocab in popular_vocab %}
                <tr>
                    <td>{{ vocab.thai_word }}</td>
                    <td>{{ vocab.chinese_meaning }}</td>
                    <td>{{ vocab.count }}</td>
                </tr>
                {% else %}
                <tr><td colspan="3">暂无数据</td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}
```

**步骤 5：创建管理后台 CSS**

创建 `app/static/css/admin.css`：

```css
/* 管理后台样式 */
.admin-body {
    margin: 0;
    padding: 0;
    background: #f0f2f5;
}

.admin-layout {
    display: flex;
    min-height: 100vh;
}

/* 侧边栏 */
.admin-sidebar {
    width: 220px;
    background: #1a1a2e;
    color: white;
    flex-shrink: 0;
}

.admin-logo {
    padding: 20px;
    border-bottom: 1px solid #333;
}

.admin-logo h2 {
    margin: 0;
    font-size: 1.5rem;
}

.admin-logo span {
    font-size: 0.8rem;
    opacity: 0.7;
}

.admin-nav {
    padding: 20px 0;
}

.admin-nav a {
    display: block;
    padding: 12px 20px;
    color: #ccc;
    text-decoration: none;
    transition: all 0.3s;
}

.admin-nav a:hover,
.admin-nav a.active {
    background: #16213e;
    color: white;
    border-left: 3px solid #3498db;
}

.admin-nav hr {
    border: none;
    border-top: 1px solid #333;
    margin: 20px 0;
}

/* 主内容区 */
.admin-main {
    flex: 1;
    display: flex;
    flex-direction: column;
}

.admin-header {
    background: white;
    padding: 15px 30px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.admin-header h1 {
    margin: 0;
    font-size: 1.5rem;
    color: #333;
}

.admin-user {
    display: flex;
    align-items: center;
    gap: 15px;
}

.admin-user a {
    color: #e74c3c;
    text-decoration: none;
}

.admin-content {
    padding: 30px;
    flex: 1;
}

/* 统计卡片 */
.stats-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
}

.stat-card {
    background: white;
    padding: 25px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.stat-number {
    font-size: 2.5rem;
    font-weight: bold;
    color: #3498db;
}

.stat-label {
    font-size: 1rem;
    color: #666;
    margin-top: 5px;
}

.stat-sub {
    font-size: 0.85rem;
    color: #999;
    margin-top: 5px;
}

/* 图表区域 */
.charts-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
}

.chart-card {
    background: white;
    padding: 25px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.chart-card h3 {
    margin: 0 0 20px 0;
    color: #333;
    font-size: 1.1rem;
}

/* 柱状图 */
.bar-chart {
    display: flex;
    align-items: flex-end;
    height: 200px;
    gap: 15px;
    padding: 10px 0;
}

.bar-item {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    height: 100%;
}

.bar {
    width: 100%;
    max-width: 50px;
    background: linear-gradient(to top, #3498db, #5dade2);
    border-radius: 4px 4px 0 0;
    display: flex;
    align-items: flex-start;
    justify-content: center;
    min-height: 20px;
    transition: height 0.3s;
}

.bar-value {
    color: white;
    font-size: 0.8rem;
    padding-top: 5px;
}

.bar-label {
    margin-top: 10px;
    font-size: 0.8rem;
    color: #666;
}

/* 水平柱状图 */
.bar-chart.horizontal {
    flex-direction: column;
    height: auto;
    gap: 10px;
}

.bar-item-h {
    display: flex;
    align-items: center;
    gap: 10px;
}

.bar-label-h {
    width: 60px;
    font-size: 0.85rem;
    color: #666;
}

.bar-h {
    height: 25px;
    background: linear-gradient(to right, #27ae60, #2ecc71);
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: flex-end;
    padding-right: 10px;
    min-width: 30px;
}

.bar-value-h {
    color: white;
    font-size: 0.8rem;
}

/* 表格区域 */
.tables-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 20px;
}

.table-card {
    background: white;
    padding: 25px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.table-card h3 {
    margin: 0 0 15px 0;
    color: #333;
    font-size: 1.1rem;
}

.admin-table {
    width: 100%;
    border-collapse: collapse;
}

.admin-table th,
.admin-table td {
    padding: 12px;
    text-align: left;
    border-bottom: 1px solid #eee;
}

.admin-table th {
    background: #f8f9fa;
    font-weight: 600;
    color: #555;
}

.admin-table tbody tr:hover {
    background: #f8f9fa;
}

/* 响应式 */
@media (max-width: 768px) {
    .admin-sidebar {
        position: fixed;
        left: -220px;
        z-index: 100;
        transition: left 0.3s;
    }

    .admin-sidebar.open {
        left: 0;
    }

    .charts-row,
    .tables-row {
        grid-template-columns: 1fr;
    }
}
```

**步骤 6：在前台导航添加管理入口**

修改 `app/templates/base.html`，在导航栏中添加（在登出链接前）：

```html
{% if current_user.is_admin %}
    <a href="{{ url_for('admin.dashboard') }}">管理后台</a>
{% endif %}
```

**步骤 7：运行测试**

运行：`pytest tests/test_admin.py -v`
预期：test_admin_can_access_admin 通过

**步骤 8：提交**

```bash
git add app/routes/admin.py app/templates/admin/ app/static/css/admin.css app/__init__.py app/templates/base.html
git commit -m "feat: 添加管理后台仪表板

- 统计卡片（用户、词汇、活跃、答题）
- 每日活跃趋势图
- 词汇掌握度分布
- 困难/热门词汇排行

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## 任务 4：词汇管理 - 列表和搜索

**涉及文件：**
- 修改：`app/routes/admin.py`
- 创建：`app/templates/admin/vocabulary_list.html`

**步骤 1：添加词汇列表路由**

在 `app/routes/admin.py` 中添加：

```python
@admin_bp.route('/vocabulary')
@admin_required
def vocabulary_list():
    """词汇列表"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    difficulty = request.args.get('difficulty', '', type=str)
    status = request.args.get('status', '')

    query = Vocabulary.query

    if search:
        query = query.filter(
            db.or_(
                Vocabulary.thai_word.contains(search),
                Vocabulary.chinese_meaning.contains(search)
            )
        )

    if category:
        query = query.filter_by(category=category)

    if difficulty:
        query = query.filter_by(difficulty_level=int(difficulty))

    if status == 'active':
        query = query.filter_by(is_active=True)
    elif status == 'inactive':
        query = query.filter_by(is_active=False)

    pagination = query.order_by(Vocabulary.id.desc()).paginate(page=page, per_page=20)

    # 获取所有分类用于筛选
    categories = db.session.query(Vocabulary.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]

    return render_template('admin/vocabulary_list.html',
                          vocabularies=pagination.items,
                          pagination=pagination,
                          search=search,
                          category=category,
                          difficulty=difficulty,
                          status=status,
                          categories=categories)
```

需要添加 import：`from flask import request`

**步骤 2：创建词汇列表模板**

创建 `app/templates/admin/vocabulary_list.html`：

```html
{% extends "admin/base_admin.html" %}

{% block title %}词汇管理{% endblock %}
{% block page_title %}词汇管理{% endblock %}

{% block content %}
<div class="toolbar">
    <form class="filter-form" method="GET">
        <input type="text" name="search" placeholder="搜索泰语/中文..." value="{{ search }}">
        <select name="category">
            <option value="">全部分类</option>
            {% for cat in categories %}
            <option value="{{ cat }}" {% if category == cat %}selected{% endif %}>{{ cat }}</option>
            {% endfor %}
        </select>
        <select name="difficulty">
            <option value="">全部难度</option>
            {% for i in range(1, 6) %}
            <option value="{{ i }}" {% if difficulty == i|string %}selected{% endif %}>难度 {{ i }}</option>
            {% endfor %}
        </select>
        <select name="status">
            <option value="">全部状态</option>
            <option value="active" {% if status == 'active' %}selected{% endif %}>已启用</option>
            <option value="inactive" {% if status == 'inactive' %}selected{% endif %}>已禁用</option>
        </select>
        <button type="submit" class="btn btn-primary">筛选</button>
        <a href="{{ url_for('admin.vocabulary_list') }}" class="btn">重置</a>
    </form>
    <a href="{{ url_for('admin.vocabulary_add') }}" class="btn btn-primary">添加词汇</a>
</div>

<div class="table-card">
    <table class="admin-table">
        <thead>
            <tr>
                <th>ID</th>
                <th>泰语</th>
                <th>中文</th>
                <th>发音</th>
                <th>分类</th>
                <th>难度</th>
                <th>状态</th>
                <th>操作</th>
            </tr>
        </thead>
        <tbody>
            {% for vocab in vocabularies %}
            <tr>
                <td>{{ vocab.id }}</td>
                <td>{{ vocab.thai_word }}</td>
                <td>{{ vocab.chinese_meaning }}</td>
                <td>{{ vocab.pronunciation or '-' }}</td>
                <td>{{ vocab.category or '-' }}</td>
                <td>{{ vocab.difficulty_level }}</td>
                <td>
                    <span class="status-badge {% if vocab.is_active %}active{% else %}inactive{% endif %}">
                        {{ '启用' if vocab.is_active else '禁用' }}
                    </span>
                </td>
                <td>
                    <a href="{{ url_for('admin.vocabulary_edit', id=vocab.id) }}" class="btn btn-small">编辑</a>
                    <form action="{{ url_for('admin.vocabulary_toggle', id=vocab.id) }}" method="POST" style="display:inline">
                        <button type="submit" class="btn btn-small {% if vocab.is_active %}btn-danger{% else %}btn-success{% endif %}">
                            {{ '禁用' if vocab.is_active else '启用' }}
                        </button>
                    </form>
                </td>
            </tr>
            {% else %}
            <tr>
                <td colspan="8">暂无词汇</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>

{% if pagination.pages > 1 %}
<div class="pagination">
    {% if pagination.has_prev %}
    <a href="{{ url_for('admin.vocabulary_list', page=pagination.prev_num, search=search, category=category, difficulty=difficulty, status=status) }}">&laquo; 上一页</a>
    {% endif %}

    <span>第 {{ pagination.page }} / {{ pagination.pages }} 页</span>

    {% if pagination.has_next %}
    <a href="{{ url_for('admin.vocabulary_list', page=pagination.next_num, search=search, category=category, difficulty=difficulty, status=status) }}">下一页 &raquo;</a>
    {% endif %}
</div>
{% endif %}
{% endblock %}
```

**步骤 3：添加工具栏和分页样式**

在 `app/static/css/admin.css` 末尾添加：

```css
/* 工具栏 */
.toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    flex-wrap: wrap;
    gap: 15px;
}

.filter-form {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
}

.filter-form input,
.filter-form select {
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 0.9rem;
}

.filter-form input {
    width: 200px;
}

/* 按钮 */
.btn-small {
    padding: 5px 10px;
    font-size: 0.8rem;
}

.btn-danger {
    background: #e74c3c;
    color: white;
}

.btn-danger:hover {
    background: #c0392b;
}

.btn-success {
    background: #27ae60;
    color: white;
}

.btn-success:hover {
    background: #1e8449;
}

/* 状态标签 */
.status-badge {
    padding: 3px 8px;
    border-radius: 3px;
    font-size: 0.8rem;
}

.status-badge.active {
    background: #d4edda;
    color: #155724;
}

.status-badge.inactive {
    background: #f8d7da;
    color: #721c24;
}

/* 分页 */
.pagination {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 20px;
    margin-top: 20px;
}

.pagination a {
    color: #3498db;
    text-decoration: none;
}

.pagination a:hover {
    text-decoration: underline;
}
```

**步骤 4：提交**

```bash
git add app/routes/admin.py app/templates/admin/vocabulary_list.html app/static/css/admin.css
git commit -m "feat: 添加词汇列表页面

- 分页显示
- 搜索和筛选功能
- 状态切换按钮

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## 任务 5：词汇管理 - 增删改

**涉及文件：**
- 修改：`app/routes/admin.py`
- 创建：`app/templates/admin/vocabulary_form.html`

**步骤 1：添加词汇 CRUD 路由**

在 `app/routes/admin.py` 中添加：

```python
@admin_bp.route('/vocabulary/add', methods=['GET', 'POST'])
@admin_required
def vocabulary_add():
    """添加词汇"""
    if request.method == 'POST':
        vocab = Vocabulary(
            thai_word=request.form['thai_word'].strip(),
            chinese_meaning=request.form['chinese_meaning'].strip(),
            pronunciation=request.form.get('pronunciation', '').strip(),
            category=request.form.get('category', '').strip(),
            difficulty_level=int(request.form.get('difficulty_level', 1)),
            example_sentence_thai=request.form.get('example_thai', '').strip(),
            example_sentence_chinese=request.form.get('example_chinese', '').strip(),
            is_active=request.form.get('is_active') == 'on'
        )
        db.session.add(vocab)
        db.session.commit()
        flash('词汇添加成功', 'success')
        return redirect(url_for('admin.vocabulary_list'))

    categories = db.session.query(Vocabulary.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    return render_template('admin/vocabulary_form.html', vocab=None, categories=categories)

@admin_bp.route('/vocabulary/<int:id>', methods=['GET', 'POST'])
@admin_required
def vocabulary_edit(id):
    """编辑词汇"""
    vocab = Vocabulary.query.get_or_404(id)

    if request.method == 'POST':
        vocab.thai_word = request.form['thai_word'].strip()
        vocab.chinese_meaning = request.form['chinese_meaning'].strip()
        vocab.pronunciation = request.form.get('pronunciation', '').strip()
        vocab.category = request.form.get('category', '').strip()
        vocab.difficulty_level = int(request.form.get('difficulty_level', 1))
        vocab.example_sentence_thai = request.form.get('example_thai', '').strip()
        vocab.example_sentence_chinese = request.form.get('example_chinese', '').strip()
        vocab.is_active = request.form.get('is_active') == 'on'

        db.session.commit()
        flash('词汇更新成功', 'success')
        return redirect(url_for('admin.vocabulary_list'))

    categories = db.session.query(Vocabulary.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    return render_template('admin/vocabulary_form.html', vocab=vocab, categories=categories)

@admin_bp.route('/vocabulary/<int:id>/toggle', methods=['POST'])
@admin_required
def vocabulary_toggle(id):
    """切换词汇状态"""
    vocab = Vocabulary.query.get_or_404(id)
    vocab.is_active = not vocab.is_active
    db.session.commit()
    flash(f"词汇已{'启用' if vocab.is_active else '禁用'}", 'success')
    return redirect(url_for('admin.vocabulary_list'))
```

需要添加 import：`from flask import redirect, url_for, flash`

**步骤 2：创建词汇表单模板**

创建 `app/templates/admin/vocabulary_form.html`：

```html
{% extends "admin/base_admin.html" %}

{% block title %}{{ '编辑词汇' if vocab else '添加词汇' }}{% endblock %}
{% block page_title %}{{ '编辑词汇' if vocab else '添加词汇' }}{% endblock %}

{% block content %}
<div class="form-card">
    <form method="POST" class="admin-form">
        <div class="form-row">
            <div class="form-group">
                <label for="thai_word">泰语词 *</label>
                <input type="text" id="thai_word" name="thai_word" required
                       value="{{ vocab.thai_word if vocab else '' }}">
            </div>
            <div class="form-group">
                <label for="chinese_meaning">中文释义 *</label>
                <input type="text" id="chinese_meaning" name="chinese_meaning" required
                       value="{{ vocab.chinese_meaning if vocab else '' }}">
            </div>
        </div>

        <div class="form-row">
            <div class="form-group">
                <label for="pronunciation">发音</label>
                <input type="text" id="pronunciation" name="pronunciation"
                       value="{{ vocab.pronunciation if vocab else '' }}">
            </div>
            <div class="form-group">
                <label for="category">分类</label>
                <input type="text" id="category" name="category" list="categories"
                       value="{{ vocab.category if vocab else '' }}">
                <datalist id="categories">
                    {% for cat in categories %}
                    <option value="{{ cat }}">
                    {% endfor %}
                </datalist>
            </div>
        </div>

        <div class="form-row">
            <div class="form-group">
                <label for="difficulty_level">难度等级</label>
                <select id="difficulty_level" name="difficulty_level">
                    {% for i in range(1, 6) %}
                    <option value="{{ i }}" {% if vocab and vocab.difficulty_level == i %}selected{% endif %}>
                        {{ i }}
                    </option>
                    {% endfor %}
                </select>
            </div>
            <div class="form-group">
                <label class="checkbox-label">
                    <input type="checkbox" name="is_active"
                           {% if not vocab or vocab.is_active %}checked{% endif %}>
                    启用此词汇
                </label>
            </div>
        </div>

        <div class="form-group">
            <label for="example_thai">例句（泰语）</label>
            <textarea id="example_thai" name="example_thai" rows="2">{{ vocab.example_sentence_thai if vocab else '' }}</textarea>
        </div>

        <div class="form-group">
            <label for="example_chinese">例句（中文）</label>
            <textarea id="example_chinese" name="example_chinese" rows="2">{{ vocab.example_sentence_chinese if vocab else '' }}</textarea>
        </div>

        <div class="form-actions">
            <button type="submit" class="btn btn-primary">{{ '保存修改' if vocab else '添加词汇' }}</button>
            <a href="{{ url_for('admin.vocabulary_list') }}" class="btn">取消</a>
        </div>
    </form>
</div>
{% endblock %}
```

**步骤 3：添加表单样式**

在 `app/static/css/admin.css` 末尾添加：

```css
/* 表单卡片 */
.form-card {
    background: white;
    padding: 30px;
    border-radius: 8px;
    max-width: 800px;
}

.admin-form .form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-bottom: 20px;
}

.admin-form .form-group {
    display: flex;
    flex-direction: column;
}

.admin-form label {
    margin-bottom: 5px;
    font-weight: 500;
    color: #333;
}

.admin-form input,
.admin-form select,
.admin-form textarea {
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 1rem;
}

.admin-form input:focus,
.admin-form select:focus,
.admin-form textarea:focus {
    outline: none;
    border-color: #3498db;
}

.checkbox-label {
    flex-direction: row !important;
    align-items: center;
    gap: 10px;
    margin-top: 25px;
}

.checkbox-label input {
    width: auto;
}

.form-actions {
    display: flex;
    gap: 10px;
    margin-top: 30px;
}

@media (max-width: 600px) {
    .admin-form .form-row {
        grid-template-columns: 1fr;
    }
}
```

**步骤 4：提交**

```bash
git add app/routes/admin.py app/templates/admin/vocabulary_form.html app/static/css/admin.css
git commit -m "feat: 添加词汇增删改功能

- 添加词汇表单
- 编辑词汇
- 切换启用/禁用状态

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## 任务 6：用户管理 - 列表

**涉及文件：**
- 修改：`app/routes/admin.py`
- 创建：`app/templates/admin/user_list.html`

**步骤 1：添加用户列表路由**

在 `app/routes/admin.py` 中添加：

```python
@admin_bp.route('/users')
@admin_required
def user_list():
    """用户列表"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')

    query = User.query

    if search:
        query = query.filter(
            db.or_(
                User.username.contains(search),
                User.email.contains(search)
            )
        )

    pagination = query.order_by(User.created_at.desc()).paginate(page=page, per_page=20)

    # 获取每个用户的学习词汇数
    user_vocab_counts = {}
    for user in pagination.items:
        user_vocab_counts[user.id] = UserVocabulary.query.filter_by(user_id=user.id).count()

    return render_template('admin/user_list.html',
                          users=pagination.items,
                          pagination=pagination,
                          search=search,
                          user_vocab_counts=user_vocab_counts)
```

**步骤 2：创建用户列表模板**

创建 `app/templates/admin/user_list.html`：

```html
{% extends "admin/base_admin.html" %}

{% block title %}用户管理{% endblock %}
{% block page_title %}用户管理{% endblock %}

{% block content %}
<div class="toolbar">
    <form class="filter-form" method="GET">
        <input type="text" name="search" placeholder="搜索用户名/邮箱..." value="{{ search }}">
        <button type="submit" class="btn btn-primary">搜索</button>
        <a href="{{ url_for('admin.user_list') }}" class="btn">重置</a>
    </form>
</div>

<div class="table-card">
    <table class="admin-table">
        <thead>
            <tr>
                <th>ID</th>
                <th>用户名</th>
                <th>邮箱</th>
                <th>注册时间</th>
                <th>最后登录</th>
                <th>学习词汇</th>
                <th>角色</th>
                <th>状态</th>
                <th>操作</th>
            </tr>
        </thead>
        <tbody>
            {% for user in users %}
            <tr>
                <td>{{ user.id }}</td>
                <td>{{ user.username }}</td>
                <td>{{ user.email }}</td>
                <td>{{ user.created_at.strftime('%Y-%m-%d') if user.created_at else '-' }}</td>
                <td>{{ user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else '从未' }}</td>
                <td>{{ user_vocab_counts.get(user.id, 0) }}</td>
                <td>
                    <span class="role-badge {% if user.is_admin %}admin{% endif %}">
                        {{ '管理员' if user.is_admin else '用户' }}
                    </span>
                </td>
                <td>
                    <span class="status-badge {% if user.is_active %}active{% else %}inactive{% endif %}">
                        {{ '正常' if user.is_active else '禁用' }}
                    </span>
                </td>
                <td>
                    <a href="{{ url_for('admin.user_detail', id=user.id) }}" class="btn btn-small">详情</a>
                </td>
            </tr>
            {% else %}
            <tr>
                <td colspan="9">暂无用户</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>

{% if pagination.pages > 1 %}
<div class="pagination">
    {% if pagination.has_prev %}
    <a href="{{ url_for('admin.user_list', page=pagination.prev_num, search=search) }}">&laquo; 上一页</a>
    {% endif %}

    <span>第 {{ pagination.page }} / {{ pagination.pages }} 页</span>

    {% if pagination.has_next %}
    <a href="{{ url_for('admin.user_list', page=pagination.next_num, search=search) }}">下一页 &raquo;</a>
    {% endif %}
</div>
{% endif %}
{% endblock %}
```

**步骤 3：添加角色标签样式**

在 `app/static/css/admin.css` 末尾添加：

```css
/* 角色标签 */
.role-badge {
    padding: 3px 8px;
    border-radius: 3px;
    font-size: 0.8rem;
    background: #e9ecef;
    color: #666;
}

.role-badge.admin {
    background: #fff3cd;
    color: #856404;
}
```

**步骤 4：提交**

```bash
git add app/routes/admin.py app/templates/admin/user_list.html app/static/css/admin.css
git commit -m "feat: 添加用户列表页面

- 分页显示
- 搜索功能
- 显示学习词汇数和状态

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## 任务 7：用户管理 - 详情和操作

**涉及文件：**
- 修改：`app/routes/admin.py`
- 创建：`app/templates/admin/user_detail.html`

**步骤 1：添加用户详情路由**

在 `app/routes/admin.py` 中添加：

```python
@admin_bp.route('/users/<int:id>')
@admin_required
def user_detail(id):
    """用户详情"""
    user = User.query.get_or_404(id)

    # 学习统计
    total_vocab = UserVocabulary.query.filter_by(user_id=id).count()
    mastered_vocab = UserVocabulary.query.filter(
        UserVocabulary.user_id == id,
        UserVocabulary.familiarity_level >= 4
    ).count()

    total_attempts = QuizAttempt.query.filter_by(user_id=id).count()
    correct_attempts = QuizAttempt.query.filter_by(user_id=id, is_correct=True).count()
    accuracy = round(correct_attempts / total_attempts * 100, 1) if total_attempts > 0 else 0

    # 最近7天学习情况
    today = datetime.utcnow().date()
    recent_activity = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_start = datetime.combine(day, datetime.min.time())
        day_end = datetime.combine(day, datetime.max.time())
        count = QuizAttempt.query.filter(
            QuizAttempt.user_id == id,
            QuizAttempt.created_at >= day_start,
            QuizAttempt.created_at <= day_end
        ).count()
        recent_activity.append({'date': day.strftime('%m-%d'), 'count': count})

    return render_template('admin/user_detail.html',
                          user=user,
                          total_vocab=total_vocab,
                          mastered_vocab=mastered_vocab,
                          total_attempts=total_attempts,
                          accuracy=accuracy,
                          recent_activity=recent_activity)

@admin_bp.route('/users/<int:id>/toggle-active', methods=['POST'])
@admin_required
def user_toggle_active(id):
    """切换用户状态"""
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('不能禁用自己的账户', 'error')
    else:
        user.is_active = not user.is_active
        db.session.commit()
        flash(f"用户已{'启用' if user.is_active else '禁用'}", 'success')
    return redirect(url_for('admin.user_detail', id=id))

@admin_bp.route('/users/<int:id>/toggle-admin', methods=['POST'])
@admin_required
def user_toggle_admin(id):
    """切换管理员权限"""
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('不能修改自己的权限', 'error')
    else:
        user.is_admin = not user.is_admin
        db.session.commit()
        flash(f"用户已{'设为管理员' if user.is_admin else '取消管理员'}", 'success')
    return redirect(url_for('admin.user_detail', id=id))
```

**步骤 2：创建用户详情模板**

创建 `app/templates/admin/user_detail.html`：

```html
{% extends "admin/base_admin.html" %}

{% block title %}用户详情{% endblock %}
{% block page_title %}用户详情 - {{ user.username }}{% endblock %}

{% block content %}
<div class="detail-grid">
    <div class="detail-card">
        <h3>基本信息</h3>
        <div class="info-list">
            <div class="info-item">
                <span class="info-label">用户名</span>
                <span class="info-value">{{ user.username }}</span>
            </div>
            <div class="info-item">
                <span class="info-label">邮箱</span>
                <span class="info-value">{{ user.email }}</span>
            </div>
            <div class="info-item">
                <span class="info-label">注册时间</span>
                <span class="info-value">{{ user.created_at.strftime('%Y-%m-%d %H:%M') if user.created_at else '-' }}</span>
            </div>
            <div class="info-item">
                <span class="info-label">最后登录</span>
                <span class="info-value">{{ user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else '从未登录' }}</span>
            </div>
            <div class="info-item">
                <span class="info-label">角色</span>
                <span class="info-value">
                    <span class="role-badge {% if user.is_admin %}admin{% endif %}">
                        {{ '管理员' if user.is_admin else '普通用户' }}
                    </span>
                </span>
            </div>
            <div class="info-item">
                <span class="info-label">状态</span>
                <span class="info-value">
                    <span class="status-badge {% if user.is_active %}active{% else %}inactive{% endif %}">
                        {{ '正常' if user.is_active else '已禁用' }}
                    </span>
                </span>
            </div>
        </div>

        <div class="action-buttons">
            <form action="{{ url_for('admin.user_toggle_active', id=user.id) }}" method="POST" style="display:inline">
                <button type="submit" class="btn {% if user.is_active %}btn-danger{% else %}btn-success{% endif %}">
                    {{ '禁用账户' if user.is_active else '启用账户' }}
                </button>
            </form>
            <form action="{{ url_for('admin.user_toggle_admin', id=user.id) }}" method="POST" style="display:inline">
                <button type="submit" class="btn">
                    {{ '取消管理员' if user.is_admin else '设为管理员' }}
                </button>
            </form>
        </div>
    </div>

    <div class="detail-card">
        <h3>学习统计</h3>
        <div class="stats-mini">
            <div class="stat-mini">
                <div class="stat-mini-value">{{ total_vocab }}</div>
                <div class="stat-mini-label">已学词汇</div>
            </div>
            <div class="stat-mini">
                <div class="stat-mini-value">{{ mastered_vocab }}</div>
                <div class="stat-mini-label">已掌握</div>
            </div>
            <div class="stat-mini">
                <div class="stat-mini-value">{{ total_attempts }}</div>
                <div class="stat-mini-label">答题次数</div>
            </div>
            <div class="stat-mini">
                <div class="stat-mini-value">{{ accuracy }}%</div>
                <div class="stat-mini-label">正确率</div>
            </div>
        </div>
    </div>
</div>

<div class="detail-card" style="margin-top: 20px;">
    <h3>最近7天学习情况</h3>
    <div class="bar-chart">
        {% set max_count = recent_activity|map(attribute='count')|max or 1 %}
        {% for day in recent_activity %}
        <div class="bar-item">
            <div class="bar" style="height: {{ (day.count / max_count * 100)|int if day.count > 0 else 5 }}%">
                <span class="bar-value">{{ day.count }}</span>
            </div>
            <span class="bar-label">{{ day.date }}</span>
        </div>
        {% endfor %}
    </div>
</div>

<div style="margin-top: 20px;">
    <a href="{{ url_for('admin.user_list') }}" class="btn">&laquo; 返回用户列表</a>
</div>
{% endblock %}
```

**步骤 3：添加详情页样式**

在 `app/static/css/admin.css` 末尾添加：

```css
/* 详情页 */
.detail-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: 20px;
}

.detail-card {
    background: white;
    padding: 25px;
    border-radius: 8px;
}

.detail-card h3 {
    margin: 0 0 20px 0;
    padding-bottom: 10px;
    border-bottom: 1px solid #eee;
    color: #333;
}

.info-list {
    display: flex;
    flex-direction: column;
    gap: 15px;
}

.info-item {
    display: flex;
    justify-content: space-between;
}

.info-label {
    color: #666;
}

.info-value {
    font-weight: 500;
}

.action-buttons {
    margin-top: 25px;
    padding-top: 20px;
    border-top: 1px solid #eee;
    display: flex;
    gap: 10px;
}

/* 迷你统计 */
.stats-mini {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 20px;
}

.stat-mini {
    text-align: center;
    padding: 15px;
    background: #f8f9fa;
    border-radius: 8px;
}

.stat-mini-value {
    font-size: 1.8rem;
    font-weight: bold;
    color: #3498db;
}

.stat-mini-label {
    font-size: 0.85rem;
    color: #666;
    margin-top: 5px;
}
```

**步骤 4：运行所有测试**

运行：`pytest -v`
预期：所有测试通过

**步骤 5：提交**

```bash
git add app/routes/admin.py app/templates/admin/user_detail.html app/static/css/admin.css
git commit -m "feat: 添加用户详情和管理操作

- 用户基本信息展示
- 学习统计（词汇数、正确率）
- 最近7天活跃图表
- 禁用/启用账户
- 设置/取消管理员

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## 测试检查清单

完成所有任务后，验证：

- [ ] `pytest -v` 所有测试通过
- [ ] 管理员可以访问 /admin/
- [ ] 非管理员访问 /admin/ 返回 403
- [ ] 仪表板显示正确统计数据
- [ ] 词汇列表分页、搜索、筛选正常
- [ ] 词汇增删改正常
- [ ] 用户列表分页、搜索正常
- [ ] 用户详情显示正确
- [ ] 禁用/启用用户正常
- [ ] 设置/取消管理员正常
- [ ] 禁用用户无法登录

运行：`pytest -v`

预期：所有测试通过
