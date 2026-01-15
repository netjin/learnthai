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

def test_non_admin_cannot_access_admin(client, app):
    """测试非管理员无法访问后台"""
    with app.app_context():
        user = User(username='normal', email='normal@test.com', is_admin=False)
        user.set_password('pass')
        db.session.add(user)
        db.session.commit()

    client.post('/auth/login', data={
        'username': 'normal',
        'password': 'pass'
    })

    response = client.get('/admin/')
    assert response.status_code == 403

def test_admin_can_access_admin(client, app):
    """测试管理员可以访问后台"""
    with app.app_context():
        admin = User(username='admin', email='admin@test.com', is_admin=True)
        admin.set_password('pass')
        db.session.add(admin)
        db.session.commit()

    client.post('/auth/login', data={
        'username': 'admin',
        'password': 'pass'
    })

    response = client.get('/admin/')
    assert response.status_code == 200
