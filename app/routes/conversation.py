from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import ConversationScene, Conversation, ConversationLine, UserConversation
from datetime import datetime
import random
import json

conversation_bp = Blueprint('conversation', __name__, url_prefix='/conversation')


@conversation_bp.route('/')
@login_required
def index():
    """场景列表页面"""
    scenes = ConversationScene.query.filter_by(is_active=True).order_by(
        ConversationScene.sort_order
    ).all()

    # 统计每个场景的学习进度
    for scene in scenes:
        scene.total_conversations = scene.conversations.filter_by(is_active=True).count()
        scene.completed = UserConversation.query.join(Conversation).filter(
            Conversation.scene_id == scene.id,
            UserConversation.user_id == current_user.id,
            UserConversation.familiarity_level >= 4
        ).count()

    return render_template('conversation/index.html', scenes=scenes)


@conversation_bp.route('/scene/<int:scene_id>')
@login_required
def scene(scene_id):
    """某个场景下的对话列表"""
    scene = ConversationScene.query.get_or_404(scene_id)
    conversations = scene.conversations.filter_by(is_active=True).order_by(
        Conversation.sort_order
    ).all()

    # 获取用户进度
    for conv in conversations:
        user_progress = UserConversation.query.filter_by(
            user_id=current_user.id,
            conversation_id=conv.id
        ).first()
        conv.user_familiarity = user_progress.familiarity_level if user_progress else 0
        conv.completed_modes = json.loads(user_progress.completed_modes) if user_progress and user_progress.completed_modes else []

    return render_template('conversation/scene.html', scene=scene, conversations=conversations)


@conversation_bp.route('/view/<int:conversation_id>')
@login_required
def view(conversation_id):
    """查看完整对话"""
    conversation = Conversation.query.get_or_404(conversation_id)
    lines = conversation.lines.order_by(ConversationLine.line_order).all()

    return render_template('conversation/view.html', conversation=conversation, lines=lines)


@conversation_bp.route('/practice/<int:conversation_id>/<mode>')
@login_required
def practice(conversation_id, mode):
    """开始练习"""
    conversation = Conversation.query.get_or_404(conversation_id)
    lines = conversation.lines.order_by(ConversationLine.line_order).all()

    if mode == 'fill_blank':
        # 生成填空练习
        exercises = generate_fill_blank_exercise(lines)
        return render_template('conversation/fill_blank.html',
                             conversation=conversation,
                             exercises=exercises)
    elif mode == 'order':
        # 生成排序练习
        exercise_data = generate_order_exercise(lines)
        return render_template('conversation/order.html',
                             conversation=conversation,
                             shuffled_lines=exercise_data['shuffled_lines'],
                             correct_order=exercise_data['correct_order'])
    elif mode == 'role_play':
        # 角色扮演模式
        return render_template('conversation/role_play.html',
                             conversation=conversation,
                             lines=lines)
    else:
        flash('未知的练习模式', 'error')
        return redirect(url_for('conversation.view', conversation_id=conversation_id))


def generate_fill_blank_exercise(lines):
    """从对话中随机选择关键词作为填空题"""
    exercises = []

    for line in lines:
        # 解析关键词
        try:
            key_words = json.loads(line.key_words) if line.key_words else []
        except:
            key_words = []

        if key_words:
            # 随机选择1-2个关键词作为空格
            num_blanks = min(2, len(key_words))
            blanks = random.sample(key_words, num_blanks)
            text_with_blanks = line.text_thai

            # 替换为统一的占位符
            blank_answers = []
            for word in blanks:
                if word in text_with_blanks:
                    text_with_blanks = text_with_blanks.replace(word, '____', 1)
                    blank_answers.append({'index': len(blank_answers), 'answer': word})

            exercises.append({
                'line_id': line.id,
                'text_with_blanks': text_with_blanks,
                'blanks': blank_answers,
                'chinese': line.text_chinese,
                'speaker': line.speaker_role
            })

    return exercises


def generate_order_exercise(lines):
    """打乱对话顺序让用户排序"""
    lines_list = list(lines)
    shuffled = lines_list.copy()
    random.shuffle(shuffled)

    return {
        'correct_order': [line.id for line in lines_list],
        'shuffled_lines': [{
            'id': line.id,
            'text_thai': line.text_thai,
            'text_chinese': line.text_chinese,
            'speaker': line.speaker_role
        } for line in shuffled]
    }


@conversation_bp.route('/check-fill-blank', methods=['POST'])
@login_required
def check_fill_blank():
    """检查填空答案"""
    data = request.get_json()
    conversation_id = data.get('conversation_id')
    answers = data.get('answers', [])

    if not conversation_id:
        return jsonify({'success': False, 'error': '缺少对话ID'}), 400

    # 验证答案
    results = []
    total_correct = 0

    for answer in answers:
        line_id = answer.get('line_id')
        user_answers = answer.get('user_answers', [])

        line = ConversationLine.query.get(line_id)
        if not line:
            continue

        try:
            key_words = json.loads(line.key_words) if line.key_words else []
        except:
            key_words = []

        # 检查每个空格
        line_correct = 0
        for i, user_answer in enumerate(user_answers):
            if i < len(key_words):
                is_correct = user_answer.strip() == key_words[i].strip()
                if is_correct:
                    line_correct += 1
                    total_correct += 1

        results.append({
            'line_id': line_id,
            'correct': line_correct,
            'total': len(user_answers)
        })

    # 更新用户进度
    update_user_progress(conversation_id, 'fill_blank', total_correct, len(answers))

    return jsonify({
        'success': True,
        'results': results,
        'total_correct': total_correct
    })


@conversation_bp.route('/check-order', methods=['POST'])
@login_required
def check_order():
    """检查排序答案"""
    data = request.get_json()
    conversation_id = data.get('conversation_id')
    user_order = data.get('user_order', [])
    correct_order = data.get('correct_order', [])

    if not conversation_id:
        return jsonify({'success': False, 'error': '缺少对话ID'}), 400

    # 检查顺序是否正确
    is_correct = user_order == correct_order

    # 更新用户进度
    update_user_progress(conversation_id, 'order', 1 if is_correct else 0, 1)

    return jsonify({
        'success': True,
        'is_correct': is_correct,
        'correct_order': correct_order
    })


@conversation_bp.route('/submit-practice', methods=['POST'])
@login_required
def submit_practice():
    """提交练习结果"""
    data = request.get_json()
    conversation_id = data.get('conversation_id')
    mode = data.get('mode')
    score = data.get('score', 0)

    if not conversation_id or not mode:
        return jsonify({'success': False, 'error': '缺少参数'}), 400

    # 更新用户进度
    update_user_progress(conversation_id, mode, score, 1)

    return jsonify({'success': True})


def update_user_progress(conversation_id, mode, correct_count, total_count):
    """更新用户学习进度"""
    user_conv = UserConversation.query.filter_by(
        user_id=current_user.id,
        conversation_id=conversation_id
    ).first()

    if not user_conv:
        user_conv = UserConversation(
            user_id=current_user.id,
            conversation_id=conversation_id,
            familiarity_level=0,
            completed_modes='[]',
            practice_count=0
        )
        db.session.add(user_conv)

    # 更新练习次数
    user_conv.practice_count += 1
    user_conv.last_practiced = datetime.utcnow()

    # 更新已完成的模式
    try:
        completed_modes = json.loads(user_conv.completed_modes) if user_conv.completed_modes else []
    except:
        completed_modes = []

    if mode not in completed_modes:
        completed_modes.append(mode)
        user_conv.completed_modes = json.dumps(completed_modes)

    # 根据正确率更新熟练度
    accuracy = correct_count / total_count if total_count > 0 else 0
    if accuracy >= 0.9:
        user_conv.familiarity_level = min(user_conv.familiarity_level + 1, 5)
    elif accuracy >= 0.7:
        user_conv.familiarity_level = max(user_conv.familiarity_level, 3)
    elif accuracy < 0.5:
        user_conv.familiarity_level = max(user_conv.familiarity_level - 1, 0)

    db.session.commit()


@conversation_bp.route('/progress')
@login_required
def progress():
    """用户学习进度总览"""
    # 获取所有场景及进度
    scenes = ConversationScene.query.filter_by(is_active=True).order_by(
        ConversationScene.sort_order
    ).all()

    progress_data = []
    for scene in scenes:
        total = scene.conversations.filter_by(is_active=True).count()
        completed = UserConversation.query.join(Conversation).filter(
            Conversation.scene_id == scene.id,
            UserConversation.user_id == current_user.id,
            UserConversation.familiarity_level >= 4
        ).count()

        progress_data.append({
            'scene': scene,
            'total': total,
            'completed': completed,
            'percentage': round(completed / total * 100) if total > 0 else 0
        })

    # 总体统计
    total_conversations = Conversation.query.filter_by(is_active=True).count()
    total_completed = UserConversation.query.filter(
        UserConversation.user_id == current_user.id,
        UserConversation.familiarity_level >= 4
    ).count()

    return render_template('conversation/progress.html',
                         progress_data=progress_data,
                         total_conversations=total_conversations,
                         total_completed=total_completed)
