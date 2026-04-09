# 快速上手

## 第一步：安装项目

```bash
git clone <your-repo-url>
cd regentos
chmod +x install.sh
./install.sh
```

安装脚本会自动完成：

- 创建 `.venv`
- 安装 Python 依赖
- 安装 Dashboard 前端依赖
- 初始化 `runtime/` 与 `data/`
- 生成 `agents.json`
- 生成 `data/demo_cases.json`
- 构建 React Dashboard

## 第二步：启动 API

```bash
bash scripts/run_api.sh
```

默认地址：

- `http://127.0.0.1:8000/healthz`
- `http://127.0.0.1:8000/api/cases`
- `http://127.0.0.1:8000/api/agents`

## 第三步：启动文渊阁中枢原型

```bash
bash scripts/run_dashboard.sh
```

默认地址：

- `http://127.0.0.1:7891`

当前 Dashboard 是 React 前端原型，用现有 API 实时取数。
如果仓库根目录存在 `data/demo_cases.json`，API 启动时会自动加载示例案件。

## 第四步：查看 18 个治理 Agent

```bash
curl http://127.0.0.1:8000/api/agents
curl http://127.0.0.1:8000/api/agents/styles
curl http://127.0.0.1:8000/api/models/runtime-capabilities
```

## 第五步：继续开发

```bash
pytest tests
python scripts/export_agent_manifest.py
python scripts/seed_demo_data.py
python scripts/run_e2e_demo.py
```

其中 `python scripts/run_e2e_demo.py` 会直接在进程内通过 API 跑完一条完整治理链：

- 创建案件
- 受理与票拟
- 提交审批
- 批准执行
- 标记修复待令
- 下达修复令
- 重跑回到执行
- 进入回奏
- 完成归档

React 前端开发模式：

```bash
cd apps/dashboard
npm install
VITE_API_BASE=http://127.0.0.1:8000 npm run dev -- --host 0.0.0.0 --port 7891
```

## 模型接入

RegentOS 当前文档和元数据层已经按三类模型来源设计：

- 远程 API 模型
- 本地蒸馏模型
- 本地完整大模型

系统设计本身不限制本地模型大小。
真正的运行上限由本机硬件、推理框架、量化方式和上下文配置决定。
