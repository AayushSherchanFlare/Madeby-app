import logging
from datetime import date
from pathlib import Path

from flask import Flask, render_template, request
from flask_wtf.csrf import CSRFError, CSRFProtect
from authlib.integrations.flask_client import OAuth

from config import Config


csrf = CSRFProtect()
oauth = OAuth()


def create_app(config_class=Config):
    """Create and configure the MadeBy Flask application."""
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(config_class)

    if (
        not app.config["TESTING"]
        and app.config["SECRET_KEY"] == "development-only-change-me"
    ):
        app.logger.warning("SECRET_KEY is using the insecure development fallback")

    csrf.init_app(app)
    oauth.init_app(app)
    if app.config["GOOGLE_CLIENT_ID"] and app.config["GOOGLE_CLIENT_SECRET"]:
        oauth.register(
            name="google",
            client_id=app.config["GOOGLE_CLIENT_ID"],
            client_secret=app.config["GOOGLE_CLIENT_SECRET"],
            authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
            access_token_url="https://oauth2.googleapis.com/token",
            api_base_url="https://openidconnect.googleapis.com/",
            issuer="https://accounts.google.com",
            jwks_uri="https://www.googleapis.com/oauth2/v3/certs",
            userinfo_endpoint="https://openidconnect.googleapis.com/v1/userinfo",
            id_token_signing_alg_values_supported=["RS256"],
            client_kwargs={
                "scope": "openid email profile",
                "token_endpoint_auth_method": "client_secret_post",
                "default_timeout": 15,
            },
        )
    _create_upload_directories(app)
    _register_blueprints(app)
    _register_error_handlers(app)

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        if request.endpoint and request.endpoint.startswith(("social.", "godhood.")):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.context_processor
    def template_globals():
        def asset_version(filename):
            try:
                return (Path(app.static_folder) / filename).stat().st_mtime_ns
            except OSError:
                return 1

        return {
            "asset_version": asset_version,
            "current_year": date.today().year,
        }

    return app


def _create_upload_directories(app):
    for config_key in (
        "PROFILE_UPLOAD_FOLDER",
        "COVER_UPLOAD_FOLDER",
        "PROJECT_UPLOAD_FOLDER",
    ):
        Path(app.config[config_key]).mkdir(parents=True, exist_ok=True)


def _register_blueprints(app):
    from app.routes.authRoutes import auth_bp
    from app.routes.adminRoutes import godhood_bp
    from app.routes.mainRoutes import main_bp
    from app.routes.socialRoutes import social_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(social_bp)
    app.register_blueprint(godhood_bp)


def _register_error_handlers(app):
    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(413)
    def request_too_large(_error):
        return render_template("errors/413.html"), 413

    @app.errorhandler(CSRFError)
    def csrf_error(error):
        return render_template("errors/403.html", error_message=error.description), 403

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error("Unhandled application error: %s", error)
        return render_template("errors/500.html"), 500

    if not app.debug:
        logging.basicConfig(level=logging.INFO)
