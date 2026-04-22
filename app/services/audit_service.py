"""审计日志服务。"""

import logging

from sqlalchemy.orm import Session

from app.models.entities import AuditLog

logger = logging.getLogger(__name__)


class AuditService:
    """统一写入审计事件。"""

    def __init__(self, db: Session):
        self.db = db

    def record(self, actor: str, action: str, target: str, detail: str = "") -> None:
        """记录审计日志。

        审计是企业级系统的关键能力，因此将记录逻辑集中在独立服务中。
        """

        log = AuditLog(actor=actor, action=action, target=target, detail=detail)
        self.db.add(log)
        self.db.commit()
        logger.info("审计链路：actor=%s action=%s target=%s", actor, action, target)
