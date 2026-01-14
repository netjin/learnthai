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

def test_learning_requires_login(client, app):
    """测试学习需要登录"""
    response = client.get('/learning/start')
    # Should redirect to login
    assert response.status_code == 302
    assert '/auth/login' in response.location

def test_submit_updates_existing_user_vocabulary(client, app):
    """测试提交更新已存在的用户词汇记录"""
    with app.app_context():
        user = User(username='existing', email='existing@test.com')
        user.set_password('pass')
        db.session.add(user)

        vocab = Vocabulary(
            thai_word='กิน',
            chinese_meaning='吃',
            category='动词',
            difficulty_level=1
        )
        db.session.add(vocab)
        db.session.commit()

        # 创建已存在的 UserVocabulary 记录
        uv = UserVocabulary(
            user_id=user.id,
            vocabulary_id=vocab.id,
            familiarity_level=2,
            next_review_date=datetime.utcnow(),
            review_count=1,
            correct_count=1
        )
        db.session.add(uv)
        db.session.commit()

        vocab_id = vocab.id
        user_id = user.id

    # 登录
    client.post('/auth/login', data={
        'username': 'existing',
        'password': 'pass'
    })

    # 提交高熟悉度答案
    response = client.post('/learning/submit', json={
        'vocabulary_id': vocab_id,
        'quiz_type': 'flashcard',
        'familiarity': 5,
        'time_taken': 3
    })

    assert response.status_code == 200

    # 验证更新
    with app.app_context():
        uv = UserVocabulary.query.filter_by(
            user_id=user_id,
            vocabulary_id=vocab_id
        ).first()
        assert uv.familiarity_level == 5
        assert uv.review_count == 2  # 应增加

def test_learning_summary(client, app):
    """测试学习总结页面"""
    with app.app_context():
        user = User(username='summary_user', email='summary@test.com')
        user.set_password('pass')
        db.session.add(user)
        db.session.commit()

    # 登录
    client.post('/auth/login', data={
        'username': 'summary_user',
        'password': 'pass'
    })

    # 访问总结页面
    response = client.get('/learning/summary')
    assert response.status_code == 200

def test_due_vocabulary_included(client, app):
    """测试到期词汇被包含在学习会话中"""
    with app.app_context():
        user = User(username='due_user', email='due@test.com')
        user.set_password('pass')
        db.session.add(user)

        vocab = Vocabulary(
            thai_word='น้ำ',
            chinese_meaning='水',
            category='名词',
            difficulty_level=1
        )
        db.session.add(vocab)
        db.session.commit()

        # 创建已到期的 UserVocabulary
        uv = UserVocabulary(
            user_id=user.id,
            vocabulary_id=vocab.id,
            familiarity_level=3,
            next_review_date=datetime.utcnow() - timedelta(hours=1),  # 已到期
            review_count=2
        )
        db.session.add(uv)
        db.session.commit()

    # 登录
    client.post('/auth/login', data={
        'username': 'due_user',
        'password': 'pass'
    })

    # 开始学习
    response = client.get('/learning/start')
    assert response.status_code == 200
    assert '水' in response.data.decode('utf-8')
