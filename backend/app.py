"""AI Companion: Flask app that serves both the API (/api/*) and the frontend."""
import logging
from datetime import timedelta

from flask import Flask, request, send_from_directory
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from config import FRONTEND_DIR, Config
from database import init_db
from routes import auth, chat, conversations, memory, profile
from utils import ApiError, fail, ok

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("companion")


def create_app():
    app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")
    app.config.update(
        SECRET_KEY=Config.SECRET_KEY,
        MAX_CONTENT_LENGTH=Config.MAX_CONTENT_LENGTH,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=Config.COOKIE_SECURE,
        PERMANENT_SESSION_LIFETIME=timedelta(days=14),
    )
    if Config.SECRET_KEY == "change_this_secret_key":
        log.warning("SECRET_KEY is still the default. Set a long random value in .env before deploying.")
    if not Config.ai_configured():
        log.warning("GROQ_API_KEY is not set. The app will run, but chat replies need a key in .env.")

    CORS(app, resources={r"/api/*": {"origins": Config.CORS_ORIGINS}}, supports_credentials=True)
    init_db()

    for module in (auth, chat, conversations, memory, profile):
        app.register_blueprint(module.bp, url_prefix="/api")

    @app.get("/api/health")
    def health():
        return ok({"status": "ok", "ai_configured": Config.ai_configured()})

    @app.get("/")
    def index():
        return send_from_directory(FRONTEND_DIR, "index.html")

    @app.after_request
    def security_headers(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Referrer-Policy", "same-origin")
        if request.path.startswith("/api/"):
            resp.headers["Cache-Control"] = "no-store"
        return resp

    @app.errorhandler(ApiError)
    def handle_api_error(err):
        return fail(err.message, err.status)

    @app.errorhandler(404)
    def not_found(_):
        if request.path.startswith("/api/"):
            return fail("That endpoint doesn't exist.", 404)
        return send_from_directory(FRONTEND_DIR, "index.html"), 404

    @app.errorhandler(405)
    def bad_method(_):
        return fail("That action isn't allowed here.", 405)

    @app.errorhandler(413)
    def too_large(_):
        return fail("That request is too large.", 413)

    @app.errorhandler(Exception)
    def unexpected(err):
        if isinstance(err, HTTPException):
            return fail("That request couldn't be processed.", err.code or 400)
        log.exception("Unhandled error: %s", err)
        return fail("Something went wrong on our side. Please try again.", 500)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=Config.PORT, debug=Config.DEBUG, threaded=True)
