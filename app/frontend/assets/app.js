import { ApiClient } from "./api.js";
import { createLogger } from "./logger.js";
import { appState, setAuthContext } from "./state.js";

// 初始化基础对象：API 客户端 + 日志。
const api = new ApiClient();
const logger = createLogger(document.getElementById("logBox"));

// 页面元素引用，集中管理避免散落在事件回调中。
const apiKeyEl = document.getElementById("apiKey");
const roleEl = document.getElementById("userRole");
const saveAuthBtn = document.getElementById("saveAuth");

const aiDescriptionEl = document.getElementById("aiDescription");
const extractBtn = document.getElementById("extractBtn");
const aiResultEl = document.getElementById("aiResult");

const customerIdEl = document.getElementById("customerId");
const productIdEl = document.getElementById("productId");
const quantityEl = document.getElementById("quantity");
const createOrderBtn = document.getElementById("createOrderBtn");

const orderIdEl = document.getElementById("orderId");
const calcPlanBtn = document.getElementById("calcPlanBtn");
const planResultEl = document.getElementById("planResult");

/**
 * 将对象结果以可读 JSON 输出到界面。
 * @param {HTMLElement} target 输出容器
 * @param {any} data 输出数据
 */
function renderJson(target, data) {
  target.textContent = JSON.stringify(data, null, 2);
}

/**
 * 持久化鉴权上下文到浏览器本地。
 * 这样刷新页面后仍保留之前设置，提升操作效率。
 */
function persistAuth() {
  localStorage.setItem(
    "smartpack_auth",
    JSON.stringify({ apiKey: appState.apiKey, role: appState.role }),
  );
}

/**
 * 从本地恢复鉴权上下文。
 */
function restoreAuth() {
  const raw = localStorage.getItem("smartpack_auth");
  if (!raw) return;

  try {
    const parsed = JSON.parse(raw);
    setAuthContext(parsed.apiKey || "", parsed.role || "packer");
    apiKeyEl.value = appState.apiKey;
    roleEl.value = appState.role;
    logger.info("前端链路：已恢复本地鉴权上下文");
  } catch (_err) {
    logger.warn("前端链路：本地鉴权信息损坏，已忽略");
  }
}

// 保存鉴权配置。
saveAuthBtn.addEventListener("click", () => {
  setAuthContext(apiKeyEl.value, roleEl.value);
  persistAuth();
  logger.info(`前端链路：鉴权上下文已保存 role=${appState.role}`);
});

// AI 解析链路。
extractBtn.addEventListener("click", async () => {
  try {
    logger.info("前端链路：开始调用 AI 解析接口");
    const result = await api.extractProduct(aiDescriptionEl.value);
    renderJson(aiResultEl, result);
    logger.info("前端链路：AI 解析完成");
  } catch (err) {
    logger.error(`前端链路：AI 解析失败 -> ${err.message}`);
  }
});

// 创建订单链路。
createOrderBtn.addEventListener("click", async () => {
  try {
    logger.info("前端链路：开始创建订单");
    const order = await api.createOrder(
      Number(customerIdEl.value),
      Number(productIdEl.value),
      Number(quantityEl.value),
    );
    renderJson(planResultEl, order);
    orderIdEl.value = order.id;
    logger.info(`前端链路：订单创建成功 order_id=${order.id}`);
  } catch (err) {
    logger.error(`前端链路：订单创建失败 -> ${err.message}`);
  }
});

// 装箱计算链路。
calcPlanBtn.addEventListener("click", async () => {
  try {
    logger.info("前端链路：开始计算装箱方案");
    const plans = await api.calculatePlans(Number(orderIdEl.value));
    renderJson(planResultEl, plans);
    logger.info(`前端链路：装箱方案计算完成 order_id=${orderIdEl.value}`);
  } catch (err) {
    logger.error(`前端链路：装箱方案计算失败 -> ${err.message}`);
  }
});

// 页面加载完成后恢复上下文。
restoreAuth();
logger.info("前端链路：控制台初始化完成");
