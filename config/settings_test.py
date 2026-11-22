"""
pytest 自動テスト用の Django 設定。
Neon (本番PostgreSQL) への接続を完全に遮断し、インメモリ SQLite を使用します。
"""
from .settings import *

# テスト実行時はインメモリ SQLite で高速・安全に実行
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# パスワードハッシュを高速化
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# テスト時は静的ファイルキャッシュを無効化
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
