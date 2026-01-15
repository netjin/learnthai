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
