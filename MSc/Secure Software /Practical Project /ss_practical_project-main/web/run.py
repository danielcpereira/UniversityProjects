from app import app
import os

if __name__ == "__main__":
    app = app.create_app()
    debug = os.getenv("FLASK_DEBUG") == "1"
    host = os.getenv("FLASK_HOST", "0.0.0.0") # nosec B104
    port = int(os.getenv("FLASK_PORT", "8000"))
    app.run(host=host, port=port, debug=debug)