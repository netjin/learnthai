from app.utils.srs import calculate_next_review_minutes, calculate_next_review_date, update_familiarity
from datetime import datetime, timedelta

def test_srs_failed_review():
    """答错后应该 10 分钟内复习"""
    interval = calculate_next_review_minutes(familiarity=2, review_count=5)
    assert interval == 10

def test_srs_first_success():
    """首次答对应该 1 天后复习"""
    interval = calculate_next_review_minutes(familiarity=3, review_count=0)
    assert interval == 1440  # 1 天 = 1440 分钟

def test_srs_progression():
    """复习间隔应该递增"""
    intervals = []
    for i in range(7):
        interval = calculate_next_review_minutes(familiarity=4, review_count=i)
        intervals.append(interval)

    # 确保间隔递增
    for i in range(len(intervals) - 1):
        assert intervals[i] <= intervals[i + 1]

def test_srs_max_interval():
    """最大间隔应该是 90 天"""
    interval = calculate_next_review_minutes(familiarity=5, review_count=10)
    assert interval == 129600  # 90 天 = 129600 分钟

def test_calculate_next_review_date():
    """测试计算下次复习日期"""
    base_date = datetime(2026, 1, 14, 10, 0, 0)

    # 10分钟后
    next_date = calculate_next_review_date(familiarity=2, review_count=0, from_date=base_date)
    assert next_date == base_date + timedelta(minutes=10)

    # 1天后
    next_date = calculate_next_review_date(familiarity=3, review_count=0, from_date=base_date)
    assert next_date == base_date + timedelta(days=1)

def test_update_familiarity_correct():
    """测试答对后熟悉度更新"""
    assert update_familiarity(0, True) == 1
    assert update_familiarity(3, True) == 4
    assert update_familiarity(5, True) == 5  # 最高 5

def test_update_familiarity_incorrect():
    """测试答错后熟悉度更新"""
    assert update_familiarity(3, False) == 1
    assert update_familiarity(5, False) == 1
    assert update_familiarity(0, False) == 1
