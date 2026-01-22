from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Vocabulary, UserVocabulary, QuizAttempt, ThaiAlphabet, UserAlphabet
from app.utils.srs import calculate_next_review_date
from datetime import datetime
import random

learning_bp = Blueprint('learning', __name__, url_prefix='/learning')

MAX_SESSION_WORDS = 20


@learning_bp.route('/select')
@login_required
def select():
    """学习类型选择页面（字母学习 vs 词汇学习）"""
    # 字母统计
    consonant_count = ThaiAlphabet.query.filter_by(alphabet_type='consonant', is_active=True).count()
    vowel_count = ThaiAlphabet.query.filter_by(alphabet_type='vowel', is_active=True).count()
    alphabet_mastered = UserAlphabet.query.filter(
        UserAlphabet.user_id == current_user.id,
        UserAlphabet.familiarity_level >= 4
    ).count()

    # 词汇统计
    total_vocab = Vocabulary.query.filter_by(is_active=True).count()
    due_vocab = UserVocabulary.query.filter(
        UserVocabulary.user_id == current_user.id,
        UserVocabulary.next_review_date <= datetime.utcnow()
    ).count()
    vocab_mastered = UserVocabulary.query.filter(
        UserVocabulary.user_id == current_user.id,
        UserVocabulary.familiarity_level >= 4
    ).count()

    return render_template('learning/select.html',
        alphabet_stats={
            'consonants': consonant_count,
            'vowels': vowel_count,
            'mastered': alphabet_mastered
        },
        vocab_stats={
            'total': total_vocab,
            'due': due_vocab,
            'mastered': vocab_mastered
        }
    )


def generate_true_false(correct_vocab, all_vocab):
    """生成判断题（50%概率显示正确答案，50%显示错误答案）"""
    is_correct_pairing = random.choice([True, False])

    if is_correct_pairing:
        shown_meaning = correct_vocab['chinese_meaning']
    else:
        # 选择一个错误的意思
        other_meanings = [v['chinese_meaning'] for v in all_vocab
                         if v['chinese_meaning'] != correct_vocab['chinese_meaning']]
        if other_meanings:
            shown_meaning = random.choice(other_meanings)
        else:
            # 如果没有其他词汇，从数据库获取
            wrong_vocab = Vocabulary.query.filter(
                Vocabulary.is_active == True,
                Vocabulary.chinese_meaning != correct_vocab['chinese_meaning']
            ).order_by(db.func.random()).first()
            shown_meaning = wrong_vocab.chinese_meaning if wrong_vocab else correct_vocab['chinese_meaning']
            is_correct_pairing = True  # 如果找不到错误答案，就显示正确的

    return shown_meaning, is_correct_pairing


def generate_options(correct_vocab, all_vocab):
    """生成选择题选项（1个正确 + 3个干扰项）"""
    correct_answer = correct_vocab['chinese_meaning']
    options = [{'text': correct_answer, 'is_correct': True}]

    # 收集干扰项候选
    same_category = [v for v in all_vocab
                     if v.get('category') == correct_vocab.get('category')
                     and v['chinese_meaning'] != correct_answer]

    other_category = [v for v in all_vocab
                      if v.get('category') != correct_vocab.get('category')
                      and v['chinese_meaning'] != correct_answer]

    # 优先从同分类中选择干扰项
    distractors = []
    if len(same_category) >= 3:
        distractors = random.sample(same_category, 3)
    else:
        distractors = same_category.copy()
        needed = 3 - len(distractors)
        if other_category and needed > 0:
            distractors += random.sample(other_category, min(needed, len(other_category)))

    # 如果还不够，从数据库补充
    if len(distractors) < 3:
        needed = 3 - len(distractors)
        existing_meanings = [correct_answer] + [d['chinese_meaning'] for d in distractors]
        extra = Vocabulary.query.filter(
            Vocabulary.is_active == True,
            ~Vocabulary.chinese_meaning.in_(existing_meanings)
        ).limit(needed).all()
        for v in extra:
            distractors.append({'chinese_meaning': v.chinese_meaning})

    for d in distractors:
        options.append({'text': d['chinese_meaning'], 'is_correct': False})

    random.shuffle(options)
    return options

@learning_bp.route('/')
@login_required
def index():
    """学习模式选择页面"""
    # 获取待复习词汇数
    due_count = UserVocabulary.query.filter(
        UserVocabulary.user_id == current_user.id,
        UserVocabulary.next_review_date <= datetime.utcnow()
    ).count()

    # 获取新词汇数
    learned_ids = db.session.query(UserVocabulary.vocabulary_id).filter(
        UserVocabulary.user_id == current_user.id
    ).subquery()
    new_count = Vocabulary.query.filter(
        Vocabulary.is_active == True,
        ~Vocabulary.id.in_(learned_ids)
    ).count()

    return render_template('learning/index.html',
        due_count=due_count,
        new_count=new_count
    )


@learning_bp.route('/start')
@learning_bp.route('/start/<mode>')
@login_required
def start(mode='flashcard'):
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
    session['learning_mode'] = mode
    session['learning_stats'] = {
        'total': len(session_vocab),
        'completed': 0,
        'correct': 0,
        'familiar': 0,  # 熟悉度 >= 3
        'start_time': datetime.utcnow().isoformat()
    }

    # 获取当前词汇
    current_vocab = session_vocab[0]

    if mode == 'multiple_choice':
        # 选择题模式：生成选项
        options = generate_options(current_vocab, session_vocab)
        return render_template('learning/multiple_choice.html',
            vocab=current_vocab,
            options=options,
            current=1,
            total=len(session_vocab)
        )
    elif mode == 'true_false':
        # 判断题模式：生成正确/错误配对
        shown_meaning, is_correct_pairing = generate_true_false(current_vocab, session_vocab)
        return render_template('learning/true_false.html',
            vocab=current_vocab,
            shown_meaning=shown_meaning,
            is_correct_pairing=is_correct_pairing,
            current=1,
            total=len(session_vocab)
        )
    else:
        # 闪卡模式
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


@learning_bp.route('/check-answer', methods=['POST'])
@login_required
def check_answer():
    """检查选择题答案"""
    data = request.get_json()
    vocab_id = data.get('vocabulary_id')
    selected_answer = data.get('selected_answer')
    time_taken = data.get('time_taken', 0)

    if not vocab_id or not selected_answer:
        return jsonify({'success': False, 'error': '缺少参数'}), 400

    # 获取正确答案
    vocab = Vocabulary.query.get(vocab_id)
    if not vocab:
        return jsonify({'success': False, 'error': '词汇不存在'}), 404

    is_correct = (selected_answer == vocab.chinese_meaning)

    # 更新 UserVocabulary
    uv = UserVocabulary.query.filter_by(
        user_id=current_user.id,
        vocabulary_id=vocab_id
    ).first()

    if uv:
        if is_correct:
            uv.familiarity_level = min(uv.familiarity_level + 1, 5)
            uv.correct_count += 1
        else:
            uv.familiarity_level = 1  # 答错重置
        uv.review_count += 1
        uv.next_review_date = calculate_next_review_date(uv.familiarity_level, uv.review_count)
        uv.last_reviewed = datetime.utcnow()

    # 记录答题
    attempt = QuizAttempt(
        user_id=current_user.id,
        vocabulary_id=vocab_id,
        quiz_type='multiple_choice',
        is_correct=is_correct,
        time_taken=time_taken
    )
    db.session.add(attempt)
    db.session.commit()

    # 更新会话统计
    stats = session.get('learning_stats', {})
    stats['completed'] = stats.get('completed', 0) + 1
    if is_correct:
        stats['correct'] = stats.get('correct', 0) + 1
        stats['familiar'] = stats.get('familiar', 0) + 1
    session['learning_stats'] = stats

    return jsonify({
        'success': True,
        'is_correct': is_correct,
        'correct_answer': vocab.chinese_meaning
    })


@learning_bp.route('/check-judgment', methods=['POST'])
@login_required
def check_judgment():
    """检查判断题答案"""
    data = request.get_json()
    vocab_id = data.get('vocabulary_id')
    user_answer = data.get('user_answer')  # True = 用户认为正确, False = 用户认为错误
    is_correct_pairing = data.get('is_correct_pairing')  # 实际是否正确配对
    time_taken = data.get('time_taken', 0)

    if vocab_id is None or user_answer is None or is_correct_pairing is None:
        return jsonify({'success': False, 'error': '缺少参数'}), 400

    # 判断用户是否答对
    is_user_correct = (user_answer == is_correct_pairing)

    # 更新 UserVocabulary
    uv = UserVocabulary.query.filter_by(
        user_id=current_user.id,
        vocabulary_id=vocab_id
    ).first()

    if uv:
        if is_user_correct:
            uv.familiarity_level = min(uv.familiarity_level + 1, 5)
            uv.correct_count += 1
        else:
            uv.familiarity_level = 1  # 答错重置
        uv.review_count += 1
        uv.next_review_date = calculate_next_review_date(uv.familiarity_level, uv.review_count)
        uv.last_reviewed = datetime.utcnow()

    # 记录答题
    attempt = QuizAttempt(
        user_id=current_user.id,
        vocabulary_id=vocab_id,
        quiz_type='true_false',
        is_correct=is_user_correct,
        time_taken=time_taken
    )
    db.session.add(attempt)
    db.session.commit()

    # 更新会话统计
    stats = session.get('learning_stats', {})
    stats['completed'] = stats.get('completed', 0) + 1
    if is_user_correct:
        stats['correct'] = stats.get('correct', 0) + 1
        stats['familiar'] = stats.get('familiar', 0) + 1
    session['learning_stats'] = stats

    return jsonify({
        'success': True,
        'is_user_correct': is_user_correct
    })


@learning_bp.route('/next', methods=['POST'])
@login_required
def next_vocab():
    """获取下一个词汇"""
    vocab_list = session.get('learning_vocab', [])
    current_index = session.get('learning_index', 0)
    mode = session.get('learning_mode', 'flashcard')
    next_index = current_index + 1

    if next_index >= len(vocab_list):
        return jsonify({
            'success': True,
            'completed': True,
            'redirect': url_for('learning.summary')
        })

    session['learning_index'] = next_index
    next_vocab_item = vocab_list[next_index]

    result = {
        'success': True,
        'completed': False,
        'vocab': next_vocab_item,
        'current': next_index + 1,
        'total': len(vocab_list)
    }

    if mode == 'multiple_choice':
        result['options'] = generate_options(next_vocab_item, vocab_list)
    elif mode == 'true_false':
        shown_meaning, is_correct_pairing = generate_true_false(next_vocab_item, vocab_list)
        result['shown_meaning'] = shown_meaning
        result['is_correct_pairing'] = is_correct_pairing

    return jsonify(result)


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
