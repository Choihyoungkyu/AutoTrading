from flask import Flask
from src.api.routes import api_bp
import os


def create_app():
    # frontend/dist(빌드 산출물)를 정적으로 서빙. /assets/* 등은 Flask가 자동 처리.
    app = Flask(__name__, static_folder="frontend/dist", static_url_path="")
    app.register_blueprint(api_bp)
    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
