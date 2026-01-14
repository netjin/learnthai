from app import create_app, db
from app.models import User, Vocabulary, UserVocabulary, QuizAttempt

def init_database():
    """初始化数据库"""
    app = create_app()
    with app.app_context():
        db.create_all()
        print("✓ 数据库表创建成功！")

if __name__ == '__main__':
    init_database()
