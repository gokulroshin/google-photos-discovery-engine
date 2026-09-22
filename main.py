import os
import uvicorn
from backend.config import get_settings
from backend.logger import logger
from backend.main import app

if __name__ == "__main__":
    settings = get_settings()
    port_env = os.environ.get("PORT", "")
    try:
        port = int(port_env) if port_env and port_env != "$PORT" else settings.PORT
    except Exception:
        port = 8000
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"[Railway Entrypoint] Starting Uvicorn server on {host}:{port}...")
    uvicorn.run(app, host=host, port=port)
