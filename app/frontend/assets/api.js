import { appState } from "./state.js";

/**
 * API 客户端。
 * 统一封装请求头与错误处理，后续替换为更完整 SDK 时只需改这一层。
 */
export class ApiClient {
  constructor(baseUrl = "/api/v1") {
    this.baseUrl = baseUrl;
  }

  /**
   * 执行 HTTP 请求。
   * @param {string} path 接口路径
   * @param {RequestInit} init 请求参数
   * @returns {Promise<any>}
   */
  async request(path, init = {}) {
    const headers = {
      "Content-Type": "application/json",
      "X-API-Key": appState.apiKey,
      "X-User-Role": appState.role,
      ...init.headers,
    };

    const resp = await fetch(`${this.baseUrl}${path}`, {
      ...init,
      headers,
    });

    const body = await resp.json().catch(() => ({}));
    if (!resp.ok) {
      throw new Error(body.detail || `请求失败: ${resp.status}`);
    }
    return body;
  }

  /**
   * 调用 AI 描述解析接口。
   * @param {string} description 商品描述
   */
  extractProduct(description) {
    return this.request("/ai/extract", {
      method: "POST",
      body: JSON.stringify({ description }),
    });
  }

  /**
   * 创建订单。
   * @param {number} customerId 客户ID
   * @param {number} productId 产品ID
   * @param {number} quantity 数量
   */
  createOrder(customerId, productId, quantity) {
    return this.request("/orders", {
      method: "POST",
      body: JSON.stringify({
        customer_id: customerId,
        items: [{ product_id: productId, quantity }],
      }),
    });
  }

  /**
   * 计算订单装箱方案。
   * @param {number} orderId 订单ID
   */
  calculatePlans(orderId) {
    return this.request(`/orders/${orderId}/plans`, { method: "POST" });
  }
}
