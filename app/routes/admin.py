from flask import Blueprint, render_template, request, redirect, url_for, flash
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
