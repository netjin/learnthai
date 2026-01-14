from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config

db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录'

    # 注册蓝图
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    # 主页路由
    @app.route('/')
    def index():
        return render_template('index.html')

    return app
