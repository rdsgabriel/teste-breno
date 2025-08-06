import os
from flask import Blueprint, redirect, url_for, session, abort
from authlib.integrations.flask_client import OAuth

auth_bp = Blueprint("auth", __name__)
oauth     = OAuth()

# carrega lista e domínio permitidos
ALLOWED       = [e.strip() for e in os.getenv("ALLOWED_EMAILS","").split(",") if e.strip()]
ALLOWED_DOMAIN = os.getenv("ALLOWED_DOMAIN")

def is_authorized(email):
    if ALLOWED and email in ALLOWED:
        return True
    return False

@auth_bp.route("/login")
def login():
    redirect_uri = url_for("auth.callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@auth_bp.route("/callback")
def callback():
    token    = oauth.google.authorize_access_token()
    profile  = oauth.google.get("userinfo").json()
    email    = profile.get("email")
    verified = profile.get("verified_email", False)

    if not (email and verified):
        return redirect(url_for("report.login_page", error="email_not_verified"))
    if not is_authorized(email):
        return redirect(url_for("report.login_page", error="unauthorized"))

    # marca na sessão
    session["email"]      = email
    session["authorized"] = True

    return redirect(url_for("report.home"))

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("report.login_page"))

# decorator que você pode importar em outros blueprints
def login_required(f):
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("authorized"):
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return wrapper
