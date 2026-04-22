"""安全相关仓储层。"""

from app.models.entities import ApiKey
from app.repositories.base import BaseRepository
from app.schemas.dto import ApiKeyCreate
from app.utils.security import hash_api_key


class SecurityRepository(BaseRepository):
    """API Key 数据访问层。"""

    def create_api_key(self, payload: ApiKeyCreate) -> ApiKey:
        """创建 API Key（数据库仅保存哈希值）。"""

        api_key = ApiKey(
            name=payload.name,
            key_hash=hash_api_key(payload.raw_key),
            owner_user_id=payload.owner_user_id,
            ip_whitelist=payload.ip_whitelist,
            rate_limit_per_minute=payload.rate_limit_per_minute,
            enabled=True,
        )
        self.db.add(api_key)
        self.db.commit()
        self.db.refresh(api_key)
        return api_key
