"""API模块

提供RESTful API接口。
"""

from .routes import create_app

__all__ = ["create_app"]