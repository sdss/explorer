"""
Explorer's FastAPI backend for serving custom summary files, can also host dashboard
"""

from .main import app

if __name__ == "__main__":
    app.run()
