from app.models import User
from app import db

def test_inactive_user_cannot_login(client, app):
    """测试禁用用户无法登录"""
    with app.app_context():
        user = User(username='inactive', email='inactive@test.com', is_active=False)
        user.set_password('pass')
        db.session.add(user)
        db.session.commit()

    response = client.post('/auth/login', data={
        'username': 'inactive',
        'password': 'pass'
    }, follow_redirects=True)

    assert '账户已被禁用' in response.data.decode('utf-8')
