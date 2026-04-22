# SmartPack 智能包装系统（Python + uv）

一个面向电商/物流的智能装箱后端项目，目标是平衡**包装成本**与**商品保护质量**。

## 1. 核心能力

- 智能推荐：根据订单商品计算三类方案（成本优先/质量优先/均衡）。
- AI 辅助：输入自然语言描述，自动提取易碎、尺寸、重量并推荐材质。
- 方案模板：将满意方案保存为模板，后续快速复用。
- 规则内建：软删除、唯一约束、状态机、禁用箱型过滤等关键 BR 已落地。

## 2. 技术栈

- Python 3.11+
- FastAPI
- SQLAlchemy 2.x
- SQLite（可切换 PostgreSQL）
- pytest
- uv（依赖与虚拟环境管理）

## 3. 本地部署（不使用 Docker）

```bash
# 1) 创建并激活 uv 虚拟环境
uv venv
source .venv/bin/activate

# 2) 安装依赖
uv sync

# 3) 启动服务
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

启动后访问：

- OpenAPI 文档：http://127.0.0.1:8000/docs
- 健康检查：http://127.0.0.1:8000/health

## 4. 可扩展架构说明

项目采用分层结构，降低耦合：

- `app/api`: 仅处理 HTTP 协议与参数校验。
- `app/services`: 业务编排（装箱、状态机、AI 解析）。
- `app/repositories`: 数据访问隔离层。
- `app/models`: 核心实体模型。
- `app/schemas`: DTO。
- `app/core`: 配置与日志。

后续扩展建议：

1. 将 `AIService` 从规则引擎替换为模型推理服务（保持接口不变）。
2. 将 `PackingService._mock_placement` 替换为真实 3D 算法引擎。
3. 增加 `Role + API Key + IP 白名单 + 速率限制` 中间件体系。
4. 通过 Alembic 迁移支持平滑演进数据库结构。

## 5. 关键业务规则落地点

- 箱子外尺寸 > 内尺寸：`CatalogRepository.create_box`。
- 停用箱子不参与计算：`PackingService._choose_box`。
- 软删除：所有模型统一 `is_deleted` 字段。
- 关键字段唯一：`sku/code/name` 等在模型层设定唯一约束。
- 订单确认后不可变更：`OrderService.bind_plan` 与 `PackingService.generate_plans`。
- 状态机严格流转：`OrderService.allowed_transitions`。

## 6. 日志策略

- 全链路中文日志，覆盖：接口入口、订单创建、装箱计算、AI 解析、模板保存。
- 日志格式：时间 | 级别 | 模块 | 信息（简洁但可定位问题）。

## 7. 常用命令

```bash
# 新增依赖
uv add <package>

# 同步依赖
uv sync

# 运行测试
uv run pytest

# 代码检查
uv run ruff check .
```
