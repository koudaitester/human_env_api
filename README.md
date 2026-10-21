```markdown
# 人居微环境视觉检测系统
> 本地一体化AI原型平台｜FastAPI + Ollama(LLaVA/Llama) + 轻量RAG + 静态前端
> 支持人居环境规则校验、本地大模型对话、AI视频生成（Mock，后续接入Wan2.1）、图像视觉检测。用于室内/封闭空间环境识别、风险判断与方案评估。

## ✨ 项目简介
本系统为**本地离线优先**的人居微环境验证原型，整套服务不强制依赖外网。
核心用途：对密闭人居空间（室内、舱体等）做环境参数检测、风险识别，自动输出评估结论与整改建议。

**当前内置能力清单**
1. 人居环境规则校验：空气净化器睡眠朝向校验业务规则
2. 本地视觉AI：Ollama LLaVA多模态模型，图片上传+环境视觉识别
3. 本地LLM对话：Ollama Llama系列大模型，文本问答
4. AI视频生成模块：Mock任务接口，前端页面调用，后续可无缝接入Wan2.1视频模型
5. 轻量RAG知识库：本地Markdown场景规则库，语义检索，降低大模型幻觉
6. 静态前端页面：浏览器页面，支持图片上传、视频任务提交，可视化结果展示
7. RESTful接口：FastAPI自动生成交互式API文档，方便调试

**技术栈**
- 后端：Python + FastAPI，分层架构 `routers`(路由) / `services`(业务) / `utils`(工具) / `config`(配置)
- AI底座：Ollama，本地运行 Llama3 / LLaVA 多模态模型
- 向量检索：chromadb，轻量本地RAG
- 前端：原生HTML，静态资源托管
- 项目管理：Git，支持离线commit，联网后统一push

## 📦 核心组件
1. **Ollama**：本地模型服务
    - `llama3.1:7b` / `llama3.1:2.5b`：文本对话模型
    - `llama3.2-vision`(LLaVA)：图像视觉分析，环境图片识别
2. **FastAPI**：HTTP接口服务，统一入口，自动生成 `/docs` 接口文档
3. **Services业务层**：业务逻辑隔离，环境规则、Llama大模型、视频生成业务分开维护
4. **config配置目录**：统一存放模型参数、服务地址等配置项，代码与配置解耦
5. **轻量RAG知识库**：读取`knowledge/scene_rule.md`场景规则，检索后注入Prompt，约束模型输出
6. **静态前端(html_basic)**：浏览器交互页面，图片上传、视频生成任务提交

## 🚀 完整运行流程
### 场景1：人居环境视觉检测
1. 前端页面上传环境照片
2. FastAPI接收图片，调用RAG检索匹配相关人居环境规则
3. 图片+检索到的场景规则一起送入LLaVA视觉模型
4. 模型输出环境评估、潜在风险、整改建议，返回前端展示

### 场景2：AI视频生成（当前Mock）
1. 前端输入视频提示词，提交任务
2. 后端创建异步任务，返回task_id
3. 前端轮询任务状态，任务完成后展示视频（后续接入Wan2.1真实推理）

### 场景3：人居设备规则校验
1. 前端/API提交设备参数（例：净化器角度、是否睡眠模式）
2. Service层执行硬规则校验，返回合规判断

### 场景4：本地大模型对话
1. 请求 `/llama/chat` 接口，传入prompt
2. 调用Ollama本地Llama模型，返回文本回答

## 📁 完整目录结构
```text
.
├── config
│   ├── db_config.yaml
│   ├── launch.json
│   ├── llama_config.py
│   └── prompt_config.py
├── html_basic
│   ├── index.html
│   ├── js
│   └── static
│       ├── common.js
│       ├── env_history.html
│       ├── index.html
│       ├── login.html
│       ├── mold_analyze_duo.html
│       ├── mold_analyze.html
│       ├── mold_detect.html
│       ├── placeholder_help.html
│       ├── placeholder_history.html
│       ├── register.html
│       ├── test_upload.html
│       └── vision_analysis.html
├── knowledge
│   ├── base_prompt.md
│   ├── extraterrestrial_habitat_knowledge_base.md
│   ├── mode_rules_origin.md
│   ├── mode_rules.md
│   ├── mold_risk_calc.md
│   ├── scene_rule.md
│   └── weather_rules.md
├── log
│   ├── 20261013.log
│   ├── 20261014.log
│   ├── 20261015.log
│   ├── 20261016.log
│   ├── 20261017.log
│   ├── 20261018.log
│   ├── 20261019.log
│   ├── 20261020.log
│   └── 20261021.log
├── main.py
├── README.md
├── requirements.txt
├── routers
│   ├── __init__.py
│   ├── audio_router.py
│   ├── business_router.py
│   ├── env_router.py
│   ├── env.py
│   ├── health.py
│   ├── llama.py
│   ├── llm_router.py
│   ├── mold_router.py
│   ├── rag_router.py
│   ├── report_router.py
│   ├── user_router.py
│   ├── video.py
│   └── vision_router.py
├── schemas
│   ├── env.py
│   └── user.py
├── services
│   ├── __init__.py
│   ├── audio_service.py
│   ├── base_service.py
│   ├── dao
│   │   ├── __init__.py
│   │   ├── app_user_dao.py
│   │   ├── db_pool.py
│   │   ├── env_dao.py
│   │   └── report_dao.py
│   ├── env_service.py
│   ├── llama_service.py
│   ├── llm_service.py
│   ├── log_service.py
│   ├── mold_weight_service.py
│   ├── prompt_service.py
│   ├── rag_service.py
│   ├── report_service.py
│   ├── user_service.py
│   ├── video_service.py
│   └── vision_service.py
├── tests
│   └── mold_full_test_notes.md
├── tmp
│   ├── 豆包 (1).png
│   └── 豆包.png
├── TODO.md
└── utils
    ├── __init__.py
    ├── common.py
    ├── deps.py
    ├── rag_helper.py
    ├── security.py
    ├── tools.py
    └── validator.py
```

## ⚙️ 环境准备
### 1. 前置软件
- Python >=3.10
- Ollama 本地服务，提前拉取模型
```bash
ollama pull llama3.1:7b
ollama pull llama3.2-vision
```

### 2. Python依赖安装
```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装全部依赖
pip install -r requirements.txt
```

requirements.txt关键包：
```text
fastapi
uvicorn[standard]
pydantic
ollama
pillow
httpx
chromadb
```

## 📝 启动与访问
```bash
# 启动服务
python3 main.py
```
服务地址：`[http://127.0.0.1:8000](http://127.0.0.1:8000)`
- API交互式文档：`[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)`
- 前端页面：`[http://127.0.0.1:8000/static/index.html](http://127.0.0.1:8000/static/index.html)`

## 📌 接口清单
| 接口 | 方法 | 说明 |
|---|---|---|
| `/health` | GET | 服务健康检查 |
| `/env/purifier/check` | POST | 净化器睡眠朝向规则校验 |
| `/video/create` | POST | 创建视频生成任务（Mock） |
| `/video/task/{task_id}` | GET | 查询视频任务状态 |
| `/llama/chat` | POST | 本地Llama文本对话 |

## ⚠️ 项目当前开发状态
> 开发中｜本地原型验证项目，离线优先
✅ 已完成
- FastAPI分层脚手架，自动项目脚本生成
- 人居环境设备规则校验接口
- Ollama Llama文本对话封装，配置抽离到config
- AI视频任务前后端Mock链路，静态前端页面
- Git离线提交能力（本地commit，联网后push）
- VSCode开发踩坑记录（Python语言服务器索引重启方案）

🔨 待实现
- LLaVA图像上传接口接入，打通视觉检测全链路
- RAG知识库检索接入，scene_rule.md语义检索
- 视频模块替换Mock，接入Wan2.1真实视频推理
- 日志持久化、异常捕获优化

## 💡 开发踩坑记录
1. VSCode Python符号跳转失效：批量脚本生成代码后，执行 `Command+Shift+P` → `Python: Restart Language Server` 重新索引
2. Git离线工作流：`git add` / `git commit` 完全本地执行，不需要外网；`git push` 才需要网络同步远端
3. FastAPI静态文件挂载：`app.mount("/static", StaticFiles(directory="html_basic"))`，URL前缀`/static`对应本地文件夹html_basic
4. Ollama本地模型：确保ollama服务常驻运行，模型提前pull到本地

## 📄 补充说明
项目用于**封闭人居微环境评估原型验证**。
持续向 `knowledge/scene_rule.md` 新增环境场景规则，RAG模块会自动加载知识库。
整套架构低耦合，后续模块可以单独替换：Mock视频服务替换为真实Wan推理、RAG可切换Dify工作流。
```
