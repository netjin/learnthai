from app.models import User
from app import db

def test_register_new_user(client, app):
    """测试新用户注册"""
    response = client.post('/auth/register', data={
        'username': 'newuser',
        'email': 'new@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)

    assert response.status_code == 200

    with app.app_context():
        user = User.query.filter_by(username='newuser').first()
        assert user is not None
        assert user.email == 'new@example.com'

def test_register_duplicate_username(client, app):
    """测试重复用户名注册"""
    with app.app_context():
        user = User(username='existing', email='existing@test.com')
        user.set_password('pass')
        db.session.add(user)
        db.session.commit()

    response = client.post('/auth/register', data={
        'username': 'existing',
        'email': 'new@test.com',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)

    assert '用户名已存在' in response.data.decode('utf-8')
