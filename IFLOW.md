# RAG Service 项目上下文

## 项目概述

RAG Service 是一个基于 FastAPI 的检索增强生成（Retrieval-Augmented Generation）服务，提供文件上传、管理、索引和聊天对话功能。

## 技术栈

| 类别 | 技术 |
|------|------|
| 后端框架 | FastAPI 0.104+ |
| ASGI 服务器 | Uvicorn 0.24+ |
| 前端框架 | Vue.js 2.7 |
| UI 组件库 | Element UI |
| 依赖管理 | Python 虚拟环境 (.venv) |

## 项目结构

```
rag_service/
├── main.py              # FastAPI 后端主程序
├── requirements.txt     # Python 依赖列表
├── start.sh            # 启动脚本（自动清理端口并启动服务）
├── IFLOW.md            # 本文档
├── static/             # 前端静态资源
│   ├── index.html      # 主页面（Vue2 + Element UI）
│   ├── app.js          # 前端 Vue 应用逻辑
│   └── style.css       # 样式文件
├── rag/                # RAG 相关模块
│   ├── collection/     # 集合模块
│   └── func1-Simple_RAG/  # 简单 RAG 实现
├── uploads/            # 上传文件存储目录
├── indexes/            # 索引文件存储目录
└── __pycache__/        # Python 缓存
```

## 运行命令

### 启动服务
```bash
# 方式1：使用启动脚本（推荐）
./start.sh

# 方式2：手动启动
.venv/bin/python main.py
```

### 服务地址
- 本地访问: http://127.0.0.1:8000
- 端口: 8000

## API 端点

### 文件上传
- `POST /upload` - 上传文件，支持 txt、md、csv、pdf、doc、docx、xls、xlsx

### 文件管理
- `GET /uploads` - 获取已上传文件列表
- `DELETE /uploads/{filename}` - 删除单个文件
- `POST /uploads/delete` - 批量删除文件

### 索引管理
- `POST /index/mark` - 标记文件已索引
- `POST /index/delete` - 删除索引文件
- `GET /index/status` - 获取索引状态

### 聊天
- `POST /chat` - 发送消息进行对话

## 前端功能

### 页面结构
1. **左侧导航栏** - 可折叠，包含多个菜单：
   - RAG - 主功能页面（文件上传 + 聊天）
   - 首页、文件管理、智能对话、历史记录、设置（开发中）

2. **RAG 主页面**：
   - **文件管理面板** - 上传、索引、删除文件
   - **对话面板** - 聊天输入和消息展示
   - **RAG 方法侧边栏** - 右侧固定侧边栏，包含 17 种 RAG 方法配置

### RAG 方法列表
1. SimpleRAG（简单切块）
2. Semantic Chunking（语义切块）
3. Context Enriched Retrieval（上下文增强检索）
4. Contextual Chunk Headers（上下文分块标题）
5. Document Augmentation（文档增强）
6. Query Transformation（查询转换）
7. Reranker（重排序）
8. RSE（语义扩展重排序）
9. Feedback Loop（反馈闭环）
10. Adaptive RAG（自适应检索增强生成）
11. Self RAG（自反思检索增强生成）
12. Knowledge Graph（知识图谱）
13. Hierarchical Indices（层次化索引）
14. HyDE（假设文档嵌入）
15. Fusion（融合检索）
16. CRAG（纠错型 RAG）
17. Multi-Modal RAG（多模态检索增强生成）

## 开发规范

### 前端修改
- Vue.js 2 语法
- Element UI 组件
- 静态文件位于 `/static/` 目录
- 支持热更新，修改后刷新浏览器即可

### 后端修改
- FastAPI 路由定义在 `main.py`
- 使用 `Path` 模块管理文件路径
- 支持 CORS 跨域

## 注意事项

- `uploads/` 和 `indexes/` 目录已添加到 `.gitignore`
- 启动前会自动检查并清理占用端口的进程
- 前端代码修改后需要刷新浏览器查看效果
