"""AI 辅助解析服务。"""

import logging
import re

logger = logging.getLogger(__name__)


class AIService:
    """使用规则引擎模拟自然语言解析，后续可替换为真实大模型调用。"""

    def extract_product_features(self, description: str) -> dict:
        """从中文描述中提取易碎、尺寸、重量并推荐材质。

        这里使用轻量规则法保证可离线部署，不依赖外部模型服务。
        """

        logger.info("AI解析链路开始：接收描述文本")
        fragile = any(keyword in description for keyword in ["易碎", "玻璃", "陶瓷"])

        # 提取形如 10x20x30cm 的尺寸信息。
        size_match = re.search(r"(\d+(?:\.\d+)?)\s*[xX*]\s*(\d+(?:\.\d+)?)\s*[xX*]\s*(\d+(?:\.\d+)?)", description)
        if size_match:
            length, width, height = map(float, size_match.groups())
        else:
            # 没有明确尺寸时给默认值，避免流程中断。
            length, width, height = 10.0, 10.0, 10.0

        weight_match = re.search(r"(\d+(?:\.\d+)?)\s*(kg|公斤)", description)
        weight = float(weight_match.group(1)) if weight_match else 1.0

        material = "高缓冲气泡垫" if fragile else "标准瓦楞纸"
        logger.info("AI解析链路完成：易碎=%s, 推荐材质=%s", fragile, material)
        return {
            "suggested_fragile": fragile,
            "suggested_length": length,
            "suggested_width": width,
            "suggested_height": height,
            "suggested_weight": weight,
            "material_recommendation": material,
        }
