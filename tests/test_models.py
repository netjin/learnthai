from app.models import User, Vocabulary, UserVocabulary, QuizAttempt
from app import db
from datetime import datetime, timedelta

def test_user_password_hashing(app):
    """测试用户密码加密"""
    with app.app_context():
        user = User(username='test', email='test@test.com')
        user.set_password('secret')

        assert user.password_hash is not None
        assert user.password_hash != 'secret'
        assert user.check_password('secret')
        assert not user.check_password('wrong')


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
