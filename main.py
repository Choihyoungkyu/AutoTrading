from flask import Flask
from src.api.routes import api_bp
import os


def create_app():
    app = Flask(__name__)
    app.register_blueprint(api_bp)
    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
