from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
from pathlib import Path
from typing import List, Optional

from rag.file_reader import extract_text_from_file, get_supported_extensions
from rag.vector_store import VectorStore, chunk_text
from rag.ollama_client import OllamaClient, get_chat_model, get_embedding_model
from rag.rag_methods import get_rag_method, RAG_METHODS, SimpleRAG

app = FastAPI(title="RAG Service")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建必要的目录
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

INDEX_DIR = Path("indexes")
INDEX_DIR.mkdir(exist_ok=True)

# 向量存储实例
vector_store = VectorStore(index_dir=str(INDEX_DIR))

# Ollama 客户端
ollama_client = OllamaClient()

# 挂载静态文件目录（支持热更新）
app.mount("/static", StaticFiles(directory="static", html=True), name="static")


@app.get("/")
async def root():
    """返回首页"""
    return FileResponse("static/index.html")


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """上传文件接口，支持文本、PDF、Word 和 Excel"""
    print(f"收到文件上传请求: {file.filename}, 类型: {file.content_type}")
    
    # 检查文件类型
    allowed_extensions = {'.txt', '.md', '.csv', '.pdf', '.doc', '.docx', '.xls', '.xlsx'}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型。仅支持: {', '.join(allowed_extensions)}"
        )
    
    # 保存文件
    file_path = UPLOAD_DIR / file.filename
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 使用统一的文件读取方法提取内容
        content = extract_text_from_file(file_path)
        if content:
            print(f"成功提取文件内容: {file.filename}")
            # 统计文本块数量
            chunks = chunk_text(content)
            print(f"文本被分割为 {len(chunks)} 个块")
        else:
            print(f"无法提取文件内容或文件类型不支持: {file.filename}")
        
        print(f"文件上传成功: {file.filename}, 大小: {file_path.stat().st_size}")
        
        return JSONResponse({
            "message": "文件上传成功",
            "filename": file.filename,
            "file_type": file_ext,
            "content": content,
            "size": file_path.stat().st_size,
            "chunk_count": len(chunk_text(content)) if content else 0
        })
    except Exception as e:
        print(f"文件上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@app.post("/chat")
async def chat(message: dict):
    """聊天接口，支持 17 种 RAG 方法"""
    user_message = message.get("message", "")
    rag_method = message.get("rag_method", "option1")  # 默认 SimpleRAG
    
    if not user_message:
        raise HTTPException(status_code=400, detail="消息内容不能为空")
    
    # 获取 RAG 方法
    rag = get_rag_method(rag_method)
    method_info = {
        "id": rag_method,
        "name": RAG_METHODS.get(rag_method, SimpleRAG()).description if rag_method in RAG_METHODS else "未知方法"
    }
    
    # 调用 RAG 方法生成回答
    try:
        result = rag.chat(user_message, vector_store)
        
        # 处理新格式的返回（dict）
        if isinstance(result, dict):
            response_content = result.get("content", "")
            sources = result.get("sources", [])
            source_type = result.get("source_type", "local")
        else:
            # 兼容旧格式
            response_content = result
            sources = []
            source_type = "local"
        
        return JSONResponse({
            "message": response_content,
            "method": method_info,
            "sources": sources,
            "source_type": source_type,
            "timestamp": "2026-01-07"
        })
    except Exception as e:
        print(f"RAG 生成失败: {str(e)}")
        # 回退到简单聊天
        chat_model = get_chat_model()
        response = chat_model.chat(user_message)
        return JSONResponse({
            "message": response,
            "method": method_info,
            "sources": [],
            "source_type": "general",
            "error": str(e),
            "timestamp": "2026-01-07"
        })


@app.post("/index")
async def create_index(request: dict):
    """创建文档索引"""
    filenames = request.get("filenames", [])
    
    if not filenames:
        raise HTTPException(status_code=400, detail="未指定要索引的文件")
    
    indexed_count = 0
    failed_files = []
    
    for filename in filenames:
        file_path = UPLOAD_DIR / filename
        
        if not file_path.exists():
            failed_files.append({"filename": filename, "error": "文件不存在"})
            continue
        
        # 提取文件内容
        content = extract_text_from_file(file_path)
        if not content:
            failed_files.append({"filename": filename, "error": "无法提取文件内容"})
            continue
        
        # 分割文本
        chunks = chunk_text(content)
        if not chunks:
            failed_files.append({"filename": filename, "error": "文本分割失败"})
            continue
        
        # 创建元数据
        metadatas = [{
            "source": filename,
            "chunk_index": i
        } for i in range(len(chunks))]
        
        # 添加到向量存储
        vector_store.add_documents(
            texts=chunks,
            metadatas=metadatas,
            store_name="default"
        )
        
        # 创建索引标记文件
        index_file = INDEX_DIR / f"{filename}.index"
        try:
            with open(index_file, 'w') as f:
                f.write(f"chunks={len(chunks)}\\n")
            indexed_count += 1
            print(f"索引创建成功: {filename}, {len(chunks)} 个块")
        except Exception as e:
            failed_files.append({"filename": filename, "error": f"索引标记失败: {str(e)}"})
    
    return JSONResponse({
        "message": f"成功索引 {indexed_count} 个文件",
        "indexed_count": indexed_count,
        "failed_files": failed_files
    })


@app.post("/index/delete")
async def delete_index(request: dict):
    """删除索引文件"""
    filenames = request.get("filenames", [])
    
    if not filenames:
        raise HTTPException(status_code=400, detail="未指定要删除索引的文件")
    
    deleted = []
    not_found = []
    
    for filename in filenames:
        index_file = INDEX_DIR / f"{filename}.index"
        try:
            if index_file.exists():
                index_file.unlink()
                deleted.append(filename)
                print(f"索引删除成功: {filename}")
            else:
                not_found.append(filename)
        except Exception as e:
            print(f"索引删除失败: {filename}, 错误: {str(e)}")
    
    if deleted:
        message = f"成功删除 {len(deleted)} 个索引文件"
    else:
        message = "没有找到要删除的索引文件"
    
    return JSONResponse({
        "message": message,
        "deleted": deleted,
        "not_found": not_found
    })


@app.get("/index/status")
async def get_index_status():
    """获取所有已索引文件的状态"""
    indexed_files = []
    for index_file in INDEX_DIR.iterdir():
        if index_file.is_file() and index_file.name.endswith('.index'):
            filename = index_file.name[:-6]
            # 读取索引信息
            try:
                with open(index_file, 'r') as f:
                    info = f.read()
                indexed_files.append({
                    "filename": filename,
                    "info": info.strip()
                })
            except:
                indexed_files.append({"filename": filename, "info": "未知"})
    
    # 获取向量存储统计
    stats = vector_store.get_stats()
    
    return JSONResponse({
        "indexed_files": indexed_files,
        "vector_store_stats": stats
    })


@app.get("/uploads")
async def list_uploads():
    """获取已上传的文件列表"""
    # 获取已索引文件列表
    indexed_files = set()
    for index_file in INDEX_DIR.iterdir():
        if index_file.is_file() and index_file.name.endswith('.index'):
            filename = index_file.name[:-6]
            indexed_files.add(filename)
    
    files = []
    for file_path in UPLOAD_DIR.iterdir():
        if file_path.is_file():
            files.append({
                "filename": file_path.name,
                "size": file_path.stat().st_size,
                "type": file_path.suffix,
                "indexed": file_path.name in indexed_files
            })
    return JSONResponse({"files": files})


@app.delete("/uploads/{filename}")
async def delete_file(filename: str):
    """删除指定文件"""
    file_path = UPLOAD_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"文件不存在: {filename}")
    
    if not file_path.is_file():
        raise HTTPException(status_code=400, detail=f"不是文件: {filename}")
    
    try:
        file_path.unlink()
        # 同时删除索引文件
        index_file = INDEX_DIR / f"{filename}.index"
        if index_file.exists():
            index_file.unlink()
        print(f"文件删除成功: {filename}")
        return JSONResponse({
            "message": "文件删除成功",
            "filename": filename
        })
    except Exception as e:
        print(f"文件删除失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文件删除失败: {str(e)}")


@app.post("/uploads/delete")
async def delete_files(request: dict):
    """批量删除文件（先删除索引，再删除文件）"""
    filenames = request.get("filenames", [])
    
    if not filenames:
        raise HTTPException(status_code=400, detail="未指定要删除的文件")
    
    deleted_files = []
    failed_files = []
    
    for filename in filenames:
        file_path = UPLOAD_DIR / filename
        index_file = INDEX_DIR / f"{filename}.index"
        
        try:
            # 先删除索引文件
            if index_file.exists():
                index_file.unlink()
                print(f"索引删除成功: {filename}")
            
            # 再删除实际文件
            if file_path.exists() and file_path.is_file():
                file_path.unlink()
                deleted_files.append(filename)
                print(f"文件删除成功: {filename}")
            else:
                failed_files.append({"filename": filename, "error": "文件不存在"})
        except Exception as e:
            failed_files.append({"filename": filename, "error": str(e)})
            print(f"文件删除失败: {filename}, 错误: {str(e)}")
    
    return JSONResponse({
        "message": f"成功删除 {len(deleted_files)} 个文件",
        "deleted_files": deleted_files,
        "failed_files": failed_files
    })


@app.get("/ollama/status")
async def get_ollama_status():
    """获取 Ollama 服务状态"""
    if ollama_client.is_available():
        models = ollama_client.list_models()
        return JSONResponse({
            "status": "connected",
            "models": models
        })
    else:
        return JSONResponse({
            "status": "disconnected",
            "models": [],
            "error": "Ollama 服务未运行"
        })


@app.get("/ollama/models")
async def get_available_models():
    """获取可用的模型列表"""
    from rag.ollama_client import AVAILABLE_MODELS
    return JSONResponse({
        "models": AVAILABLE_MODELS
    })


@app.get("/rag/methods")
async def get_rag_methods():
    """获取所有 RAG 方法"""
    methods = []
    for key, method in RAG_METHODS.items():
        methods.append({
            "id": key,
            "name": method.description,
            "class_name": method.__class__.__name__
        })
    return JSONResponse({
        "methods": methods,
        "count": len(methods)
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="127.0.0.1", 
        port=8000,
        reload=True,
        reload_dirs=["static"]
    )
