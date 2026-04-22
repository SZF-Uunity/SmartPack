/**
 * 前端全局状态容器。
 * 这里集中管理鉴权头，避免在每个请求函数里重复拼装，保持低耦合。
 */
export const appState = {
  apiKey: "",
  role: "packer",
};

/**
 * 更新鉴权上下文。
 * @param {string} apiKey API Key 明文
 * @param {string} role 当前角色
 */
export function setAuthContext(apiKey, role) {
  appState.apiKey = apiKey.trim();
  appState.role = role;
}
