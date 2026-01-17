from flask import Blueprint, render_template, redirect, url_for, request, session, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import ThaiAlphabet, UserAlphabet
from app.utils.srs import calculate_next_review_date
from datetime import datetime
import random

alphabet_bp = Blueprint('alphabet', __name__, url_prefix='/alphabet')


@alphabet_bp.route('/')
@login_required
def index():
    """字母学习首页"""
    # 辅音统计
    consonant_total = ThaiAlphabet.query.filter_by(alphabet_type='consonant', is_active=True).count()
    consonant_learned = UserAlphabet.query.join(ThaiAlphabet).filter(
        UserAlphabet.user_id == current_user.id,
        ThaiAlphabet.alphabet_type == 'consonant'
    ).count()

    # 元音统计
    vowel_total = ThaiAlphabet.query.filter_by(alphabet_type='vowel', is_active=True).count()
    vowel_learned = UserAlphabet.query.join(ThaiAlphabet).filter(
        UserAlphabet.user_id == current_user.id,
        ThaiAlphabet.alphabet_type == 'vowel'
    ).count()

    return render_template('alphabet/index.html',
        consonant_total=consonant_total,
        consonant_learned=consonant_learned,
        vowel_total=vowel_total,
        vowel_learned=vowel_learned
    )


@alphabet_bp.route('/consonants')
@login_required
def consonants():
    """辅音列表"""
    # 按辅音类别分组
    mid_consonants = ThaiAlphabet.query.filter_by(
        alphabet_type='consonant', consonant_class='mid', is_active=True
    ).order_by(ThaiAlphabet.sort_order).all()

    high_consonants = ThaiAlphabet.query.filter_by(
        alphabet_type='consonant', consonant_class='high', is_active=True
    ).order_by(ThaiAlphabet.sort_order).all()

    low_consonants = ThaiAlphabet.query.filter_by(
        alphabet_type='consonant', consonant_class='low', is_active=True
    ).order_by(ThaiAlphabet.sort_order).all()

    # 获取用户学习进度
    user_progress = {ua.alphabet_id: ua for ua in UserAlphabet.query.filter_by(user_id=current_user.id).all()}

    return render_template('alphabet/consonants.html',
        mid_consonants=mid_consonants,
        high_consonants=high_consonants,
        low_consonants=low_consonants,
        user_progress=user_progress
    )


@alphabet_bp.route('/vowels')
@login_required
def vowels():
    """元音列表"""
    # 按元音类型分组
    short_vowels = ThaiAlphabet.query.filter_by(
        alphabet_type='vowel', vowel_type='short', is_active=True
    ).order_by(ThaiAlphabet.sort_order).all()

    long_vowels = ThaiAlphabet.query.filter_by(
        alphabet_type='vowel', vowel_type='long', is_active=True
    ).order_by(ThaiAlphabet.sort_order).all()

    compound_vowels = ThaiAlphabet.query.filter_by(
        alphabet_type='vowel', vowel_type='compound', is_active=True
    ).order_by(ThaiAlphabet.sort_order).all()

    special_vowels = ThaiAlphabet.query.filter(
        ThaiAlphabet.alphabet_type == 'vowel',
        ThaiAlphabet.vowel_type.in_(['special', 'short_compound']),
        ThaiAlphabet.is_active == True
    ).order_by(ThaiAlphabet.sort_order).all()

    # 获取用户学习进度
    user_progress = {ua.alphabet_id: ua for ua in UserAlphabet.query.filter_by(user_id=current_user.id).all()}

    return render_template('alphabet/vowels.html',
        short_vowels=short_vowels,
        long_vowels=long_vowels,
        compound_vowels=compound_vowels,
        special_vowels=special_vowels,
        user_progress=user_progress
    )


@alphabet_bp.route('/practice')
@alphabet_bp.route('/practice/<alphabet_type>')
@login_required
def practice(alphabet_type='all'):
    """字母练习"""
    mode = request.args.get('mode', 'flashcard')

    # 获取要练习的字母
    query = ThaiAlphabet.query.filter_by(is_active=True)
    if alphabet_type == 'consonant':
        query = query.filter_by(alphabet_type='consonant')
    elif alphabet_type == 'vowel':
        query = query.filter_by(alphabet_type='vowel')

    alphabets = query.order_by(ThaiAlphabet.sort_order).all()

    if not alphabets:
        return redirect(url_for('alphabet.index'))

    # 随机打乱顺序
    random.shuffle(alphabets)

    # 限制每次练习数量
    max_count = min(20, len(alphabets))
    practice_list = alphabets[:max_count]

    # 存储会话
    session['alphabet_practice'] = [{
        'id': a.id,
        'character': a.character,
        'name_thai': a.name_thai,
        'name_chinese': a.name_chinese,
        'pronunciation': a.pronunciation,
        'sound': a.sound,
        'alphabet_type': a.alphabet_type,
        'example_word': a.example_word,
        'example_meaning': a.example_meaning
    } for a in practice_list]
    session['alphabet_index'] = 0
    session['alphabet_mode'] = mode
    session['alphabet_stats'] = {
        'total': len(practice_list),
        'completed': 0,
        'correct': 0
    }

    current = session['alphabet_practice'][0]

    if mode == 'multiple_choice':
        options = generate_alphabet_options(current, alphabets)
        return render_template('alphabet/practice_choice.html',
            alphabet=current,
            options=options,
            current=1,
            total=len(practice_list),
            alphabet_type=alphabet_type
        )
    else:
        return render_template('alphabet/practice_flashcard.html',
            alphabet=current,
            current=1,
            total=len(practice_list),
            alphabet_type=alphabet_type
        )


def generate_alphabet_options(correct, all_alphabets):
    """生成字母选择题选项"""
    correct_answer = correct['name_chinese']
    options = [{'text': correct_answer, 'is_correct': True}]

    # 从同类型字母中选择干扰项
    same_type = [a for a in all_alphabets
                 if a.alphabet_type == correct['alphabet_type']
                 and a.name_chinese != correct_answer]

    if len(same_type) >= 3:
        distractors = random.sample(same_type, 3)
    else:
        distractors = same_type
        other = [a for a in all_alphabets if a.name_chinese != correct_answer and a not in distractors]
        if other:
            distractors += random.sample(other, min(3 - len(distractors), len(other)))

    for d in distractors:
        options.append({'text': d.name_chinese, 'is_correct': False})

    random.shuffle(options)
    return options


@alphabet_bp.route('/practice/check', methods=['POST'])
@login_required
def check_alphabet_answer():
    """检查字母答案"""
    data = request.get_json()
    alphabet_id = data.get('alphabet_id')
    selected_answer = data.get('selected_answer')

    alphabet = ThaiAlphabet.query.get(alphabet_id)
    if not alphabet:
        return jsonify({'success': False, 'error': '字母不存在'}), 404

    is_correct = (selected_answer == alphabet.name_chinese)

    # 更新用户进度
    ua = UserAlphabet.query.filter_by(
        user_id=current_user.id,
        alphabet_id=alphabet_id
    ).first()

    if not ua:
        ua = UserAlphabet(
            user_id=current_user.id,
            alphabet_id=alphabet_id,
            familiarity_level=1 if is_correct else 0,
            review_count=1,
            correct_count=1 if is_correct else 0,
            next_review_date=calculate_next_review_date(1 if is_correct else 0, 1),
            last_reviewed=datetime.utcnow()
        )
        db.session.add(ua)
    else:
        if is_correct:
            ua.familiarity_level = min(ua.familiarity_level + 1, 5)
            ua.correct_count += 1
        else:
            ua.familiarity_level = max(ua.familiarity_level - 1, 0)
        ua.review_count += 1
        ua.next_review_date = calculate_next_review_date(ua.familiarity_level, ua.review_count)
        ua.last_reviewed = datetime.utcnow()

    db.session.commit()

    # 更新会话统计
    stats = session.get('alphabet_stats', {})
    stats['completed'] = stats.get('completed', 0) + 1
    if is_correct:
        stats['correct'] = stats.get('correct', 0) + 1
    session['alphabet_stats'] = stats

    return jsonify({
        'success': True,
        'is_correct': is_correct,
        'correct_answer': alphabet.name_chinese
    })


@alphabet_bp.route('/practice/submit', methods=['POST'])
@login_required
def submit_alphabet():
    """提交闪卡答案"""
    data = request.get_json()
    alphabet_id = data.get('alphabet_id')
    familiarity = data.get('familiarity', 0)

    # 更新用户进度
    ua = UserAlphabet.query.filter_by(
        user_id=current_user.id,
        alphabet_id=alphabet_id
    ).first()

    if not ua:
        ua = UserAlphabet(
            user_id=current_user.id,
            alphabet_id=alphabet_id,
            familiarity_level=familiarity,
            review_count=1,
            correct_count=1 if familiarity >= 3 else 0,
            next_review_date=calculate_next_review_date(familiarity, 1),
            last_reviewed=datetime.utcnow()
        )
        db.session.add(ua)
    else:
        ua.familiarity_level = familiarity
        ua.review_count += 1
        if familiarity >= 3:
            ua.correct_count += 1
        ua.next_review_date = calculate_next_review_date(familiarity, ua.review_count)
        ua.last_reviewed = datetime.utcnow()

    db.session.commit()

    # 更新会话统计
    stats = session.get('alphabet_stats', {})
    stats['completed'] = stats.get('completed', 0) + 1
    if familiarity >= 3:
        stats['correct'] = stats.get('correct', 0) + 1
    session['alphabet_stats'] = stats

    return jsonify({'success': True})


@alphabet_bp.route('/practice/next', methods=['POST'])
@login_required
def next_alphabet():
    """获取下一个字母"""
    practice_list = session.get('alphabet_practice', [])
    current_index = session.get('alphabet_index', 0)
    mode = session.get('alphabet_mode', 'flashcard')
    next_index = current_index + 1

    if next_index >= len(practice_list):
        stats = session.get('alphabet_stats', {})
        return jsonify({
            'success': True,
            'completed': True,
            'stats': stats
        })

    session['alphabet_index'] = next_index
    next_item = practice_list[next_index]

    result = {
        'success': True,
        'completed': False,
        'alphabet': next_item,
        'current': next_index + 1,
        'total': len(practice_list)
    }

    if mode == 'multiple_choice':
        # 重新获取所有字母用于生成选项
        all_alphabets = ThaiAlphabet.query.filter_by(
            alphabet_type=next_item['alphabet_type'],
            is_active=True
        ).all()
        result['options'] = generate_alphabet_options(next_item, all_alphabets)

    return jsonify(result)


@alphabet_bp.route('/practice/summary')
@login_required
def practice_summary():
    """练习总结"""
    stats = session.get('alphabet_stats', {})
    total = stats.get('total', 0)
    completed = stats.get('completed', 0)
    correct = stats.get('correct', 0)
    accuracy = round(correct / completed * 100) if completed > 0 else 0

    return render_template('alphabet/summary.html',
        total=total,
        completed=completed,
        correct=correct,
        accuracy=accuracy
    )
