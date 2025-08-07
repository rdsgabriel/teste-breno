import os
from flask import Flask
from dotenv import load_dotenv
from .auth import oauth
from werkzeug.middleware.proxy_fix import ProxyFix


def create_app():
    load_dotenv() # Carrega variáveis de ambiente do .env para desenvolvimento local
    app = Flask(__name__)

    # Corrige o problema de sessão/CSRF por trás do proxy do Fly.io
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)
    
    app.debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    # Em produção (Fly.io), a SECRET_KEY virá das variáveis de ambiente/secrets da plataforma.
    # Para desenvolvimento local, ela virá do seu arquivo .env.
    app.secret_key = os.getenv("SECRET_KEY")

    # configura OAuth Google
    oauth.init_app(app)
    oauth.register(
        name="google",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        access_token_url="https://oauth2.googleapis.com/token",
        authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
        api_base_url="https://www.googleapis.com/oauth2/v2/",
        client_kwargs={"scope": "openid email profile"},
        jwks_uri="https://www.googleapis.com/oauth2/v3/certs"
    )

    # registra blueprint de auth
    from .auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")

    from .routes.views import report_bp
    app.register_blueprint(report_bp, url_prefix="/")

    return app