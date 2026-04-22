/**
 * 前端日志工具。
 * 与后端一致使用简洁中文日志风格，覆盖用户关键操作链路。
 */
export function createLogger(logElement) {
  /**
   * 输出一条日志。
   * @param {"INFO"|"WARN"|"ERROR"} level 日志级别
   * @param {string} message 中文日志内容
   */
  function log(level, message) {
    const now = new Date().toISOString();
    const line = `${now} | ${level} | frontend | ${message}`;
    const item = document.createElement("div");
    item.textContent = line;
    logElement.prepend(item);
  }

  return {
    info: (msg) => log("INFO", msg),
    warn: (msg) => log("WARN", msg),
    error: (msg) => log("ERROR", msg),
  };
}
