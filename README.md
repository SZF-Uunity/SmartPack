# SmartPack 智能包装系统（企业级版）

一个面向电商/物流的智能装箱后端项目，核心目标是平衡**包装成本**与**商品保护质量**，并支持企业级治理能力（RBAC、API Key、IP 白名单、限流、审计日志）。

## 1. 核心能力

- 智能推荐：根据订单商品计算三类方案（成本优先/质量优先/均衡）。
- AI 辅助：输入自然语言描述，自动提取易碎、尺寸、重量并推荐材质。
- 方案模板：将满意方案保存为模板，后续快速复用。
- 企业安全：API Key 鉴权、角色权限控制、IP 白名单、分钟级限流。
- 可审计：关键写操作落审计日志，满足合规要求。

## 2. 技术栈（前沿可演进）

- Python 3.11+
- FastAPI（异步高性能 Web）
- SQLAlchemy 2.x（现代 ORM）
- Pydantic v2（高性能校验）
- SQLite（开发）/ PostgreSQL（生产可切换）
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
- 企业控制台：http://127.0.0.1:8000/app

## 4. 企业级架构说明

项目采用分层结构，强调低耦合与可演进：

- `app/api`: HTTP 协议层（路由、权限依赖）。
- `app/services`: 业务编排（订单、装箱、AI、安全、审计）。
- `app/repositories`: 数据访问隔离层。
- `app/models`: 核心实体模型。
- `app/schemas`: DTO。
- `app/core`: 配置、日志、中间件支撑。
- `app/utils`: 加密哈希等基础能力。

### 4.1 关键前沿能力

1. **统一请求上下文**：中间件注入 `X-Request-Id` + 访问耗时日志。
2. **策略引擎化装箱**：三策略评分函数隔离，便于后续接入 OR-Tools/遗传算法。
3. **安全可插拔**：当前内存限流实现可平滑替换 Redis/Gateway。
4. **审计链路**：操作级审计日志模型，可对接 ELK/SIEM。


## 4.2 企业前端控制台（新增）

- 访问地址：`/app`
- 前端采用原生 ES Modules 分层：`app.js`（编排）+ `api.js`（API 客户端）+ `state.js`（状态）+ `logger.js`（日志）。
- 内置功能：
  - API Key / 角色上下文保存（本地持久化）
  - AI 商品描述解析
  - 订单创建
  - 装箱方案计算
  - 前端链路中文日志展示

> 说明：当前前端是可演进的“企业控制台基础版”，后续可无缝替换为 React/Vue 构建产物并继续复用后端 API。

## 5. 关键业务规则落地点

- 箱子外尺寸 > 内尺寸：`CatalogRepository.create_box`。
- 停用箱子不参与计算：`PackingService._choose_box`。
- 软删除：所有模型统一 `is_deleted` 字段。
- 关键字段唯一：`sku/code/name` 等在模型层设定唯一约束。
- 订单确认后不可变更：`OrderService.bind_plan` 与 `PackingService.generate_plans`。
- 状态机严格流转：`OrderService.allowed_transitions`。
- API 安全约束：`SecurityService.validate_api_key`（IP + 限流）。

## 6. 链路日志与可观测性

- 中文日志覆盖：鉴权、接口入口、订单创建、装箱计算、模板保存、审计记录。
- 日志格式：时间 | 级别 | 模块 | 信息（简洁但可定位问题）。
- 每次请求自动记录 request_id 和耗时。

## 7. 权限模型（RBAC）

- `sysadmin`: 全权限。
- `admin`: 基础数据管理、订单审核、模板管理。
- `packer`: 订单创建、装箱计算、模板维护。
- `customer_user`: 仅限本人数据只读（后续可通过客户映射进一步收敛）。

## 8. 常用命令

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

## 9. 下一步演进建议（生产级）

1. 接入 Alembic 完整迁移流程。
2. API 网关层追加 WAF + OAuth2/JWT。
3. 限流状态迁移到 Redis，支持多实例横向扩展。
4. 装箱算法替换为 3D Bin Packing 真实求解器。
5. 增加异步任务总线（如 Kafka/Celery）解耦重计算任务。
