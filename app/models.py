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


class ThaiAlphabet(db.Model):
    """泰语字母表（辅音和元音）"""
    __tablename__ = 'thai_alphabets'

    id = db.Column(db.Integer, primary_key=True)
    character = db.Column(db.String(10), nullable=False)  # 字母符号
    name_thai = db.Column(db.String(50))                   # 泰语名称（如 ก ไก่）
    name_chinese = db.Column(db.String(50))                # 中文名称（如 鸡）
    pronunciation = db.Column(db.String(50))               # 罗马音（如 ko kai）
    sound = db.Column(db.String(20))                       # 音值（如 k）
    alphabet_type = db.Column(db.String(20), nullable=False)  # consonant/vowel
    consonant_class = db.Column(db.String(10))             # high/mid/low（仅辅音）
    vowel_type = db.Column(db.String(20))                  # short/long（仅元音）
    example_word = db.Column(db.String(50))                # 示例词
    example_meaning = db.Column(db.String(50))             # 示例词中文
    audio_file = db.Column(db.String(200))                 # 音频路径
    sort_order = db.Column(db.Integer, default=0)          # 排序
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    user_progress = db.relationship('UserAlphabet', backref='alphabet', lazy='dynamic')

    def __repr__(self):
        return f'<ThaiAlphabet {self.character}>'


class UserAlphabet(db.Model):
    """用户字母学习进度"""
    __tablename__ = 'user_alphabets'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    alphabet_id = db.Column(db.Integer, db.ForeignKey('thai_alphabets.id'), nullable=False)
    familiarity_level = db.Column(db.Integer, default=0)  # 0-5
    next_review_date = db.Column(db.DateTime)
    review_count = db.Column(db.Integer, default=0)
    correct_count = db.Column(db.Integer, default=0)
    last_reviewed = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'alphabet_id', name='unique_user_alphabet'),
    )

    def __repr__(self):
        return f'<UserAlphabet user={self.user_id} alphabet={self.alphabet_id}>'


class ConversationScene(db.Model):
    """生活场景分类"""
    __tablename__ = 'conversation_scenes'

    id = db.Column(db.Integer, primary_key=True)
    name_chinese = db.Column(db.String(50), nullable=False)  # 中文名称（如"餐厅点餐"）
    name_thai = db.Column(db.String(50))                      # 泰语名称
    icon = db.Column(db.String(50))                           # 图标名称
    description = db.Column(db.Text)                          # 场景描述
    difficulty_level = db.Column(db.Integer, default=1)       # 难度等级 1-5
    sort_order = db.Column(db.Integer, default=0)             # 排序
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    conversations = db.relationship('Conversation', backref='scene', lazy='dynamic')

    def __repr__(self):
        return f'<ConversationScene {self.name_chinese}>'


class Conversation(db.Model):
    """具体对话"""
    __tablename__ = 'conversations'

    id = db.Column(db.Integer, primary_key=True)
    scene_id = db.Column(db.Integer, db.ForeignKey('conversation_scenes.id'), nullable=False)
    title_chinese = db.Column(db.String(100), nullable=False)  # 对话标题（如"预订餐位"）
    title_thai = db.Column(db.String(100))
    situation = db.Column(db.Text)                              # 情境说明
    difficulty_level = db.Column(db.Integer, default=1)
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    lines = db.relationship('ConversationLine', backref='conversation', lazy='dynamic',
                           order_by='ConversationLine.line_order')
    user_progress = db.relationship('UserConversation', backref='conversation', lazy='dynamic')

    def __repr__(self):
        return f'<Conversation {self.title_chinese}>'


class ConversationLine(db.Model):
    """对话的每一句"""
    __tablename__ = 'conversation_lines'

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    line_order = db.Column(db.Integer, nullable=False)         # 句子顺序
    speaker_role = db.Column(db.String(50), nullable=False)    # 角色（如"顾客"、"服务员"）
    speaker_role_thai = db.Column(db.String(50))
    text_thai = db.Column(db.Text, nullable=False)             # 泰语文本
    text_chinese = db.Column(db.Text, nullable=False)          # 中文翻译
    pronunciation = db.Column(db.Text)                         # 发音标注
    audio_file = db.Column(db.String(200))                     # 音频文件路径
    key_words = db.Column(db.Text)                             # 关键词（JSON格式）
    notes = db.Column(db.Text)                                 # 注释说明

    __table_args__ = (
        db.Index('idx_conversation_order', 'conversation_id', 'line_order'),
    )

    def __repr__(self):
        return f'<ConversationLine {self.conversation_id}:{self.line_order}>'


class UserConversation(db.Model):
    """用户对话学习进度"""
    __tablename__ = 'user_conversations'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    familiarity_level = db.Column(db.Integer, default=0)       # 熟练度 0-5
    completed_modes = db.Column(db.String(100))                # 已完成的模式（JSON）
    practice_count = db.Column(db.Integer, default=0)          # 练习次数
    last_practiced = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'conversation_id', name='unique_user_conversation'),
    )

    def __repr__(self):
        return f'<UserConversation user={self.user_id} conversation={self.conversation_id}>'

