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
    is_active = db.Column(db.Boolean, default=True)
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
