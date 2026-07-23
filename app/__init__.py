import logging
from datetime import date
from pathlib import Path

from flask import Flask, render_template
from flask_wtf.csrf import CSRFError, CSRFProtect

from config import Config


csrf = CSRFProtect()


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
    _create_upload_directories(app)
    _register_blueprints(app)
    _register_error_handlers(app)

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        return response

    @app.context_processor
    def template_globals():
        return {"current_year": date.today().year}

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
    from app.routes.mainRoutes import main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)


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
