from app import create_app, db
from app.models import User
import getpass

def create_admin():
    """创建管理员账户"""
    app = create_app()
    with app.app_context():
        username = input("管理员用户名: ")
        email = input("管理员邮箱: ")
        password = getpass.getpass("管理员密码: ")

        if User.query.filter_by(username=username).first():
            print(f"✗ 错误：用户名 '{username}' 已存在")
            return

        if User.query.filter_by(email=email).first():
            print(f"✗ 错误：邮箱 '{email}' 已注册")
            return

        admin = User(username=username, email=email, is_admin=True)
        admin.set_password(password)

        db.session.add(admin)
        db.session.commit()

        print(f"✓ 管理员账户 '{username}' 创建成功！")

if __name__ == '__main__':
    create_admin()
