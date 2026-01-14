from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Vocabulary, UserVocabulary, QuizAttempt
from app.utils.srs import calculate_next_review_date
from datetime import datetime

learning_bp = Blueprint('learning', __name__, url_prefix='/learning')

MAX_SESSION_WORDS = 20

@learning_bp.route('/start')
@login_required
def start():
    """开始学习会话"""
    # 获取到期需要复习的词汇
    due_vocab = db.session.query(Vocabulary, UserVocabulary).join(
        UserVocabulary,
        UserVocabulary.vocabulary_id == Vocabulary.id
    ).filter(
        UserVocabulary.user_id == current_user.id,
        UserVocabulary.next_review_date <= datetime.utcnow()
    ).order_by(
        UserVocabulary.next_review_date.asc()
    ).limit(MAX_SESSION_WORDS).all()

    session_vocab = []
    for vocab, uv in due_vocab:
        session_vocab.append({
            'id': vocab.id,
            'thai_word': vocab.thai_word,
            'chinese_meaning': vocab.chinese_meaning,
            'pronunciation': vocab.pronunciation,
            'category': vocab.category,
            'is_new': False,
            'familiarity_level': uv.familiarity_level
        })

    # 如果不足 MAX_SESSION_WORDS，添加新词汇
    if len(session_vocab) < MAX_SESSION_WORDS:
        # 获取用户已学过的词汇 ID
        learned_ids = db.session.query(UserVocabulary.vocabulary_id).filter(
            UserVocabulary.user_id == current_user.id
        ).subquery()

        # 获取新词汇（用户未学过的）
        new_vocab = Vocabulary.query.filter(
            Vocabulary.is_active == True,
            ~Vocabulary.id.in_(learned_ids)
        ).order_by(
            Vocabulary.difficulty_level.asc(),
            Vocabulary.id.asc()
        ).limit(MAX_SESSION_WORDS - len(session_vocab)).all()

        for vocab in new_vocab:
            # 为新词汇创建 UserVocabulary 记录
            uv = UserVocabulary(
                user_id=current_user.id,
                vocabulary_id=vocab.id,
                familiarity_level=0,
                next_review_date=datetime.utcnow(),
                review_count=0,
                correct_count=0
            )
            db.session.add(uv)

            session_vocab.append({
                'id': vocab.id,
                'thai_word': vocab.thai_word,
                'chinese_meaning': vocab.chinese_meaning,
                'pronunciation': vocab.pronunciation,
                'category': vocab.category,
                'is_new': True,
                'familiarity_level': 0
            })

        db.session.commit()

    # 如果没有可学习的词汇
    if not session_vocab:
        flash('恭喜！暂时没有需要学习的词汇', 'info')
        return redirect(url_for('learning.summary'))

    # 存储会话信息
    session['learning_vocab'] = session_vocab
    session['learning_index'] = 0
    session['learning_stats'] = {
        'total': len(session_vocab),
        'completed': 0,
        'familiar': 0,  # 熟悉度 >= 3
        'start_time': datetime.utcnow().isoformat()
    }

    # 获取当前词汇
    current_vocab = session_vocab[0]

    return render_template('learning/flashcard.html',
        vocab=current_vocab,
        current=1,
        total=len(session_vocab)
    )


@learning_bp.route('/submit', methods=['POST'])
@login_required
def submit():
    """提交答案"""
    data = request.get_json()

    vocab_id = data.get('vocabulary_id')
    quiz_type = data.get('quiz_type', 'flashcard')
    familiarity = data.get('familiarity', 0)
    time_taken = data.get('time_taken', 0)

    if not vocab_id:
        return jsonify({'success': False, 'error': '缺少词汇 ID'}), 400

    # 获取或创建 UserVocabulary 记录
    uv = UserVocabulary.query.filter_by(
        user_id=current_user.id,
        vocabulary_id=vocab_id
    ).first()

    if not uv:
        # 创建新记录
        uv = UserVocabulary(
            user_id=current_user.id,
            vocabulary_id=vocab_id,
            familiarity_level=familiarity,
            next_review_date=calculate_next_review_date(familiarity, 0),
            review_count=1,
            correct_count=1 if familiarity >= 3 else 0,
            last_reviewed=datetime.utcnow()
        )
        db.session.add(uv)
    else:
        # 更新现有记录
        uv.familiarity_level = familiarity
        uv.review_count += 1
        if familiarity >= 3:
            uv.correct_count += 1
        uv.next_review_date = calculate_next_review_date(familiarity, uv.review_count)
        uv.last_reviewed = datetime.utcnow()

    # 创建测验尝试记录
    attempt = QuizAttempt(
        user_id=current_user.id,
        vocabulary_id=vocab_id,
        quiz_type=quiz_type,
        is_correct=familiarity >= 3,
        time_taken=time_taken
    )
    db.session.add(attempt)
    db.session.commit()

    # 更新会话统计
    stats = session.get('learning_stats', {})
    stats['completed'] = stats.get('completed', 0) + 1
    if familiarity >= 3:
        stats['familiar'] = stats.get('familiar', 0) + 1
    session['learning_stats'] = stats

    # 获取下一个词汇
    vocab_list = session.get('learning_vocab', [])
    current_index = session.get('learning_index', 0)
    next_index = current_index + 1

    if next_index >= len(vocab_list):
        # 学习完成
        return jsonify({
            'success': True,
            'completed': True,
            'redirect': url_for('learning.summary')
        })

    # 更新索引
    session['learning_index'] = next_index
    next_vocab = vocab_list[next_index]

    return jsonify({
        'success': True,
        'completed': False,
        'next_vocab': next_vocab,
        'current': next_index + 1,
        'total': len(vocab_list)
    })


@learning_bp.route('/summary')
@login_required
def summary():
    """学习总结"""
    stats = session.get('learning_stats', {})

    total = stats.get('total', 0)
    completed = stats.get('completed', 0)
    familiar = stats.get('familiar', 0)

    # 计算掌握率
    mastery_percent = round(familiar / completed * 100) if completed > 0 else 0

    # 获取用户总体统计
    total_learned = UserVocabulary.query.filter_by(user_id=current_user.id).count()
    total_mastered = UserVocabulary.query.filter(
        UserVocabulary.user_id == current_user.id,
        UserVocabulary.familiarity_level >= 4
    ).count()

    return render_template('learning/summary.html',
        session_total=total,
        session_completed=completed,
        session_familiar=familiar,
        mastery_percent=mastery_percent,
        total_learned=total_learned,
        total_mastered=total_mastered
    )
