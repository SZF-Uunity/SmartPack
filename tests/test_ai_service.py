"""AI 服务测试。"""

from app.services.ai_service import AIService


def test_extract_product_features_fragile() -> None:
    """验证易碎商品能正确识别与推荐材质。"""

    service = AIService()
    result = service.extract_product_features("玻璃杯 10x12x15cm 2kg 易碎")
    assert result["suggested_fragile"] is True
    assert result["material_recommendation"] == "高缓冲气泡垫"
