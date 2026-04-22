"""基础仓储层，隔离 ORM 与业务层。"""

from sqlalchemy.orm import Session


class BaseRepository:
    """基础仓储，提供公共查询能力。"""

    def __init__(self, db: Session):
        self.db = db
