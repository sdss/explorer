"""WSGI instance"""

from __future__ import print_function, division, absolute_import
from .main import app

if __name__ == "__main__":
    app.run()
