"""前端页面路由测试。"""

from fastapi.testclient import TestClient

from app.main import app


# 使用 TestClient 验证 /app 和静态资源路由可访问。
client = TestClient(app)


def test_console_page_available() -> None:
    """验证企业控制台页面可正常返回。"""

    response = client.get("/app")
    assert response.status_code == 200
    assert "SmartPack 企业级智能包装控制台" in response.text


def test_static_asset_available() -> None:
    """验证静态资源路由可访问。"""

    response = client.get("/static/app.js")
    assert response.status_code == 200
