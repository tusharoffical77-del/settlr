from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from Config import Config

db = SQLAlchemy()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    jwt.init_app(app)

    with app.app_context():
        from models import user, group, expense
        db.create_all()

        from routes.auth import auth_bp
        app.register_blueprint(auth_bp, url_prefix="/auth")

        from routes.group import group_bp
        app.register_blueprint(group_bp, url_prefix="/groups")

        from routes.expense import expense_bp
        app.register_blueprint(expense_bp, url_prefix="/groups")

        from routes.balance import balance_bp
        app.register_blueprint(balance_bp, url_prefix="/groups")

    @app.route("/")
    def home():
        return {"message": "Settlr API is running", "status": "ok"}

    return app