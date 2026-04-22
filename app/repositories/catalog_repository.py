"""产品/箱型仓储层。"""

from app.models.entities import Box, Product
from app.repositories.base import BaseRepository
from app.schemas.dto import BoxCreate, ProductCreate


class CatalogRepository(BaseRepository):
    """管理产品和箱型数据，便于未来替换数据源。"""

    def create_product(self, payload: ProductCreate) -> Product:
        """创建产品记录。"""

        product = Product(**payload.model_dump())
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    def create_box(self, payload: BoxCreate) -> Box:
        """创建箱型并做外内尺寸规则校验。"""

        if not (
            payload.outer_length > payload.inner_length
            and payload.outer_width > payload.inner_width
            and payload.outer_height > payload.inner_height
        ):
            raise ValueError("箱子外尺寸必须大于内尺寸")

        box = Box(**payload.model_dump())
        self.db.add(box)
        self.db.commit()
        self.db.refresh(box)
        return box
