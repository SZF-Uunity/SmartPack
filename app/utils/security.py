"""安全工具模块。"""

import hashlib
import os


def hash_password(password: str) -> str:
    """使用 PBKDF2 对密码做强哈希存储。"""

    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return f"{salt.hex()}:{digest.hex()}"
