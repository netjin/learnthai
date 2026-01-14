# LearnThai 泰语词汇学习应用 - 实现计划

> **给 Claude 的提示:** 必须使用技能 superpowers:executing-plans 来逐任务实现此计划。

**目标：** 构建一个面向中文用户的泰语词汇学习 Web 应用，使用间隔重复算法和多种题型。

**架构：** Flask 单体应用，使用 SQLAlchemy ORM、服务端 Jinja2 模板和渐进式 JavaScript 增强、SQLite 数据库、Flask-Login 认证。

**技术栈：** Flask, Flask-SQLAlchemy, Flask-Login, Flask-WTF, pytest, Jinja2

---

## 任务 1：项目基础搭建

**涉及文件：**
- 创建：`requirements.txt`
- 创建：`config.py`
- 创建：`run.py`
- 创建：`app/__init__.py`

**步骤 1：创建依赖文件 requirements.txt**

创建依赖文件：

```txt
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Login==0.6.3
Flask-WTF==1.2.1
Werkzeug==3.0.1
pytest==7.4.3
python-dotenv==1.0.0
```

**步骤 2：创建配置文件 config.py**

```python
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
    SQLALCHEMY_ECHO = True

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
```

**步骤 3：创建应用工厂 app/__init__.py**

```python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config

db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录'

    return app
```

**步骤 4：创建应用入口 run.py**

```python
import os
from app import create_app

app = create_app(os.getenv('FLASK_ENV') or 'default')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

**步骤 5：安装依赖**

运行：`pip install -r requirements.txt`
预期：所有包安装成功

**步骤 6：测试应用启动**

运行：`python run.py`
预期：Flask 服务器在 5000 端口启动（按 Ctrl+C 停止）

**步骤 7：提交**

```bash
git add requirements.txt config.py run.py app/__init__.py
git commit -m "feat: 添加 Flask 项目基础架构

- 添加依赖包（Flask, SQLAlchemy, Login, WTF）
- 配置开发和测试环境
- 创建应用工厂模式
- 添加应用入口 run.py

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## 任务 2：数据库模型

**涉及文件：**
- 创建：`app/models.py`
- 创建：`tests/test_models.py`
- 创建：`tests/__init__.py`
- 创建：`tests/conftest.py`

**步骤 1：为 User 模型编写失败测试**

创建 `tests/__init__.py`（空文件）。

创建 `tests/conftest.py`：

```python
import pytest
from app import create_app, db

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
```

创建 `tests/test_models.py`：

```python
from app.models import User
from app import db

def test_user_password_hashing(app):
    """测试用户密码加密"""
    with app.app_context():
        user = User(username='test', email='test@test.com')
        user.set_password('secret')

        assert user.password_hash is not None
        assert user.password_hash != 'secret'
        assert user.check_password('secret')
        assert not user.check_password('wrong')
```

**步骤 2：运行测试确认失败**

运行：`pytest tests/test_models.py::test_user_password_hashing -v`
预期：失败，提示 "cannot import name 'User' from 'app.models'"

**步骤 3：实现 User 模型**

创建 `app/models.py`：

```python
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # 关系
    vocabularies = db.relationship('UserVocabulary', backref='user', lazy='dynamic')
    quiz_attempts = db.relationship('QuizAttempt', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
```

**步骤 4：运行测试确认通过**

运行：`pytest tests/test_models.py::test_user_password_hashing -v`
预期：通过

**步骤 5：为 Vocabulary 模型编写失败测试**

在 `tests/test_models.py` 中添加：

```python
from app.models import Vocabulary

def test_vocabulary_creation(app):
    """测试词汇创建"""
    with app.app_context():
        vocab = Vocabulary(
            thai_word='สวัสดี',
            chinese_meaning='你好',
            pronunciation='sa-wat-dee',
            category='日常用语',
            difficulty_level=1
        )
        db.session.add(vocab)
        db.session.commit()

        assert vocab.id is not None
        assert vocab.thai_word == 'สวัสดี'
        assert vocab.is_active is True
```

**步骤 6：运行测试确认失败**

运行：`pytest tests/test_models.py::test_vocabulary_creation -v`
预期：失败，提示 "cannot import name 'Vocabulary'"

**步骤 7：实现 Vocabulary 模型**

在 `app/models.py` 中添加：

```python
class Vocabulary(db.Model):
    __tablename__ = 'vocabularies'

    id = db.Column(db.Integer, primary_key=True)
    thai_word = db.Column(db.String(100), nullable=False, index=True)
    chinese_meaning = db.Column(db.String(200), nullable=False)
    pronunciation = db.Column(db.String(100))
    audio_file = db.Column(db.String(200))
    category = db.Column(db.String(50), index=True)
    difficulty_level = db.Column(db.Integer, default=1, index=True)
    frequency_rank = db.Column(db.Integer, index=True)
    example_sentence_thai = db.Column(db.Text)
    example_sentence_chinese = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # 关系
    user_progress = db.relationship('UserVocabulary', backref='vocabulary', lazy='dynamic')

    def __repr__(self):
        return f'<Vocabulary {self.thai_word}>'
```

**步骤 8：运行测试确认通过**

运行：`pytest tests/test_models.py::test_vocabulary_creation -v`
预期：通过

**步骤 9：为 UserVocabulary 关系编写失败测试**

在 `tests/test_models.py` 中添加：

```python
from app.models import UserVocabulary
from datetime import datetime, timedelta

def test_user_vocabulary_relationship(app):
    """测试用户词汇学习进度"""
    with app.app_context():
        user = User(username='learner', email='learner@test.com')
        user.set_password('pass')

        vocab = Vocabulary(
            thai_word='ขอบคุณ',
            chinese_meaning='谢谢',
            category='日常用语',
            difficulty_level=1
        )

        db.session.add(user)
        db.session.add(vocab)
        db.session.commit()

        uv = UserVocabulary(
            user_id=user.id,
            vocabulary_id=vocab.id,
            familiarity_level=3,
            next_review_date=datetime.utcnow() + timedelta(days=1)
        )
        db.session.add(uv)
        db.session.commit()

        assert user.vocabularies.count() == 1
        assert user.vocabularies.first().vocabulary.thai_word == 'ขอบคุณ'
        assert uv.familiarity_level == 3
```

**步骤 10：运行测试确认失败**

运行：`pytest tests/test_models.py::test_user_vocabulary_relationship -v`
预期：失败，提示 "cannot import name 'UserVocabulary'"

**步骤 11：实现 UserVocabulary 模型**

在 `app/models.py` 中添加：

```python
class UserVocabulary(db.Model):
    __tablename__ = 'user_vocabularies'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vocabulary_id = db.Column(db.Integer, db.ForeignKey('vocabularies.id'), nullable=False)
    familiarity_level = db.Column(db.Integer, default=0)  # 0-5
    next_review_date = db.Column(db.DateTime, nullable=False)
    review_count = db.Column(db.Integer, default=0)
    correct_count = db.Column(db.Integer, default=0)
    last_reviewed = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'vocabulary_id', name='unique_user_vocab'),
        db.Index('idx_user_next_review', 'user_id', 'next_review_date'),
    )

    def __repr__(self):
        return f'<UserVocab user={self.user_id} vocab={self.vocabulary_id}>'
```

**步骤 12：运行测试确认通过**

运行：`pytest tests/test_models.py::test_user_vocabulary_relationship -v`
预期：通过

**步骤 13：为 QuizAttempt 模型编写失败测试**

在 `tests/test_models.py` 中添加：

```python
from app.models import QuizAttempt

def test_quiz_attempt_logging(app):
    """测试答题记录"""
    with app.app_context():
        user = User(username='student', email='student@test.com')
        user.set_password('pass')

        vocab = Vocabulary(
            thai_word='สวัสดี',
            chinese_meaning='你好',
            category='日常用语',
            difficulty_level=1
        )

        db.session.add(user)
        db.session.add(vocab)
        db.session.commit()

        attempt = QuizAttempt(
            user_id=user.id,
            vocabulary_id=vocab.id,
            quiz_type='flashcard',
            is_correct=True,
            time_taken=5
        )
        db.session.add(attempt)
        db.session.commit()

        assert user.quiz_attempts.count() == 1
        assert attempt.is_correct is True
        assert attempt.quiz_type == 'flashcard'
```

**步骤 14：运行测试确认失败**

运行：`pytest tests/test_models.py::test_quiz_attempt_logging -v`
预期：失败，提示 "cannot import name 'QuizAttempt'"

**步骤 15：实现 QuizAttempt 模型**

在 `app/models.py` 中添加：

```python
class QuizAttempt(db.Model):
    __tablename__ = 'quiz_attempts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vocabulary_id = db.Column(db.Integer, db.ForeignKey('vocabularies.id'), nullable=False)
    quiz_type = db.Column(db.String(20), nullable=False)  # flashcard, multiple_choice, typing, listening
    is_correct = db.Column(db.Boolean, nullable=False)
    time_taken = db.Column(db.Integer)  # 秒
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        db.Index('idx_user_created', 'user_id', 'created_at'),
    )

    def __repr__(self):
        return f'<QuizAttempt user={self.user_id} correct={self.is_correct}>'
```

**步骤 16：运行测试确认通过**

运行：`pytest tests/test_models.py::test_quiz_attempt_logging -v`
预期：通过

**步骤 17：运行所有模型测试**

运行：`pytest tests/test_models.py -v`
预期：全部 4 个测试通过

**步骤 18：提交**

```bash
git add app/models.py tests/
git commit -m "feat: 添加数据库模型和测试

- 添加 User 模型（带密码加密）
- 添加 Vocabulary 模型（泰语词汇）
- 添加 UserVocabulary 模型（学习进度追踪）
- 添加 QuizAttempt 模型（答题记录）
- 包含完整的测试覆盖

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## 任务 3：数据库初始化脚本

**涉及文件：**
- 创建：`init_db.py`
- 创建：`create_admin.py`
- 创建：`import_vocab.py`
- 创建：`data/basic_vocab.csv`

**步骤 1：创建数据库初始化脚本**

创建 `init_db.py`：

```python
from app import create_app, db

def init_database():
    """初始化数据库"""
    app = create_app()
    with app.app_context():
        db.create_all()
        print("✓ 数据库表创建成功！")

if __name__ == '__main__':
    init_database()
```

**步骤 2：创建管理员创建脚本**

创建 `create_admin.py`：

```python
from app import create_app, db
from app.models import User
import getpass

def create_admin():
    """创建管理员账户"""
    app = create_app()
    with app.app_context():
        username = input("管理员用户名: ")
        email = input("管理员邮箱: ")
        password = getpass.getpass("管理员密码: ")

        if User.query.filter_by(username=username).first():
            print(f"✗ 错误：用户名 '{username}' 已存在")
            return

        if User.query.filter_by(email=email).first():
            print(f"✗ 错误：邮箱 '{email}' 已注册")
            return

        admin = User(username=username, email=email, is_admin=True)
        admin.set_password(password)

        db.session.add(admin)
        db.session.commit()

        print(f"✓ 管理员账户 '{username}' 创建成功！")

if __name__ == '__main__':
    create_admin()
```

**步骤 3：创建词汇导入脚本**

创建 `import_vocab.py`：

```python
import csv
import sys
from app import create_app, db
from app.models import Vocabulary

def import_from_csv(csv_file_path):
    """从 CSV 文件导入词汇"""
    app = create_app()
    with app.app_context():
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                count = 0
                skipped = 0

                for row in reader:
                    # 检查是否已存在
                    existing = Vocabulary.query.filter_by(
                        thai_word=row['thai_word']
                    ).first()

                    if existing:
                        print(f"⊘ 跳过重复词汇: {row['thai_word']}")
                        skipped += 1
                        continue

                    vocab = Vocabulary(
                        thai_word=row['thai_word'],
                        chinese_meaning=row['chinese_meaning'],
                        pronunciation=row.get('pronunciation', ''),
                        category=row.get('category', ''),
                        difficulty_level=int(row.get('difficulty_level', 1)),
                        audio_file=row.get('audio_file', ''),
                        example_sentence_thai=row.get('example_thai', ''),
                        example_sentence_chinese=row.get('example_chinese', '')
                    )
                    db.session.add(vocab)
                    count += 1

                db.session.commit()
                print(f"\n✓ 成功导入 {count} 个词汇")
                if skipped:
                    print(f"⊘ 跳过 {skipped} 个重复词汇")

        except FileNotFoundError:
            print(f"✗ 错误：文件 '{csv_file_path}' 未找到")
            sys.exit(1)
        except Exception as e:
            print(f"✗ 导入失败: {str(e)}")
            sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python import_vocab.py <csv文件路径>")
        sys.exit(1)

    import_from_csv(sys.argv[1])
```

**步骤 4：创建示例词汇数据**

创建目录和文件：

运行：`mkdir -p data`

创建 `data/basic_vocab.csv`：

```csv
thai_word,chinese_meaning,pronunciation,category,difficulty_level,audio_file,example_thai,example_chinese
สวัสดี,你好,sa-wat-dee,日常用语,1,,สวัสดีครับ,你好（男性用语）
สวัสดีครับ,你好（男性），sa-wat-dee-khrap,日常用语,1,,สวัสดีครับ,你好（男性正式用语）
สวัสดีค่ะ,你好（女性），sa-wat-dee-kha,日常用语,1,,สวัสดีค่ะ,你好（女性用语）
ขอบคุณ,谢谢,khop-khun,日常用语,1,,ขอบคุณมาก,非常感谢
ขอบคุณครับ,谢谢（男性），khop-khun-khrap,日常用语,1,,ขอบคุณครับ,谢谢（男性用语）
ขอบคุณค่ะ,谢谢（女性），khop-khun-kha,日常用语,1,,ขอบคุณค่ะ,谢谢（女性用语）
ครับ,是的（男性），khrap,日常用语,1,,ครับผม,是的（男性正式）
ค่ะ,是的（女性），kha,日常用语,1,,ค่ะ,好的（女性）
ไม่,不,mai,日常用语,1,,ไม่ครับ,不（男性）
ไม่เป็นไร,没关系,mai-pen-rai,日常用语,1,,ไม่เป็นไรครับ,没关系（男性）
ลาก่อน,再见,la-gon,日常用语,1,,ลาก่อนครับ,再见（男性）
ขอโทษ,对不起,kho-thot,日常用语,1,,ขอโทษครับ,对不起（男性）
ชื่อ,名字,chue,日常用语,1,,ชื่ออะไร,叫什么名字？
อะไร,什么,arai,日常用语,1,,นี่อะไร,这是什么？
ที่ไหน,哪里,thi-nai,日常用语,1,,ที่ไหน,在哪里？
เท่าไหร่,多少钱,thao-rai,日常用语,1,,ราคาเท่าไหร่,价格多少？
น้ำ,水,nam,食物饮料,1,,น้ำเปล่า,白水
ข้าว,米饭,khao,食物饮料,1,,ข้าวผัด,炒饭
อร่อย,好吃,aroi,食物饮料,1,,อร่อยมาก,非常好吃
หนึ่ง,一,nueng,数字,1,,หนึ่งคน,一个人
สอง,二,song,数字,1,,สองคน,两个人
สาม,三,sam,数字,1,,สามคน,三个人
สี่,四,si,数字,1,,สี่คน,四个人
ห้า,五,ha,数字,1,,ห้าคน,五个人
หก,六,hok,数字,1,,หกคน,六个人
เจ็ด,七,jet,数字,1,,เจ็ดคน,七个人
แปด,八,paet,数字,1,,แปดคน,八个人
เก้า,九,kao,数字,1,,เก้าคน,九个人
สิบ,十,sip,数字,1,,สิบคน,十个人
```

**步骤 5：测试数据库初始化**

运行：`python init_db.py`
预期："✓ 数据库表创建成功！"

**步骤 6：测试词汇导入**

运行：`python import_vocab.py data/basic_vocab.csv`
预期："✓ 成功导入 30 个词汇"

**步骤 7：验证数据库数据**

运行：`python -c "from app import create_app, db; from app.models import Vocabulary; app = create_app(); app.app_context().push(); print(f'Total vocabularies: {Vocabulary.query.count()}')"`
预期："Total vocabularies: 30"

**步骤 8：提交**

```bash
git add init_db.py create_admin.py import_vocab.py data/
git commit -m "feat: 添加数据库管理脚本

- 添加 init_db.py 用于数据库初始化
- 添加 create_admin.py 用于创建管理员账户
- 添加 import_vocab.py 用于 CSV 词汇导入
- 包含 30 个基础泰语词汇在 data/basic_vocab.csv

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## 任务 4：认证系统

**涉及文件：**
- 创建：`app/routes/__init__.py`
- 创建：`app/routes/auth.py`
- 创建：`app/templates/base.html`
- 创建：`app/templates/auth/login.html`
- 创建：`app/templates/auth/register.html`
- 创建：`app/static/css/style.css`
- 创建：`tests/test_auth.py`
- 修改：`app/__init__.py`

**步骤 1：为用户注册编写失败测试**

创建 `tests/test_auth.py`：

```python
from app.models import User
from app import db

def test_register_new_user(client, app):
    """测试新用户注册"""
    response = client.post('/auth/register', data={
        'username': 'newuser',
        'email': 'new@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)

    assert response.status_code == 200

    with app.app_context():
        user = User.query.filter_by(username='newuser').first()
        assert user is not None
        assert user.email == 'new@example.com'

def test_register_duplicate_username(client, app):
    """测试重复用户名注册"""
    with app.app_context():
        user = User(username='existing', email='existing@test.com')
        user.set_password('pass')
        db.session.add(user)
        db.session.commit()

    response = client.post('/auth/register', data={
        'username': 'existing',
        'email': 'new@test.com',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)

    assert '用户名已存在' in response.data.decode('utf-8')
```

**步骤 2：运行测试确认失败**

运行：`pytest tests/test_auth.py::test_register_new_user -v`
预期：失败，返回 404 Not Found

**步骤 3：创建认证蓝图**

创建 `app/routes/__init__.py`（空文件）。

创建 `app/routes/auth.py`：

```python
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from app import db
from app.models import User
from datetime import datetime

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # 验证
        if not username or not email or not password:
            flash('所有字段都必须填写', 'error')
            return render_template('auth/register.html')

        if password != confirm_password:
            flash('两次密码不一致', 'error')
            return render_template('auth/register.html')

        if len(password) < 6:
            flash('密码至少 6 位', 'error')
            return render_template('auth/register.html')

        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'error')
            return render_template('auth/register.html')

        if User.query.filter_by(email=email).first():
            flash('邮箱已注册', 'error')
            return render_template('auth/register.html')

        # 创建用户
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('注册成功！请登录', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False) == 'on'

        user = User.query.filter_by(username=username).first()

        if user is None or not user.check_password(password):
            flash('用户名或密码错误', 'error')
            return render_template('auth/login.html')

        user.last_login = datetime.utcnow()
        db.session.commit()

        login_user(user, remember=remember)
        flash('登录成功！', 'success')

        next_page = request.args.get('next')
        return redirect(next_page or url_for('index'))

    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """用户登出"""
    logout_user()
    flash('已登出', 'info')
    return redirect(url_for('index'))
```

**步骤 4：在应用工厂中注册蓝图**

修改 `app/__init__.py`，在 `login_manager.init_app(app)` 后添加：

```python
    # 注册蓝图
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    # 主页路由
    @app.route('/')
    def index():
        return render_template('index.html')
```

**步骤 5：创建基础模板**

创建目录：
运行：`mkdir -p app/templates/auth app/static/css`

创建 `app/templates/base.html`：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}LearnThai - 泰语学习{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <nav class="navbar">
        <div class="container">
            <a href="{{ url_for('index') }}" class="logo">🇹🇭 LearnThai</a>
            <div class="nav-links">
                {% if current_user.is_authenticated %}
                    <span>你好, {{ current_user.username }}</span>
                    <a href="{{ url_for('auth.logout') }}">登出</a>
                {% else %}
                    <a href="{{ url_for('auth.login') }}">登录</a>
                    <a href="{{ url_for('auth.register') }}">注册</a>
                {% endif %}
            </div>
        </div>
    </nav>

    <main class="container">
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
    </main>

    <footer>
        <p>&copy; 2026 LearnThai - 中文用户泰语学习平台</p>
    </footer>

    <script>
        // 3秒后自动关闭提示消息
        setTimeout(() => {
            document.querySelectorAll('.alert').forEach(alert => {
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 300);
            });
        }, 3000);
    </script>
</body>
</html>
```

**步骤 6：创建注册模板**

创建 `app/templates/auth/register.html`：

```html
{% extends "base.html" %}

{% block title %}注册 - LearnThai{% endblock %}

{% block content %}
<div class="auth-container">
    <h1>注册新账户</h1>

    <form method="POST" class="auth-form">
        <div class="form-group">
            <label for="username">用户名</label>
            <input type="text" id="username" name="username" required minlength="3" maxlength="20">
        </div>

        <div class="form-group">
            <label for="email">邮箱</label>
            <input type="email" id="email" name="email" required>
        </div>

        <div class="form-group">
            <label for="password">密码</label>
            <input type="password" id="password" name="password" required minlength="6">
        </div>

        <div class="form-group">
            <label for="confirm_password">确认密码</label>
            <input type="password" id="confirm_password" name="confirm_password" required minlength="6">
        </div>

        <button type="submit" class="btn btn-primary">注册</button>
    </form>

    <p class="auth-link">已有账户？ <a href="{{ url_for('auth.login') }}">登录</a></p>
</div>
{% endblock %}
```

**步骤 7：创建登录模板**

创建 `app/templates/auth/login.html`：

```html
{% extends "base.html" %}

{% block title %}登录 - LearnThai{% endblock %}

{% block content %}
<div class="auth-container">
    <h1>登录</h1>

    <form method="POST" class="auth-form">
        <div class="form-group">
            <label for="username">用户名</label>
            <input type="text" id="username" name="username" required>
        </div>

        <div class="form-group">
            <label for="password">密码</label>
            <input type="password" id="password" name="password" required>
        </div>

        <div class="form-group">
            <label class="checkbox">
                <input type="checkbox" name="remember">
                记住我（30天）
            </label>
        </div>

        <button type="submit" class="btn btn-primary">登录</button>
    </form>

    <p class="auth-link">还没账户？ <a href="{{ url_for('auth.register') }}">注册</a></p>
</div>
{% endblock %}
```

**步骤 8：创建首页模板**

创建 `app/templates/index.html`：

```html
{% extends "base.html" %}

{% block content %}
<div class="hero">
    <h1>欢迎来到 LearnThai</h1>
    <p>中文用户的泰语词汇学习平台</p>

    {% if current_user.is_authenticated %}
        <a href="#" class="btn btn-primary btn-large">开始学习</a>
    {% else %}
        <a href="{{ url_for('auth.register') }}" class="btn btn-primary btn-large">开始使用</a>
    {% endif %}
</div>

<div class="features">
    <div class="feature">
        <h3>🎯 科学记忆</h3>
        <p>间隔重复算法，优化学习效果</p>
    </div>

    <div class="feature">
        <h3>🎮 多种题型</h3>
        <p>闪卡、选择题、听力、拼写练习</p>
    </div>

    <div class="feature">
        <h3>📊 进度追踪</h3>
        <p>详细统计，掌握学习情况</p>
    </div>

    <div class="feature">
        <h3>🔊 标准发音</h3>
        <p>泰语音频，提升听说能力</p>
    </div>
</div>
{% endblock %}
```

**步骤 9：创建基础 CSS**

创建 `app/static/css/style.css`：

```css
/* 基础样式 */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #f5f5f5;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

/* 导航栏 */
.navbar {
    background-color: #2196F3;
    color: white;
    padding: 1rem 0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.navbar .container {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.logo {
    font-size: 1.5rem;
    font-weight: bold;
    color: white;
    text-decoration: none;
}

.nav-links {
    display: flex;
    gap: 1rem;
    align-items: center;
}

.nav-links a {
    color: white;
    text-decoration: none;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    transition: background-color 0.3s;
}

.nav-links a:hover {
    background-color: rgba(255,255,255,0.1);
}

/* 主内容 */
main {
    min-height: calc(100vh - 200px);
    padding: 2rem 0;
}

/* Flash 消息 */
.flash-messages {
    margin-bottom: 1rem;
}

.alert {
    padding: 1rem;
    border-radius: 4px;
    margin-bottom: 0.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    animation: slideIn 0.3s ease;
    transition: opacity 0.3s;
}

@keyframes slideIn {
    from {
        transform: translateY(-20px);
        opacity: 0;
    }
    to {
        transform: translateY(0);
        opacity: 1;
    }
}

.alert-success {
    background-color: #E8F5E9;
    color: #2E7D32;
    border-left: 4px solid #4CAF50;
}

.alert-error {
    background-color: #FFEBEE;
    color: #C62828;
    border-left: 4px solid #F44336;
}

.alert-warning {
    background-color: #FFF3E0;
    color: #E65100;
    border-left: 4px solid #FF9800;
}

.alert-info {
    background-color: #E3F2FD;
    color: #1565C0;
    border-left: 4px solid #2196F3;
}

.alert .close {
    background: none;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
    color: inherit;
    opacity: 0.7;
}

.alert .close:hover {
    opacity: 1;
}

/* 按钮 */
.btn {
    display: inline-block;
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: 4px;
    font-size: 1rem;
    cursor: pointer;
    text-decoration: none;
    transition: all 0.3s;
    text-align: center;
}

.btn-primary {
    background-color: #2196F3;
    color: white;
}

.btn-primary:hover {
    background-color: #1976D2;
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}

.btn-large {
    padding: 1rem 2rem;
    font-size: 1.2rem;
}

/* 认证表单 */
.auth-container {
    max-width: 400px;
    margin: 3rem auto;
    background: white;
    padding: 2rem;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.auth-container h1 {
    margin-bottom: 1.5rem;
    text-align: center;
    color: #2196F3;
}

.auth-form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.form-group {
    display: flex;
    flex-direction: column;
}

.form-group label {
    margin-bottom: 0.5rem;
    font-weight: 500;
}

.form-group input {
    padding: 0.75rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 1rem;
}

.form-group input:focus {
    outline: none;
    border-color: #2196F3;
    box-shadow: 0 0 0 3px rgba(33, 150, 243, 0.1);
}

.checkbox {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.checkbox input {
    width: auto;
}

.auth-link {
    text-align: center;
    margin-top: 1rem;
}

.auth-link a {
    color: #2196F3;
    text-decoration: none;
}

.auth-link a:hover {
    text-decoration: underline;
}

/* 首页 */
.hero {
    text-align: center;
    padding: 4rem 0;
    background: white;
    border-radius: 8px;
    margin-bottom: 2rem;
}

.hero h1 {
    font-size: 2.5rem;
    color: #2196F3;
    margin-bottom: 1rem;
}

.hero p {
    font-size: 1.2rem;
    color: #666;
    margin-bottom: 2rem;
}

.features {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 2rem;
}

.feature {
    background: white;
    padding: 2rem;
    border-radius: 8px;
    text-align: center;
    transition: transform 0.3s;
}

.feature:hover {
    transform: translateY(-5px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.feature h3 {
    margin-bottom: 0.5rem;
    color: #2196F3;
}

.feature p {
    color: #666;
}

/* 页脚 */
footer {
    background-color: #333;
    color: white;
    text-align: center;
    padding: 1.5rem 0;
    margin-top: 3rem;
}

/* 响应式 */
@media (max-width: 768px) {
    .navbar .container {
        flex-direction: column;
        gap: 1rem;
    }

    .hero h1 {
        font-size: 2rem;
    }

    .features {
        grid-template-columns: 1fr;
    }
}
```

**步骤 10：运行测试确认通过**

运行：`pytest tests/test_auth.py::test_register_new_user -v`
预期：通过

**步骤 11：运行所有认证测试**

运行：`pytest tests/test_auth.py -v`
预期：全部测试通过

**步骤 12：手动测试 - 启动服务器**

运行：`python run.py`
访问：http://localhost:5000
预期：看到带功能展示的首页

**步骤 13：手动测试 - 注册用户**

导航到注册页面，创建账户
预期：成功消息，重定向到登录页

**步骤 14：手动测试 - 登录**

使用创建的账户登录
预期：成功消息，导航栏显示"你好, username"

**步骤 15：停止服务器**

按：Ctrl+C
预期：服务器停止

**步骤 16：提交**

```bash
git add app/routes/ app/templates/ app/static/ tests/test_auth.py app/__init__.py
git commit -m "feat: 添加认证系统和用户界面

- 添加认证蓝图（注册/登录/登出路由）
- 创建基础模板（导航栏和 Flash 消息）
- 添加认证模板（登录、注册）
- 创建带功能展示的首页
- 添加响应式 CSS 样式
- 包含完整的认证测试

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## 任务 5：SRS 算法实现

**涉及文件：**
- 创建：`app/utils/__init__.py`
- 创建：`app/utils/srs.py`
- 创建：`tests/test_srs.py`

**步骤 1：为 SRS 算法编写失败测试**

创建 `tests/test_srs.py`：

```python
from app.utils.srs import calculate_next_review_minutes
from datetime import datetime, timedelta

def test_srs_failed_review():
    """答错后应该 10 分钟内复习"""
    interval = calculate_next_review_minutes(familiarity=2, review_count=5)
    assert interval == 10

def test_srs_first_success():
    """首次答对应该 1 天后复习"""
    interval = calculate_next_review_minutes(familiarity=3, review_count=0)
    assert interval == 1440  # 1 天 = 1440 分钟

def test_srs_progression():
    """复习间隔应该递增"""
    intervals = []
    for i in range(7):
        interval = calculate_next_review_minutes(familiarity=4, review_count=i)
        intervals.append(interval)

    # 确保间隔递增
    for i in range(len(intervals) - 1):
        assert intervals[i] <= intervals[i + 1]

def test_srs_max_interval():
    """最大间隔应该是 90 天"""
    interval = calculate_next_review_minutes(familiarity=5, review_count=10)
    assert interval == 129600  # 90 天 = 129600 分钟
```

**步骤 2：运行测试确认失败**

运行：`pytest tests/test_srs.py -v`
预期：失败，提示 "cannot import name 'calculate_next_review_minutes'"

**步骤 3：实现 SRS 算法**

创建 `app/utils/__init__.py`（空文件）。

创建 `app/utils/srs.py`：

```python
from datetime import datetime, timedelta

def calculate_next_review_minutes(familiarity, review_count):
    """
    计算下次复习的间隔时间（分钟）

    Args:
        familiarity: 熟悉度等级 (0-5)
        review_count: 已复习次数

    Returns:
        int: 下次复习间隔（分钟）
    """
    # 答错或不熟练（熟悉度 < 3）：重新学习
    if familiarity < 3:
        return 10  # 10 分钟

    # 答对的情况：根据复习次数递增间隔
    interval_map = {
        0: 10,        # 首次：10分钟
        1: 1440,      # 第1次：1天
        2: 4320,      # 第2次：3天
        3: 10080,     # 第3次：7天
        4: 21600,     # 第4次：15天
        5: 43200,     # 第5次：30天
        6: 86400,     # 第6次：60天
    }

    # 第7次及以后：90天
    if review_count >= 7:
        return 129600

    return interval_map.get(review_count, 10)

def calculate_next_review_date(familiarity, review_count, from_date=None):
    """
    计算下次复习的日期时间

    Args:
        familiarity: 熟悉度等级 (0-5)
        review_count: 已复习次数
        from_date: 起始日期（默认为当前时间）

    Returns:
        datetime: 下次复习时间
    """
    if from_date is None:
        from_date = datetime.utcnow()

    minutes = calculate_next_review_minutes(familiarity, review_count)
    return from_date + timedelta(minutes=minutes)

def update_familiarity(current_familiarity, is_correct):
    """
    根据答题结果更新熟悉度

    Args:
        current_familiarity: 当前熟悉度 (0-5)
        is_correct: 是否答对

    Returns:
        int: 新的熟悉度等级
    """
    if is_correct:
        # 答对：熟悉度 +1，最高 5
        return min(current_familiarity + 1, 5)
    else:
        # 答错：重置为 1
        return 1
```

**步骤 4：运行测试确认通过**

运行：`pytest tests/test_srs.py -v`
预期：全部 4 个测试通过

**步骤 5：添加集成测试**

在 `tests/test_srs.py` 中添加：

```python
from app.utils.srs import calculate_next_review_date, update_familiarity

def test_calculate_next_review_date():
    """测试计算下次复习日期"""
    base_date = datetime(2026, 1, 14, 10, 0, 0)

    # 10分钟后
    next_date = calculate_next_review_date(familiarity=2, review_count=0, from_date=base_date)
    assert next_date == base_date + timedelta(minutes=10)

    # 1天后
    next_date = calculate_next_review_date(familiarity=3, review_count=0, from_date=base_date)
    assert next_date == base_date + timedelta(days=1)

def test_update_familiarity_correct():
    """测试答对后熟悉度更新"""
    assert update_familiarity(0, True) == 1
    assert update_familiarity(3, True) == 4
    assert update_familiarity(5, True) == 5  # 最高 5

def test_update_familiarity_incorrect():
    """测试答错后熟悉度更新"""
    assert update_familiarity(3, False) == 1
    assert update_familiarity(5, False) == 1
    assert update_familiarity(0, False) == 1
```

**步骤 6：运行所有 SRS 测试**

运行：`pytest tests/test_srs.py -v`
预期：全部 7 个测试通过

**步骤 7：提交**

```bash
git add app/utils/ tests/test_srs.py
git commit -m "feat: 实现 SRS 算法和测试

- 添加基于 SM-2 的间隔重复算法
- 计算复习间隔（10分钟到90天）
- 根据答题正确性自动更新熟悉度
- 包含完整的测试覆盖

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## 任务 6：学习流程 - 闪卡模式

**涉及文件：**
- 创建：`app/routes/learning.py`
- 创建：`app/templates/learning/flashcard.html`
- 创建：`app/templates/learning/summary.html`
- 创建：`tests/test_learning.py`
- 修改：`app/__init__.py`
- 修改：`app/templates/index.html`

**步骤 1：为学习会话编写失败测试**

创建 `tests/test_learning.py`：

```python
from app.models import User, Vocabulary, UserVocabulary, QuizAttempt
from app import db
from datetime import datetime, timedelta

def test_start_learning_session(client, app):
    """测试开始学习会话"""
    # 创建用户和词汇
    with app.app_context():
        user = User(username='learner', email='learner@test.com')
        user.set_password('pass')
        db.session.add(user)

        vocab = Vocabulary(
            thai_word='สวัสดี',
            chinese_meaning='你好',
            category='日常用语',
            difficulty_level=1
        )
        db.session.add(vocab)
        db.session.commit()

    # 登录
    client.post('/auth/login', data={
        'username': 'learner',
        'password': 'pass'
    })

    # 开始学习
    response = client.get('/learning/start')
    assert response.status_code == 200
    assert '你好' in response.data.decode('utf-8')

def test_submit_flashcard_answer(client, app):
    """测试提交闪卡答案"""
    with app.app_context():
        user = User(username='student', email='student@test.com')
        user.set_password('pass')
        db.session.add(user)

        vocab = Vocabulary(
            thai_word='ขอบคุณ',
            chinese_meaning='谢谢',
            category='日常用语',
            difficulty_level=1
        )
        db.session.add(vocab)
        db.session.commit()

        vocab_id = vocab.id
        user_id = user.id

    # 登录
    client.post('/auth/login', data={
        'username': 'student',
        'password': 'pass'
    })

    # 提交答案
    response = client.post('/learning/submit', json={
        'vocabulary_id': vocab_id,
        'quiz_type': 'flashcard',
        'familiarity': 4,
        'time_taken': 5
    })

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True

    # 验证数据库更新
    with app.app_context():
        uv = UserVocabulary.query.filter_by(
            user_id=user_id,
            vocabulary_id=vocab_id
        ).first()
        assert uv is not None
        assert uv.familiarity_level == 4

        attempt = QuizAttempt.query.filter_by(
            user_id=user_id,
            vocabulary_id=vocab_id
        ).first()
        assert attempt is not None
        assert attempt.quiz_type == 'flashcard'
```

**步骤 2：运行测试确认失败**

运行：`pytest tests/test_learning.py::test_start_learning_session -v`
预期：失败，返回 404 Not Found

**步骤 3：实现学习蓝图**

创建 `app/routes/learning.py`：

```python
from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import Vocabulary, UserVocabulary, QuizAttempt
from app.utils.srs import calculate_next_review_date, update_familiarity
from datetime import datetime
from sqlalchemy import and_

learning_bp = Blueprint('learning', __name__, url_prefix='/learning')

@learning_bp.route('/start')
@login_required
def start():
    """开始学习会话"""
    # 获取待复习词汇（next_review_date <= 现在）
    due_vocabs = db.session.query(UserVocabulary, Vocabulary)\
        .join(Vocabulary)\
        .filter(
            and_(
                UserVocabulary.user_id == current_user.id,
                UserVocabulary.next_review_date <= datetime.utcnow()
            )
        )\
        .order_by(UserVocabulary.next_review_date.asc())\
        .limit(20)\
        .all()

    # 如果复习词汇不足 20 个，补充新词
    vocab_ids = [uv.vocabulary_id for uv, _ in due_vocabs]
    needed = 20 - len(due_vocabs)

    if needed > 0:
        # 获取用户未学过的词汇
        learned_ids = [uv.vocabulary_id for uv in
                      UserVocabulary.query.filter_by(user_id=current_user.id).all()]

        new_vocabs = Vocabulary.query\
            .filter(
                and_(
                    Vocabulary.is_active == True,
                    ~Vocabulary.id.in_(learned_ids) if learned_ids else True
                )
            )\
            .order_by(Vocabulary.difficulty_level.asc(), Vocabulary.id.asc())\
            .limit(needed)\
            .all()

        # 为新词创建学习记录
        for vocab in new_vocabs:
            uv = UserVocabulary(
                user_id=current_user.id,
                vocabulary_id=vocab.id,
                familiarity_level=0,
                next_review_date=datetime.utcnow(),
                review_count=0
            )
            db.session.add(uv)

        db.session.commit()

        # 合并列表
        new_entries = [(None, vocab) for vocab in new_vocabs]
        due_vocabs.extend(new_entries)

    if not due_vocabs:
        return render_template('learning/no_words.html')

    # 存储会话信息
    session['learning_session'] = {
        'vocab_ids': [v.id for _, v in due_vocabs],
        'current_index': 0,
        'correct_count': 0,
        'total_count': len(due_vocabs),
        'start_time': datetime.utcnow().isoformat()
    }

    # 显示第一个词
    _, first_vocab = due_vocabs[0]
    return render_template('learning/flashcard.html', vocabulary=first_vocab, session_info=session['learning_session'])

@learning_bp.route('/submit', methods=['POST'])
@login_required
def submit():
    """提交答题结果"""
    data = request.get_json()

    vocabulary_id = data.get('vocabulary_id')
    quiz_type = data.get('quiz_type', 'flashcard')
    familiarity = data.get('familiarity', 3)
    time_taken = data.get('time_taken', 0)

    if not vocabulary_id:
        return jsonify({'success': False, 'error': '缺少词汇 ID'}), 400

    # 查找或创建 UserVocabulary 记录
    uv = UserVocabulary.query.filter_by(
        user_id=current_user.id,
        vocabulary_id=vocabulary_id
    ).first()

    if not uv:
        # 新词汇
        uv = UserVocabulary(
            user_id=current_user.id,
            vocabulary_id=vocabulary_id,
            familiarity_level=0,
            review_count=0,
            correct_count=0
        )
        db.session.add(uv)

    # 更新熟悉度和复习计数
    uv.familiarity_level = familiarity
    uv.review_count += 1
    if familiarity >= 3:
        uv.correct_count += 1

    uv.last_reviewed = datetime.utcnow()
    uv.next_review_date = calculate_next_review_date(familiarity, uv.review_count)

    # 记录答题
    attempt = QuizAttempt(
        user_id=current_user.id,
        vocabulary_id=vocabulary_id,
        quiz_type=quiz_type,
        is_correct=(familiarity >= 3),
        time_taken=time_taken
    )
    db.session.add(attempt)

    db.session.commit()

    # 更新会话信息
    if 'learning_session' in session:
        session['learning_session']['current_index'] += 1
        if familiarity >= 3:
            session['learning_session']['correct_count'] += 1
        session.modified = True

        # 检查是否完成
        if session['learning_session']['current_index'] >= session['learning_session']['total_count']:
            return jsonify({
                'success': True,
                'completed': True,
                'summary': session['learning_session']
            })

        # 获取下一个词
        next_index = session['learning_session']['current_index']
        next_vocab_id = session['learning_session']['vocab_ids'][next_index]
        next_vocab = Vocabulary.query.get(next_vocab_id)

        return jsonify({
            'success': True,
            'completed': False,
            'next_vocabulary': {
                'id': next_vocab.id,
                'thai_word': next_vocab.thai_word,
                'chinese_meaning': next_vocab.chinese_meaning,
                'pronunciation': next_vocab.pronunciation,
                'audio_file': next_vocab.audio_file
            }
        })

    return jsonify({'success': True, 'completed': False})

@learning_bp.route('/summary')
@login_required
def summary():
    """学习总结"""
    if 'learning_session' not in session:
        return redirect(url_for('learning.start'))

    summary_data = session.pop('learning_session')
    return render_template('learning/summary.html', summary=summary_data)
```

**步骤 4：注册学习蓝图**

修改 `app/__init__.py`，在认证蓝图注册后添加：

```python
    from app.routes.learning import learning_bp
    app.register_blueprint(learning_bp)
```

**步骤 5：创建闪卡模板**

创建 `app/templates/learning/flashcard.html`：

```html
{% extends "base.html" %}

{% block title %}学习中 - LearnThai{% endblock %}

{% block content %}
<div class="learning-container">
    <div class="progress-bar">
        <div class="progress-fill" id="progress" style="width: {{ (session_info.current_index / session_info.total_count * 100) }}%"></div>
    </div>

    <div class="progress-text">
        <span id="current">{{ session_info.current_index + 1 }}</span> / <span id="total">{{ session_info.total_count }}</span>
    </div>

    <div class="flashcard" id="flashcard">
        <div class="card-front">
            <div class="thai-word">{{ vocabulary.thai_word }}</div>
            {% if vocabulary.pronunciation %}
                <div class="pronunciation">{{ vocabulary.pronunciation }}</div>
            {% endif %}

            <button class="btn btn-secondary" onclick="showAnswer()">显示答案</button>
        </div>

        <div class="card-back" style="display: none;">
            <div class="thai-word">{{ vocabulary.thai_word }}</div>
            <div class="chinese-meaning">{{ vocabulary.chinese_meaning }}</div>

            {% if vocabulary.example_sentence_thai %}
                <div class="example">
                    <p class="example-thai">{{ vocabulary.example_sentence_thai }}</p>
                    <p class="example-chinese">{{ vocabulary.example_sentence_chinese }}</p>
                </div>
            {% endif %}

            <div class="familiarity-buttons">
                <p>你对这个词的熟悉程度？</p>
                <button class="btn-familiarity" data-level="1" onclick="submitAnswer(1)">不会</button>
                <button class="btn-familiarity" data-level="2" onclick="submitAnswer(2)">模糊</button>
                <button class="btn-familiarity" data-level="3" onclick="submitAnswer(3)">记得</button>
                <button class="btn-familiarity" data-level="4" onclick="submitAnswer(4)">熟悉</button>
                <button class="btn-familiarity" data-level="5" onclick="submitAnswer(5)">精通</button>
            </div>
        </div>
    </div>
</div>

<script>
let startTime = Date.now();
let currentVocabId = {{ vocabulary.id }};

function showAnswer() {
    document.querySelector('.card-front').style.display = 'none';
    document.querySelector('.card-back').style.display = 'block';
}

async function submitAnswer(familiarity) {
    const timeSpent = Math.floor((Date.now() - startTime) / 1000);

    const response = await fetch('/learning/submit', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            vocabulary_id: currentVocabId,
            quiz_type: 'flashcard',
            familiarity: familiarity,
            time_taken: timeSpent
        })
    });

    const data = await response.json();

    if (data.completed) {
        window.location.href = '/learning/summary';
    } else if (data.next_vocabulary) {
        loadNextWord(data.next_vocabulary);
    }
}

function loadNextWord(vocab) {
    currentVocabId = vocab.id;
    startTime = Date.now();

    // 更新进度
    const current = parseInt(document.getElementById('current').textContent);
    document.getElementById('current').textContent = current + 1;

    const total = parseInt(document.getElementById('total').textContent);
    const progress = (current / total) * 100;
    document.getElementById('progress').style.width = progress + '%';

    // 更新卡片
    document.querySelector('.card-front .thai-word').textContent = vocab.thai_word;
    if (vocab.pronunciation) {
        document.querySelector('.pronunciation').textContent = vocab.pronunciation;
    }

    document.querySelector('.card-back .thai-word').textContent = vocab.thai_word;
    document.querySelector('.chinese-meaning').textContent = vocab.chinese_meaning;

    // 重置显示
    document.querySelector('.card-front').style.display = 'block';
    document.querySelector('.card-back').style.display = 'none';
}
</script>

<style>
.learning-container {
    max-width: 600px;
    margin: 0 auto;
}

.progress-bar {
    width: 100%;
    height: 8px;
    background-color: #e0e0e0;
    border-radius: 4px;
    overflow: hidden;
    margin-bottom: 0.5rem;
}

.progress-fill {
    height: 100%;
    background-color: #4CAF50;
    transition: width 0.3s ease;
}

.progress-text {
    text-align: center;
    margin-bottom: 2rem;
    font-size: 1.2rem;
    color: #666;
}

.flashcard {
    background: white;
    border-radius: 12px;
    padding: 3rem;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    min-height: 400px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.thai-word {
    font-size: 3rem;
    text-align: center;
    margin-bottom: 1rem;
    color: #2196F3;
}

.pronunciation {
    text-align: center;
    font-size: 1.2rem;
    color: #666;
    margin-bottom: 2rem;
}

.chinese-meaning {
    font-size: 2rem;
    text-align: center;
    color: #333;
    margin-bottom: 2rem;
}

.example {
    background: #f5f5f5;
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 2rem;
}

.example-thai {
    font-size: 1.1rem;
    margin-bottom: 0.5rem;
}

.example-chinese {
    color: #666;
}

.card-front, .card-back {
    text-align: center;
}

.familiarity-buttons {
    margin-top: 2rem;
}

.familiarity-buttons p {
    text-align: center;
    margin-bottom: 1rem;
    color: #666;
}

.btn-familiarity {
    display: inline-block;
    padding: 0.75rem 1.5rem;
    margin: 0.25rem;
    border: 2px solid #ddd;
    background: white;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.3s;
}

.btn-familiarity:hover {
    border-color: #2196F3;
    background: #E3F2FD;
    transform: translateY(-2px);
}

.btn-secondary {
    background-color: #757575;
    color: white;
}

.btn-secondary:hover {
    background-color: #616161;
}
</style>
{% endblock %}
```

**步骤 6：创建总结模板**

创建 `app/templates/learning/summary.html`：

```html
{% extends "base.html" %}

{% block title %}学习总结 - LearnThai{% endblock %}

{% block content %}
<div class="summary-container">
    <h1>🎉 学习完成！</h1>

    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-value">{{ summary.total_count }}</div>
            <div class="stat-label">总题数</div>
        </div>

        <div class="stat-card">
            <div class="stat-value">{{ summary.correct_count }}</div>
            <div class="stat-label">熟悉词汇</div>
        </div>

        <div class="stat-card">
            <div class="stat-value">{{ ((summary.correct_count / summary.total_count * 100) | int) }}%</div>
            <div class="stat-label">掌握率</div>
        </div>
    </div>

    <div class="actions">
        <a href="{{ url_for('learning.start') }}" class="btn btn-primary">继续学习</a>
        <a href="{{ url_for('index') }}" class="btn btn-secondary">返回首页</a>
    </div>
</div>

<style>
.summary-container {
    max-width: 800px;
    margin: 0 auto;
    text-align: center;
    padding: 3rem;
    background: white;
    border-radius: 12px;
}

.summary-container h1 {
    color: #4CAF50;
    margin-bottom: 2rem;
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 2rem;
    margin-bottom: 3rem;
}

.stat-card {
    padding: 2rem;
    background: #f5f5f5;
    border-radius: 8px;
}

.stat-value {
    font-size: 3rem;
    font-weight: bold;
    color: #2196F3;
    margin-bottom: 0.5rem;
}

.stat-label {
    color: #666;
    font-size: 1.1rem;
}

.actions {
    display: flex;
    gap: 1rem;
    justify-content: center;
}

.btn-secondary {
    background-color: #757575;
    color: white;
}

.btn-secondary:hover {
    background-color: #616161;
}
</style>
{% endblock %}
```

**步骤 7：更新首页链接**

修改 `app/templates/index.html`，更改按钮：

```html
{% if current_user.is_authenticated %}
    <a href="{{ url_for('learning.start') }}" class="btn btn-primary btn-large">开始学习</a>
{% else %}
    <a href="{{ url_for('auth.register') }}" class="btn btn-primary btn-large">开始使用</a>
{% endif %}
```

**步骤 8：运行测试确认通过**

运行：`pytest tests/test_learning.py -v`
预期：全部测试通过

**步骤 9：手动测试 - 完成学习流程**

运行：`python run.py`
1. 以用户身份登录
2. 点击"开始学习"
3. 查看闪卡
4. 点击"显示答案"
5. 评分熟悉度
6. 完成会话
7. 查看总结
预期：完整流程运行正常

**步骤 10：提交**

```bash
git add app/routes/learning.py app/templates/learning/ tests/test_learning.py app/__init__.py app/templates/index.html
git commit -m "feat: 实现闪卡学习模式

- 添加学习蓝图和会话管理
- 创建带进度跟踪的闪卡界面
- 实现答题提交和 SRS 更新
- 添加带统计数据的学习总结
- 包含完整的集成测试

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## 后续步骤（不在此计划范围内）

以下功能已在设计文档中规划，但不包含在此实现计划中：

1. **选择题模式**
2. **听力题模式**
3. **拼写题模式**
4. **统计仪表板**
5. **管理员词汇管理面板**
6. **高级 SRS 功能**

这些功能可以在后续迭代中按照相同的 TDD 方法实现。

---

## 测试检查清单

在完成此计划之前，请验证：

- [ ] 所有单元测试通过（`pytest tests/test_models.py -v`）
- [ ] 所有 SRS 测试通过（`pytest tests/test_srs.py -v`）
- [ ] 所有认证测试通过（`pytest tests/test_auth.py -v`）
- [ ] 所有学习测试通过（`pytest tests/test_learning.py -v`）
- [ ] 手动注册流程正常
- [ ] 手动登录/登出正常
- [ ] 手动学习会话成功完成
- [ ] 数据库正确持久化用户进度
- [ ] SRS 间隔计算正确

运行所有测试：`pytest -v`

预期：所有测试通过

---

## 部署说明

**本地开发：**
1. `python init_db.py` - 初始化数据库
2. `python import_vocab.py data/basic_vocab.csv` - 加载词汇
3. `python create_admin.py` - 创建管理员账户
4. `python run.py` - 启动服务器

**环境变量：**
- `FLASK_ENV=development`（默认）
- `SECRET_KEY` - 生产环境需更改

**数据库文件：**
- 开发环境：`learnthai_dev.db`
- 位于项目根目录
- 生产环境需定期备份
