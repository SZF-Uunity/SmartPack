"""安全工具模块。"""

import hashlib
import hmac
import os


def hash_password(password: str) -> str:
    """使用 PBKDF2 对密码做强哈希存储。"""

    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return f"{salt.hex()}:{digest.hex()}"


def verify_password(password: str, hashed_password: str) -> bool:
    """校验密码是否匹配。"""

    salt_hex, digest_hex = hashed_password.split(":", maxsplit=1)
    calc_digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt_hex),
        100_000,
    ).hex()
    return hmac.compare_digest(calc_digest, digest_hex)


def hash_api_key(raw_key: str) -> str:
    """对 API Key 做不可逆哈希存储。"""

    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
