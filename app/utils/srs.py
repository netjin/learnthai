from datetime import datetime, timedelta

def calculate_next_review_minutes(familiarity, review_count):
    """
    计算下次复习的间隔时间（分钟）

    Args:
        familiarity: 熟悉度等级 (0-5)
        review_count: 已复习次数

    Returns:
        int: 下次复习间隔（分钟）
    """
    # 答错或不熟练（熟悉度 < 3）：重新学习
    if familiarity < 3:
        return 10  # 10 分钟

    # 答对的情况：根据复习次数递增间隔
    interval_map = {
        0: 1440,      # 首次：1天
        1: 4320,      # 第1次：3天
        2: 10080,     # 第2次：7天
        3: 21600,     # 第3次：15天
        4: 43200,     # 第4次：30天
        5: 86400,     # 第5次：60天
        6: 129600,    # 第6次：90天
    }

    # 第7次及以后：90天
    if review_count >= 7:
        return 129600

    return interval_map.get(review_count, 10)

def calculate_next_review_date(familiarity, review_count, from_date=None):
    """
    计算下次复习的日期时间

    Args:
        familiarity: 熟悉度等级 (0-5)
        review_count: 已复习次数
        from_date: 起始日期（默认为当前时间）

    Returns:
        datetime: 下次复习时间
    """
    if from_date is None:
        from_date = datetime.utcnow()

    minutes = calculate_next_review_minutes(familiarity, review_count)
    return from_date + timedelta(minutes=minutes)

def update_familiarity(current_familiarity, is_correct):
    """
    根据答题结果更新熟悉度

    Args:
        current_familiarity: 当前熟悉度 (0-5)
        is_correct: 是否答对

    Returns:
        int: 新的熟悉度等级
    """
    if is_correct:
        # 答对：熟悉度 +1，最高 5
        return min(current_familiarity + 1, 5)
    else:
        # 答错：重置为 1
        return 1
