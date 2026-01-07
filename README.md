# RAG Service

基于 FastAPI 的检索增强生成（Retrieval-Augmented Generation）服务。

## 快速启动

```bash
./start.sh
```

访问地址: http://127.0.0.1:8000

## 技术栈

| 类别 | 技术 |
|------|------|
| 后端框架 | FastAPI 0.104+ |
| ASGI 服务器 | Uvicorn 0.24+ |
| 前端框架 | Vue.js 2.7 |
| UI 组件库 | Element UI |

## 项目结构

```
rag_service/
├── main.py              # FastAPI 后端主程序
├── requirements.txt     # Python 依赖列表
├── start.sh            # 启动脚本
├── static/             # 前端静态资源
│   ├── index.html      # 主页面
│   ├── app.js          # 前端 Vue 应用
│   └── style.css       # 样式
├── rag/                # RAG 相关模块
├── uploads/            # 上传文件存储
└── indexes/            # 索引文件存储
```

## API 端点

### 文件上传
- `POST /upload` - 上传文件（支持 txt、md、csv、pdf、doc、docx、xls、xlsx）

### 文件管理
- `GET /uploads` - 获取文件列表
- `POST /uploads/delete` - 批量删除文件

### 索引管理
- `POST /index/mark` - 标记文件已索引
- `POST /index/delete` - 删除索引
- `GET /index/status` - 获取索引状态

### 聊天
- `POST /chat` - 发送消息对话

## 前端功能

### 页面结构
- **左侧导航栏** - 可折叠菜单（RAG、首页、文件管理、智能对话、历史记录、设置）
- **RAG 主页面** - 包含文件管理、对话面板、RAG 方法配置侧边栏

### RAG 方法（17种）
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

## 开发说明

- 前端支持热更新，修改后刷新浏览器即可
- `uploads/` 和 `indexes/` 目录已添加到 `.gitignore`
